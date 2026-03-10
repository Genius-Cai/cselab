"""Interactive REPL — transparent proxy to CSE server, powered by prompt_toolkit."""

import os
import subprocess
import sys
import time

# Suppress prompt_toolkit CPR warning before import
os.environ.setdefault("PROMPT_TOOLKIT_NO_CPR", "1")

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

from cselab.config import Config
from cselab.connection import connect, is_connected, rsync_up, rsync_down, ssh_exec
from cselab.theme import (
    GREEN, RED, DIM, BOLD, TEAL, RESET,
    TOOLBAR_BG, TOOLBAR_FG, TOOLBAR_ACCENT, TOOLBAR_DANGER, TOOLBAR_DIM,
    PROMPT_STYLE, DOT_ON, DOT_OFF, H,
)

# Paths
HISTORY_FILE = os.path.expanduser("~/.config/cselab/history")

# prompt_toolkit style
STYLE = Style.from_dict({
    "prompt": PROMPT_STYLE,
    "bottom-toolbar": f"bg:{TOOLBAR_BG} {TOOLBAR_FG}",
    "bang": "ansired bold",
})

# Known commands — CSE tools + built-ins + common utils
COMPLETIONS = sorted({
    # Built-in cselab
    "exit", "quit", "sync", "pull", "status", "help",
    # CSE tools
    "autotest", "give", "dcc", "classrun", "style",
    # Course codes (prefixes for autotest/give/classrun)
    "1511", "1521", "1531", "1911",
    "2041", "2511", "2521",
    "3231", "3311", "3331",
    "6080", "6443", "6771", "6991",
    "9021", "9024", "9032",
    # Build / compile
    "make", "gcc", "g++", "python3", "java", "javac", "mipsy",
    # File ops
    "ls", "cat", "rm", "mkdir", "cp", "mv", "cd", "chmod", "touch",
    "head", "tail", "diff", "wc", "grep", "find", "sort", "uniq",
    # Editors
    "vim", "nano",
    # Other
    "man", "echo", "test",
})

# Commands that take file/directory paths as arguments
_PATH_CMDS = frozenset([
    "cd", "ls", "cat", "rm", "mkdir", "cp", "mv", "touch",
    "chmod", "head", "tail", "diff", "vim", "nano", "find",
])


# ── Lexer: highlight ! prefix in red ──

class _BangLexer(Lexer):
    """Highlight the ! prefix (skip-sync) in red."""

    def lex_document(self, document):
        def get_line(lineno):
            line = document.lines[lineno]
            if line.startswith("!"):
                return [("class:bang", "!"), ("", line[1:])]
            return [("", line)]
        return get_line


# ── Completer: commands first word, remote paths after cd/ls/etc ──

class _SmartCompleter(Completer):
    """Context-aware completion: commands → remote paths."""

    def __init__(self, commands, cfg, remote_dir):
        self._commands = commands
        self._cfg = cfg
        self._remote_dir = remote_dir
        self._ls_cache = {}  # subdir -> (timestamp, entries)

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        stripped = text.lstrip("!").lstrip()
        words = stripped.split()

        # First word (or empty) → command completion
        if not words or (len(words) == 1 and not stripped.endswith(" ")):
            prefix = words[0].lower() if words else ""
            for cmd in self._commands:
                if cmd.startswith(prefix):
                    yield Completion(cmd, start_position=-len(prefix))
            return

        # After a path-taking command → remote path completion
        if words[0] in _PATH_CMDS:
            partial = words[-1] if not stripped.endswith(" ") else ""
            yield from self._path_completions(partial)
            return

        # Other commands → word completion for remaining args
        prefix = (words[-1] if not stripped.endswith(" ") else "").lower()
        for cmd in self._commands:
            if cmd.startswith(prefix):
                yield Completion(cmd, start_position=-len(prefix))

    def _path_completions(self, partial):
        """Yield remote file/directory completions."""
        if "/" in partial:
            parent, prefix = partial.rsplit("/", 1)
        else:
            parent, prefix = "", partial

        entries = self._cached_ls(parent)
        full_prefix = f"{parent}/" if parent else ""

        for name in entries:
            if name.lower().startswith(prefix.lower()):
                yield Completion(full_prefix + name, start_position=-len(partial))

    def _cached_ls(self, subdir):
        """List remote dir with 5s cache."""
        now = time.time()
        cached = self._ls_cache.get(subdir)
        if cached and now - cached[0] < 5:
            return cached[1]

        entries = self._ls_remote(subdir)
        self._ls_cache[subdir] = (now, entries)
        return entries

    def _ls_remote(self, subdir):
        """List remote directory via SSH ControlMaster."""
        from cselab.connection import ssh_output

        target = self._remote_dir
        if subdir:
            target = target + "/" + subdir

        out = ssh_output(self._cfg, f"ls -1p {target} 2>/dev/null")
        if not out or not out.strip():
            return []
        return [e for e in out.strip().split("\n") if e]


