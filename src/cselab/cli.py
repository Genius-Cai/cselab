"""CLI entry point for cselab."""

import argparse
import os
import re
import subprocess
import sys
import time

from cselab import __version__
from cselab.config import Config, load_config, init_config
from cselab.theme import GREEN, RED, DIM, BOLD, YELLOW, MAGENTA, TEAL, RESET, SEP


def cmd_init(args):
    """Initialize config file."""
    user = args.user or input("zID (e.g. z5555555): ").strip()
    password = args.password or input("Password (leave empty to prompt each time): ").strip()
    path = init_config(user=user, password=password)
    print(f"Config created: {path}")
    print(f"Edit with: nano {path}")


def _flush():
    sys.stdout.flush()
    sys.stderr.flush()


def cmd_run(args):
    """Sync files and run command on CSE server."""
    from cselab.connection import connect, rsync_up, ssh_exec

    cfg = load_config()
    command = " ".join(args.command)
    remote_dir = cfg.remote_workspace()

    # Step 1: Connect
    t0 = time.time()
    print(f"{DIM}[1/3] Connecting to {cfg.host}...{RESET}", end="", flush=True)
    try:
        if not connect(cfg):
            print(f" {RED}FAILED{RESET}", flush=True)
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"  {RED}connection timed out{RESET}", flush=True)
        sys.exit(1)
    print(f" {GREEN}OK{RESET} ({time.time()-t0:.1f}s)", flush=True)

    # Step 2: Sync
    if not args.no_sync:
        t1 = time.time()
        print(f"{DIM}[2/3] Syncing files...{RESET}", end="", flush=True)
        _flush()
        try:
            if not rsync_up(cfg, ".", remote_dir):
                print(f" {RED}FAILED{RESET}", flush=True)
                sys.exit(1)
        except subprocess.TimeoutExpired:
            print(f"  {RED}timed out{RESET}", flush=True)
            sys.exit(1)
        print(f" {GREEN}OK{RESET} ({time.time()-t1:.1f}s)", flush=True)
    else:
        print(f"{DIM}[2/3] Sync skipped{RESET}", flush=True)
        _flush()
        ssh_exec(cfg, f"mkdir -p {remote_dir}", interactive=False)

    # Step 3: Run command
    print(f"{DIM}[3/3] Running:{RESET} {YELLOW}{command}{RESET}", flush=True)
    print(f"{MAGENTA}{SEP}{RESET}", flush=True)
    _flush()

    exit_code = ssh_exec(cfg, command, interactive=True, cwd=remote_dir)

    _flush()
    print(f"{MAGENTA}{SEP}{RESET}", flush=True)
    if exit_code == 0:
        print(f"Exit: {GREEN}OK{RESET}", flush=True)
    else:
        print(f"Exit: {RED}{exit_code}{RESET}", flush=True)

    sys.exit(exit_code)


def cmd_sync(args):
    """Sync local files to remote."""
    from cselab.connection import connect, rsync_up

    cfg = load_config()
    remote_dir = cfg.remote_workspace()

    try:
        if not connect(cfg):
            print("Connection failed", file=sys.stderr)
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"  {RED}connection timed out{RESET}", flush=True)
        sys.exit(1)

    print(f"Syncing to {cfg.host}:{remote_dir}...")
    try:
        if rsync_up(cfg, ".", remote_dir):
            print("Done")
        else:
            print("Sync failed", file=sys.stderr)
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"  {RED}timed out{RESET}", flush=True)
        sys.exit(1)


def cmd_pull(args):
    """Pull remote files back to local."""
    from cselab.connection import connect, rsync_down

    cfg = load_config()
    remote_dir = cfg.remote_workspace()
    target = args.dest or "."

    try:
        if not connect(cfg):
            print("Connection failed", file=sys.stderr)
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"  {RED}connection timed out{RESET}", flush=True)
        sys.exit(1)

    print(f"Pulling from {cfg.host}:{remote_dir}...")
    try:
        if rsync_down(cfg, remote_dir, target):
            print("Done")
        else:
            print("Pull failed", file=sys.stderr)
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"  {RED}timed out{RESET}", flush=True)
        sys.exit(1)


def cmd_ssh(args):
    """Open interactive SSH session in workspace."""
    from cselab.connection import connect, ssh_exec

    cfg = load_config()
    remote_dir = cfg.remote_workspace()

    try:
        if not connect(cfg):
            print("Connection failed", file=sys.stderr)
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"  {RED}connection timed out{RESET}", flush=True)
        sys.exit(1)

    from shlex import quote as shq
    ssh_exec(cfg, f"cd {shq(remote_dir)} 2>/dev/null; exec $SHELL -l", interactive=True)


def cmd_clean(args):
    """Clean remote workspaces."""
    from cselab.connection import connect, ssh_exec

    cfg = load_config()

    try:
        if not connect(cfg):
            print("Connection failed", file=sys.stderr)
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"  {RED}connection timed out{RESET}", flush=True)
        sys.exit(1)

    print("Cleaning remote workspaces...")
    ssh_exec(cfg, "rm -rf ~/.cselab/workspaces && echo 'Cleaned'", interactive=False)


def cmd_config(args):
    """Show config file path and contents."""
    from cselab.config import CONFIG_FILE
    print(f"Config: {CONFIG_FILE}")
    if CONFIG_FILE.exists():
        print(CONFIG_FILE.read_text())


def cmd_disconnect(args):
    """Close SSH ControlMaster connection."""
    from cselab.connection import disconnect

    cfg = load_config()
    disconnect(cfg)
    print("Disconnected")


