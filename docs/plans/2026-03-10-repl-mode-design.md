# cselab v0.2.0 — Interactive REPL Mode

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an interactive REPL mode so students type CSE commands directly (no `cselab run "..."` wrapper), plus a branded welcome banner with mascot.

**Architecture:** When `cselab` is invoked with no subcommand, enter a `readline`-powered REPL loop that auto-syncs + forwards each command to the CSE server via the existing SSH ControlMaster. All existing subcommands (`cselab run`, `cselab sync`, etc.) remain unchanged.

**Tech Stack:** Python stdlib only (`readline`, `shutil`, `datetime`). Zero new dependencies.

---

## Context for Implementer

### Codebase Layout
```
src/cselab/
├── __init__.py        # __version__ = "0.1.0"
├── __main__.py        # python -m cselab
├── cli.py             # argparse, 9 subcommands, main()
├── config.py          # Config dataclass, TOML, load_config()
└── connection.py      # connect(), rsync_up(), ssh_exec(), etc.
```

### Key Functions (connection.py)
- `connect(cfg) -> bool` — start SSH ControlMaster if not running
- `is_connected(cfg) -> bool` — check ControlMaster status
- `rsync_up(cfg, local, remote) -> bool` — sync local → remote
- `ssh_exec(cfg, cmd, interactive=True, cwd=None) -> int` — run command on server

### CSE Command Patterns (all forwarded as-is)
```
1521 autotest collatz              # run autotest
give cs1521 lab03 collatz.c        # submit
1521 classrun -sturec              # check grades
dcc collatz.c -o collatz           # compile
make && ./test                     # any shell command
```

### Design Decisions
- REPL replaces the current "print help" when no subcommand given
- Each REPL command: rsync_up → ssh_exec (2 steps, not 3 — connect happens once at startup)
- Built-in REPL commands: `exit`, `quit`, `sync`, `pull`, `status`, `help`
- Mascot: "Labby" — ASCII art Erlenmeyer flask with face
- Seasonal variants via date detection (stretch goal)
- Version bump: 0.1.0 → 0.2.0

---

## Task 1: Create banner.py — Mascot + Welcome Screen

**Files:**
- Create: `src/cselab/banner.py`

**Step 1: Write banner.py**

```python
"""Welcome banner with Labby mascot for cselab REPL."""

import datetime

# ANSI color codes
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
DIM = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Labby the lab flask — default
LABBY_DEFAULT = f"""\
{GREEN}     ○ ○
    ┌───┐
    │● ●│
    │ ◡ │
   ┌┘   └┐
   │     │
   └─┬─┬─┘
     ╰─╯{RESET}"""

# December: Santa hat
LABBY_XMAS = f"""\
{GREEN}    🎅
    ┌───┐
    │● ●│
    │ ◡ │
   ┌┘   └┐
   │     │
   └─┬─┬─┘
     ╰─╯{RESET}"""

# October: spooky
LABBY_HALLOWEEN = f"""\
{GREEN}    ○ ○
    ┌───┐
    │◉ ◉│
    │ ▿ │
   ┌┘   └┐
   │ ~ ~ │
   └─┬─┬─┘
     ╰─╯{RESET}"""

# May-June: graduation
LABBY_GRAD = f"""\
{GREEN}    🎓
    ┌───┐
    │● ●│
    │ ◡ │
   ┌┘   └┐
   │     │
   └─┬─┬─┘
     ╰─╯{RESET}"""


def get_labby() -> str:
    """Return seasonal Labby variant."""
    month = datetime.date.today().month
    if month == 12:
        return LABBY_XMAS
    elif month == 10:
        return LABBY_HALLOWEEN
    elif month in (5, 6):
        return LABBY_GRAD
    return LABBY_DEFAULT


def print_banner(version: str, user: str, host: str):
    """Print the cselab welcome banner."""
    labby = get_labby()
    # Split labby into lines for side-by-side layout
    labby_lines = labby.split("\n")
    info_lines = [
        "",
        f"  {BOLD}cselab{RESET} v{version}",
        f"  {DIM}local edit, remote test{RESET}",
        f"  {CYAN}{user}@{host}{RESET}",
        "",
        f"  {DIM}Type any CSE command. Ctrl+C to exit.{RESET}",
        "",
    ]

    # Pad to same length
    max_lines = max(len(labby_lines), len(info_lines))
    labby_lines += [""] * (max_lines - len(labby_lines))
    info_lines += [""] * (max_lines - len(info_lines))

    print()
    for l, r in zip(labby_lines, info_lines):
        # Pad labby column (account for ANSI codes in width)
        print(f"  {l:<20s}{r}")
    print()
```

