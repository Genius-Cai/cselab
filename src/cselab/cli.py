"""CLI entry point for cselab."""

import argparse
import os
import sys
import time

from cselab import __version__
from cselab.config import Config, load_config, init_config


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
    print(f"\033[90m[1/3] Connecting to {cfg.host}...\033[0m", end="", flush=True)
    if not connect(cfg):
        print(" FAILED", flush=True)
        sys.exit(1)
    print(f" \033[32mOK\033[0m ({time.time()-t0:.1f}s)", flush=True)

    # Step 2: Sync
    if not args.no_sync:
        t1 = time.time()
        print(f"\033[90m[2/3] Syncing files...\033[0m", end="", flush=True)
        _flush()
        if not rsync_up(cfg, ".", remote_dir):
            print(" FAILED", flush=True)
            sys.exit(1)
        print(f" \033[32mOK\033[0m ({time.time()-t1:.1f}s)", flush=True)
    else:
        print(f"\033[90m[2/3] Sync skipped\033[0m", flush=True)
        _flush()
        ssh_exec(cfg, f"mkdir -p {remote_dir}", interactive=False)

    # Step 3: Run command
    print(f"\033[90m[3/3] Running:\033[0m \033[33m{command}\033[0m", flush=True)
    print("\033[35m" + "=" * 40 + "\033[0m", flush=True)
    _flush()

    exit_code = ssh_exec(cfg, command, interactive=True, cwd=remote_dir)

    _flush()
    print("\033[35m" + "=" * 40 + "\033[0m", flush=True)
    if exit_code == 0:
        print(f"Exit: \033[32mOK\033[0m", flush=True)
    else:
        print(f"Exit: \033[31m{exit_code}\033[0m", flush=True)

    sys.exit(exit_code)


def cmd_sync(args):
    """Sync local files to remote."""
    from cselab.connection import connect, rsync_up

    cfg = load_config()
    remote_dir = cfg.remote_workspace()

    if not connect(cfg):
        print("Connection failed", file=sys.stderr)
        sys.exit(1)

    print(f"Syncing to {cfg.host}:{remote_dir}...")
    if rsync_up(cfg, ".", remote_dir):
        print("Done")
    else:
        print("Sync failed", file=sys.stderr)
        sys.exit(1)


def cmd_pull(args):
    """Pull remote files back to local."""
    from cselab.connection import connect, rsync_down

    cfg = load_config()
    remote_dir = cfg.remote_workspace()
    target = args.dest or "."

    if not connect(cfg):
        print("Connection failed", file=sys.stderr)
        sys.exit(1)

    print(f"Pulling from {cfg.host}:{remote_dir}...")
    if rsync_down(cfg, remote_dir, target):
        print("Done")
    else:
        print("Pull failed", file=sys.stderr)
        sys.exit(1)


def cmd_ssh(args):
    """Open interactive SSH session in workspace."""
    from cselab.connection import connect, ssh_exec

    cfg = load_config()
    remote_dir = cfg.remote_workspace()

    if not connect(cfg):
        print("Connection failed", file=sys.stderr)
        sys.exit(1)

    ssh_exec(cfg, f"cd {remote_dir} 2>/dev/null; exec $SHELL -l", interactive=True)


def cmd_clean(args):
    """Clean remote workspaces."""
    from cselab.connection import connect, ssh_exec

    cfg = load_config()

    if not connect(cfg):
        print("Connection failed", file=sys.stderr)
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
            print(f"\n\033[36mChange detected, running...\033[0m")
            rsync_up(cfg, ".", remote_dir)
            print(f"\033[33m> {command}\033[0m")
            print("\033[35m" + "=" * 40 + "\033[0m")
            ssh_exec(cfg, command, interactive=True, cwd=remote_dir)
            print("\033[35m" + "=" * 40 + "\033[0m\n")
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
                print(f"\n\033[36mChange detected, running...\033[0m")
                rsync_up(cfg, ".", remote_dir)
                print(f"\033[33m> {command}\033[0m")
                print("\033[35m" + "=" * 40 + "\033[0m")
                ssh_exec(cfg, command, interactive=True, cwd=remote_dir)
                print("\033[35m" + "=" * 40 + "\033[0m\n")
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
        parser.print_help()
        sys.exit(1)

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