# ── UI helpers ──

def _rule():
    """Print a dim horizontal rule spanning the terminal width."""
    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 80
    print(f"{DIM}{H * cols}{RESET}")


def _display_dir() -> str:
    cwd = os.getcwd()
    home = os.path.expanduser("~")
    return "~" + cwd[len(home):] if cwd.startswith(home) else cwd


class _State:
    """Mutable state shared between REPL loop and toolbar."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.connected = False
        self.last_sync = ""
        self.display_dir = _display_dir()
        self.cmd_count = 0


def _toolbar(state: _State):
    """Bottom toolbar — teal dot for connected, red for disconnected."""
    bg = f"bg:{TOOLBAR_BG}"

    parts = [
        (f"{bg} {TOOLBAR_FG}", f" {state.cfg.user}@{state.cfg.host}  "),
    ]

    if state.connected:
        parts.append((f"{bg} {TOOLBAR_ACCENT} bold", DOT_ON))
        parts.append((f"{bg} {TOOLBAR_ACCENT}", " connected"))
    else:
        parts.append((f"{bg} {TOOLBAR_DANGER}", DOT_OFF))
        parts.append((f"{bg} {TOOLBAR_DANGER}", " disconnected"))

    parts.append((f"{bg} {TOOLBAR_FG}", f"  {state.display_dir}"))

    if state.last_sync:
        parts.append((f"{bg} {TOOLBAR_DIM}", f"  sync {state.last_sync}"))

    return parts


def _cmd_help():
    print()
    print(f"  {BOLD}Commands{RESET}")
    print(f"  {DIM}Any CSE command runs on the server:{RESET}")
    print(f"    1521 autotest collatz")
    print(f"    give cs1521 lab03 collatz.c")
    print(f"    dcc collatz.c -o collatz && ./collatz 42")
    print()
    print(f"  {BOLD}Built-in{RESET}")
    print(f"    sync     {DIM}Push local files to server{RESET}")
    print(f"    pull     {DIM}Pull server files to local{RESET}")
    print(f"    status   {DIM}Show connection info{RESET}")
    print(f"    help     {DIM}Show this help{RESET}")
    print(f"    exit     {DIM}Quit cselab{RESET}")
    print()
    print(f"  {BOLD}Tips{RESET}")
    print(f"    {RED}!{RESET}cmd     {DIM}Run without syncing first{RESET}")
    print(f"    Tab      {DIM}Auto-complete commands & paths{RESET}")
    print(f"    Ctrl+C   {DIM}Cancel current command{RESET}")
    print(f"    Ctrl+D   {DIM}Quit{RESET}")
    print()


# ── Main REPL ──

class Repl:
    """Interactive REPL — connect, sync, execute on CSE server."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.state = _State(cfg)
        self.remote_dir = cfg.remote_workspace()

        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

        self.session = PromptSession(
            history=FileHistory(HISTORY_FILE),
            completer=_SmartCompleter(COMPLETIONS, cfg, self.remote_dir),
            auto_suggest=AutoSuggestFromHistory(),
            style=STYLE,
            lexer=_BangLexer(),
            bottom_toolbar=lambda: _toolbar(self.state),
            complete_while_typing=True,
            complete_in_thread=True,
            enable_suspend=True,
        )

    def run(self):
        """Run the REPL loop."""
        self._startup()

        while True:
            try:
                cmd = self.session.prompt([("class:prompt", "> ")]).strip()
            except KeyboardInterrupt:
                continue
            except EOFError:
                print(f"\n  {DIM}Bye.{RESET}")
                break

            if not cmd:
                continue

            first = cmd.split()[0]
            if first in ("exit", "quit"):
                print(f"  {DIM}Bye.{RESET}")
                break

            if first == "help":
                _cmd_help()
                _rule()
                continue

            self._execute(cmd)
            _rule()

    def _startup(self):
        """Connect, show banner, first-time tips."""
        from cselab.banner import print_banner
        from cselab import __version__

        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

        print(f"\n  {DIM}Connecting to {self.cfg.host}...{RESET}", end=" ", flush=True)
        if connect(self.cfg):
            print(f"{GREEN}ok{RESET}")
        else:
            print(f"{RED}failed{RESET}")
            sys.exit(1)

        print_banner(__version__, self.cfg.user, self.cfg.host)
        self.state.connected = True

        try:
            history_exists = os.path.exists(HISTORY_FILE) and os.path.getsize(HISTORY_FILE) > 0
        except OSError:
            history_exists = False

        if not history_exists:
            print()
            print(f"  {DIM}Examples:{RESET}")
            print(f"    1521 autotest lab01   {DIM}run autotest{RESET}")
            print(f"    give cs1521 lab01 *.c {DIM}submit files{RESET}")
            print(f"    dcc prog.c -o prog    {DIM}compile C{RESET}")
            print(f"  {DIM}Start typing for suggestions. {RESET}help{DIM} for more.{RESET}")

        _rule()

    def _execute(self, cmd: str):
        """Dispatch a single command."""
        first = cmd.split()[0]

        try:
            if first == "sync":
                self._cmd_sync()
                return

            if first == "pull":
                self._cmd_pull()
                return

            if first == "status":
                self._cmd_status()
                return

            # ! prefix = skip sync
            skip_sync = cmd.startswith("!")
            if skip_sync:
                cmd = cmd[1:].strip()
                if not cmd:
                    return
                print(f"  {DIM}(sync skipped){RESET}")

            # Auto-reconnect
            if not self._ensure_connected():
                return

            # Sync unless skipped
            if not skip_sync:
                if not self._sync_up():
                    return

            # Forward to server
            self.state.cmd_count += 1
            exit_code = ssh_exec(self.cfg, cmd, interactive=True, cwd=self.remote_dir)
            if exit_code != 0:
                print(f"  {RED}{DOT_OFF}{RESET} {DIM}exit {exit_code}{RESET}")

        except KeyboardInterrupt:
            print(f"\r\033[K  {DIM}cancelled{RESET}")
        except subprocess.TimeoutExpired:
            print(f"  {RED}{DOT_OFF}{RESET} {DIM}timed out — try again{RESET}")
        except OSError as e:
            print(f"  {RED}{DOT_OFF}{RESET} {DIM}error: {e}{RESET}")

    def _ensure_connected(self) -> bool:
        """Check connection and auto-reconnect if needed."""
        if self.state.connected:
            self.state.connected = is_connected(self.cfg)
        if not self.state.connected:
            print(f"  {DIM}reconnecting...{RESET}", end=" ", flush=True)
            if connect(self.cfg, timeout=10):
                print(f"{GREEN}ok{RESET}")
                self.state.connected = True
            else:
                print(f"{RED}failed — check connection or type 'status'{RESET}")
                return False
        return True

    def _sync_up(self) -> bool:
        """Sync local files to remote. Returns True on success."""
        t = time.time()
        ok = rsync_up(self.cfg, ".", self.remote_dir, timeout=10)
        elapsed = time.time() - t
        self.state.last_sync = f"{elapsed:.1f}s"
        if ok:
            print(f"  {GREEN}{DOT_ON}{RESET} {DIM}sync {elapsed:.1f}s{RESET}", flush=True)
            return True
        self.state.connected = False
        print(f"  {RED}{DOT_OFF}{RESET} {DIM}sync failed — use {RESET}!cmd{DIM} to skip or {RESET}status{DIM} to check{RESET}")
        return False

    def _cmd_sync(self):
        t = time.time()
        ok = rsync_up(self.cfg, ".", self.remote_dir, timeout=10)
        elapsed = time.time() - t
        self.state.last_sync = f"{elapsed:.1f}s"
        if ok:
            print(f"  {GREEN}{DOT_ON}{RESET} {DIM}synced ({elapsed:.1f}s){RESET}")
        else:
            print(f"  {RED}{DOT_OFF}{RESET} {RED}sync failed{RESET}")

    def _cmd_pull(self):
        t = time.time()
        ok = rsync_down(self.cfg, self.remote_dir, ".", timeout=10)
        elapsed = time.time() - t
        if ok:
            print(f"  {GREEN}{DOT_ON}{RESET} {DIM}pulled ({elapsed:.1f}s){RESET}")
        else:
            print(f"  {RED}{DOT_OFF}{RESET} {RED}pull failed{RESET}")

    def _cmd_status(self):
        self.state.connected = is_connected(self.cfg)
        if self.state.connected:
            s = f"{GREEN}{DOT_ON} connected{RESET}"
        else:
            s = f"{RED}{DOT_OFF} disconnected{RESET}"
        print(f"  {self.cfg.user}@{self.cfg.host} {s}")
        print(f"  ~/{self.remote_dir}")


def repl(cfg: Config) -> None:
    """Run the interactive REPL loop."""
    try:
        Repl(cfg).run()
    except KeyboardInterrupt:
        print()