**Step 2: Manually verify**

```bash
cd /Users/geniusc/Projects/01-WIP-Education/cselab
python3 -c "from cselab.banner import print_banner; print_banner('0.2.0', 'z5502277', 'cse.unsw.edu.au')"
```

Expected: Labby mascot on left, version info on right, colored output.

**Step 3: Commit**

```bash
git add src/cselab/banner.py
git commit -m "add welcome banner with Labby mascot"
```

---

## Task 2: Create repl.py — Interactive Loop

**Files:**
- Create: `src/cselab/repl.py`

**Step 1: Write repl.py**

```python
"""Interactive REPL for cselab — type CSE commands directly."""

import readline  # noqa: F401 — importing enables history/arrow keys
import sys
import time

from cselab.config import Config
from cselab.connection import connect, is_connected, rsync_up, ssh_exec
from cselab.banner import print_banner, GREEN, DIM, RESET, YELLOW

PROMPT = f"{GREEN}⚡{RESET} "

BUILTIN_COMMANDS = {
    "exit": "Exit cselab",
    "quit": "Exit cselab",
    "sync": "Sync local files to remote (no command)",
    "pull": "Pull remote files to local",
    "status": "Show connection status",
    "help": "Show available commands",
}


def _print_sync_status(ok: bool, elapsed: float):
    if ok:
        print(f"  {DIM}[sync]{RESET} {GREEN}OK{RESET} ({elapsed:.1f}s)")
    else:
        print(f"  {DIM}[sync]{RESET} \033[31mFAILED\033[0m")


def _handle_builtin(cmd: str, cfg: Config, remote_dir: str) -> bool:
    """Handle built-in commands. Returns True if handled."""
    if cmd in ("exit", "quit"):
        print(f"  {DIM}Bye!{RESET} (･ω･)ノ")
        return True  # signal exit

    if cmd == "help":
        print(f"\n  {DIM}Built-in commands:{RESET}")
        for name, desc in BUILTIN_COMMANDS.items():
            print(f"    {YELLOW}{name:<10s}{RESET} {desc}")
        print(f"\n  {DIM}Everything else is forwarded to the CSE server.{RESET}")
        print(f"  {DIM}Examples:{RESET}")
        print(f"    1521 autotest collatz")
        print(f"    give cs1521 lab03 collatz.c")
        print(f"    dcc collatz.c -o collatz")
        print()
        return False

    if cmd == "status":
        connected = is_connected(cfg)
        status = f"{GREEN}connected{RESET}" if connected else "\033[31mdisconnected\033[0m"
        print(f"  {cfg.user}@{cfg.host} — {status}")
        print(f"  workspace: {remote_dir}")
        return False

    if cmd == "sync":
        from cselab.connection import rsync_up
        t = time.time()
        ok = rsync_up(cfg, ".", remote_dir)
        _print_sync_status(ok, time.time() - t)
        return False

    if cmd == "pull":
        from cselab.connection import rsync_down
        print(f"  {DIM}Pulling...{RESET}", end="", flush=True)
        ok = rsync_down(cfg, remote_dir, ".")
        if ok:
            print(f" {GREEN}OK{RESET}")
        else:
            print(f" \033[31mFAILED\033[0m")
        return False

    return False


def repl(cfg: Config):
    """Main REPL loop."""
    from cselab import __version__

    remote_dir = cfg.remote_workspace()

    # Print welcome banner
    print_banner(__version__, cfg.user, cfg.host)

    # Connect once at startup
    print(f"  {DIM}Connecting...{RESET}", end="", flush=True)
    if not connect(cfg):
        print(f" \033[31mFAILED\033[0m")
        print(f"  Check your config: cselab init")
        sys.exit(1)
    print(f" {GREEN}OK{RESET}")
    print()

    # REPL loop
    while True:
        try:
            cmd = input(PROMPT).strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n  {DIM}Bye!{RESET} (･ω･)ノ")
            break

        if not cmd:
            continue

        # Built-in commands
        if cmd.split()[0] in BUILTIN_COMMANDS:
            should_exit = _handle_builtin(cmd, cfg, remote_dir)
            if should_exit:
                break
            continue

        # Default: sync + run on server
        t = time.time()
        ok = rsync_up(cfg, ".", remote_dir)
        _print_sync_status(ok, time.time() - t)

        if not ok:
            continue

        exit_code = ssh_exec(cfg, cmd, interactive=True, cwd=remote_dir)
        if exit_code != 0:
            print(f"  {DIM}exit: \033[31m{exit_code}\033[0m{RESET}")
```