def cmd_watch(args):
    """Watch for file changes and auto-run command."""
    from cselab.connection import connect, rsync_up, ssh_exec
    import subprocess as sp

    cfg = load_config()
    command = " ".join(args.command)
    remote_dir = cfg.remote_workspace()

    if not connect(cfg):
        print("Connection failed", file=sys.stderr)
        sys.exit(1)

    print(f"Watching for changes... (Ctrl+C to stop)")
    print(f"Command: {command}\n")

    # Use fswatch if available, otherwise poll
    try:
        sp.run(["which", "fswatch"], capture_output=True, check=True)
        has_fswatch = True
    except (sp.CalledProcessError, FileNotFoundError):
        has_fswatch = False

    if has_fswatch:
        _watch_fswatch(cfg, command, remote_dir)
    else:
        _watch_poll(cfg, command, remote_dir)


def _watch_fswatch(cfg: Config, command: str, remote_dir: str):
    """Watch using fswatch (macOS)."""
    import subprocess as sp
    from cselab.connection import rsync_up, ssh_exec

    excludes = []
    for pat in cfg.exclude + [".git"]:
        excludes += ["--exclude", pat]

    proc = sp.Popen(
        ["fswatch", "-1", "--latency=1"] + excludes + ["."],
        stdout=sp.PIPE,
    )

    try:
        while True:
            proc.wait()
            print(f"\n{TEAL}Change detected, running...{RESET}")
            try:
                rsync_up(cfg, ".", remote_dir)
                print(f"{YELLOW}> {command}{RESET}")
                print(f"{MAGENTA}{SEP}{RESET}")
                ssh_exec(cfg, command, interactive=True, cwd=remote_dir)
                print(f"{MAGENTA}{SEP}{RESET}\n")
            except subprocess.TimeoutExpired:
                print(f"  {RED}timed out{RESET}", flush=True)
            # Restart fswatch
            proc = sp.Popen(
                ["fswatch", "-1", "--latency=1"] + excludes + ["."],
                stdout=sp.PIPE,
            )
    except KeyboardInterrupt:
        proc.kill()
        print("\nStopped watching")


def _watch_poll(cfg: Config, command: str, remote_dir: str, interval: float = 2.0):
    """Watch using polling (fallback)."""
    from cselab.connection import rsync_up, ssh_exec

    def _get_mtime():
        latest = 0
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in cfg.exclude and d != ".git"]
            for f in files:
                try:
                    mt = os.path.getmtime(os.path.join(root, f))
                    latest = max(latest, mt)
                except OSError:
                    pass
        return latest

    last_mtime = _get_mtime()
    try:
        while True:
            time.sleep(interval)
            current = _get_mtime()
            if current > last_mtime:
                last_mtime = current
                print(f"\n{TEAL}Change detected, running...{RESET}")
                try:
                    rsync_up(cfg, ".", remote_dir)
                    print(f"{YELLOW}> {command}{RESET}")
                    print(f"{MAGENTA}{SEP}{RESET}")
                    ssh_exec(cfg, command, interactive=True, cwd=remote_dir)
                    print(f"{MAGENTA}{SEP}{RESET}\n")
                except subprocess.TimeoutExpired:
                    print(f"  {RED}timed out{RESET}", flush=True)
    except KeyboardInterrupt:
        print("\nStopped watching")


def main():
    parser = argparse.ArgumentParser(
        prog="cselab",
        description="Run UNSW CSE commands locally - fast sync, interactive support",
    )
    parser.add_argument("-V", "--version", action="version", version=f"cselab {__version__}")
    sub = parser.add_subparsers(dest="subcmd")

    # init
    p_init = sub.add_parser("init", help="Setup config")
    p_init.add_argument("--user", "-u", help="zID")
    p_init.add_argument("--password", "-p", help="Password")

    # run
    p_run = sub.add_parser("run", help="Sync + run command")
    p_run.add_argument("command", nargs="+", help="Command to run")
    p_run.add_argument("--no-sync", action="store_true", help="Skip file sync")

    # sync
    sub.add_parser("sync", help="Sync local files to remote")

    # pull
    p_pull = sub.add_parser("pull", help="Pull remote files to local")
    p_pull.add_argument("--dest", "-d", help="Local destination (default: .)")

    # ssh
    sub.add_parser("ssh", help="Interactive SSH to workspace")

    # watch
    p_watch = sub.add_parser("watch", help="Watch changes + auto-run")
    p_watch.add_argument("command", nargs="+", help="Command to run on change")

    # clean
    sub.add_parser("clean", help="Clean remote workspaces")

    # config
    sub.add_parser("config", help="Show config")

    # disconnect
    sub.add_parser("disconnect", help="Close SSH connection")

    args = parser.parse_args()
    if not args.subcmd:
        from cselab.repl import repl
        from cselab.config import CONFIG_FILE
        import getpass as _gp

        if not CONFIG_FILE.exists():
            # Auto-init on first run
            print()
            print(f"  {BOLD}{GREEN}Welcome to cselab!{RESET}")
            print(f"  {DIM}Let's set up your CSE account.{RESET}")
            print()

            # zID with validation
            while True:
                user = input("  zID (e.g. z5555555): ").strip()
                if re.match(r'^z\d{7}$', user):
                    break
                if not user:
                    print(f"  {RED}zID is required.{RESET}")
                    continue
                print(f"  {RED}zID should be z + 7 digits (e.g. z5555555){RESET}")

            # Password with confirmation
            while True:
                password = _gp.getpass("  Password: ")
                confirm = _gp.getpass("  Confirm:  ")
                if password == confirm:
                    break
                print(f"  {RED}Passwords don't match. Try again.{RESET}")

            init_config(user=user, password=password)
            print(f"  {DIM}Config saved: {CONFIG_FILE}{RESET}")
            print(f"  {DIM}(password stored in plaintext){RESET}")
            print()

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