**Step 2: Manually verify with a dry test**

```bash
python3 -c "
from cselab.repl import BUILTIN_COMMANDS
print('Built-in commands:', list(BUILTIN_COMMANDS.keys()))
"
```

Expected: `['exit', 'quit', 'sync', 'pull', 'status', 'help']`

**Step 3: Commit**

```bash
git add src/cselab/repl.py
git commit -m "add interactive REPL with sync + forward"
```

---

## Task 3: Wire REPL into cli.py

**Files:**
- Modify: `src/cselab/cli.py` (lines 252-310, the `main()` function)
- Modify: `src/cselab/__init__.py` (version bump)

**Step 1: Update __init__.py version**

Change `__version__` from `"0.1.0"` to `"0.2.0"`.

**Step 2: Modify cli.py main()**

Replace the block at lines 293-309 (the `if not args.subcmd` block and handler dispatch):

```python
    args = parser.parse_args()

    # No subcommand → enter REPL mode
    if not args.subcmd:
        from cselab.repl import repl
        cfg = load_config()
        repl(cfg)
        return

    handlers = {
        "init": cmd_init,
        "run": cmd_run,
        "sync": cmd_sync,
        "pull": cmd_pull,
        "ssh": cmd_ssh,
        "watch": cmd_watch,
        "clean": cmd_clean,
        "config": cmd_config,
        "disconnect": cmd_disconnect,
    }
    handlers[args.subcmd](args)
```

**Step 3: Test all paths**

```bash
# REPL mode (will need real config to connect)
cselab

# Headless mode still works
cselab run --help
cselab --version

# Other subcommands still work
cselab config
```

**Step 4: Commit**

```bash
git add src/cselab/__init__.py src/cselab/cli.py
git commit -m "wire REPL as default mode, bump to v0.2.0"
```

---

## Task 4: Update pyproject.toml version

**Files:**
- Modify: `pyproject.toml` (line 6)

**Step 1: Change version**

```
version = "0.2.0"
```

**Step 2: Verify**

```bash
python3 -c "import cselab; print(cselab.__version__)"
# Should print: 0.2.0
```

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "bump pyproject.toml to v0.2.0"
```

---

## Task 5: End-to-End Test on Real CSE Server

**Files:** None (testing only)

**Step 1: Reinstall**

```bash
cd /Users/geniusc/Projects/01-WIP-Education/cselab
pip install -e .
```

**Step 2: Test REPL mode**

```bash
cd ~/COMP1521/lab03   # or any directory with CSE files
cselab
# Should see: Labby mascot + welcome banner + connection
# Type: 1521 autotest collatz
# Should see: [sync] OK → autotest output
# Type: exit
```

**Step 3: Test headless mode still works**

```bash
cselab run "1521 autotest collatz"
# Should work exactly as before (3-step output)
```

**Step 4: Test edge cases**

```bash
# Empty input (just press Enter)
# Ctrl+C (should exit gracefully)
# Ctrl+D (should exit gracefully)
# Invalid command (server returns error, show exit code)
# help (show built-in commands)
# status (show connection info)
```

---

## Task 6: Update README + Skill Docs

**Files:**
- Modify: `README.md` — add REPL usage section
- Modify: `skills/cselab.md` — add REPL mode docs

**Step 1: Add REPL section to README**

After the "Quick Start" section, add:

```markdown
## Interactive Mode

Just type `cselab` — no subcommand needed:

```
$ cselab

     ○ ○
    ┌───┐
    │● ●│    cselab v0.2.0
    │ ◡ │    local edit, remote test
   ┌┘   └┐   z5502277@cse.unsw.edu.au
   │     │
   └─┬─┬─┘   Type any CSE command. Ctrl+C to exit.
     ╰─╯

  Connecting... OK

⚡ 1521 autotest collatz
  [sync] OK (0.1s)
  5 tests passed 0 tests failed

⚡ give cs1521 lab03 collatz.c
  [sync] OK (0.1s)
  Submission received.
```

Same commands as the CSE server. Zero learning curve.
```

**Step 2: Update skills/cselab.md**

Add REPL mode to the Available Commands table and add usage examples.

**Step 3: Commit**

```bash
git add README.md skills/cselab.md
git commit -m "document REPL mode in README and skill"
```

---

## Task 7: Update VHS Demo Tape

**Files:**
- Modify: `assets/demo-typing.tape` — show REPL mode instead of `cselab run`
- Modify: `assets/fake-autotest.sh` — update to match real output exactly

**Step 1: Fix fake-autotest.sh**

Add the missing `dcc -fsanitize=valgrind` line to match real output:

```bash
#!/bin/bash
# Simulates real cselab REPL autotest output
sleep 0.2
echo -e "  \033[90m[sync]\033[0m \033[32mOK\033[0m (0.1s)"
sleep 0.1
echo "1521 check-recursion collatz.c"
echo "dcc -fsanitize=address -o collatz collatz.c"
echo "dcc -fsanitize=valgrind -o collatz collatz.c"
sleep 0.15
echo "Test 0 (./collatz 1) - passed"
sleep 0.1
echo "Test 1 (./collatz 12) - passed"
sleep 0.1
echo "Test 2 (./collatz 10) - passed"
sleep 0.1
echo "Test 3 (./collatz 42) - passed"
sleep 0.1
echo "Test 4 (./collatz 100) - passed"
sleep 0.15
echo -e "\033[32m5 tests passed\033[0m 0 tests failed"
```

**Step 2: Update demo-typing.tape for REPL**

New tape shows: `cselab` → banner → type command → output. Details TBD based on banner rendering.

**Step 3: Regenerate GIF**

```bash
vhs assets/demo-typing.tape
```

**Step 4: Commit**

```bash
git add assets/
git commit -m "update demo for REPL mode"
```

---

## Summary

| Task | Files | Estimate |
|------|-------|----------|
| 1. banner.py | +1 new | 5 min |
| 2. repl.py | +1 new | 10 min |
| 3. Wire into cli.py | 2 modified | 5 min |
| 4. Version bump | 1 modified | 1 min |
| 5. E2E test | testing only | 10 min |
| 6. Update docs | 2 modified | 5 min |
| 7. Update demo | 2 modified | 5 min |
| **Total** | **4 new/modified** | **~40 min** |
