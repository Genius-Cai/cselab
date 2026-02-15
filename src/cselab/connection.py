"""SSH ControlMaster and rsync transport."""

import os
import sys
import stat
import signal
import subprocess
import tempfile
import getpass
from pathlib import Path

from cselab.config import Config


def _ssh_base_args(cfg: Config) -> list[str]:
    """Common SSH options."""
    return [
        "-o", f"ControlPath={cfg.socket_path}",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=60",
        "-o", "ServerAliveCountMax=3",
        "-p", str(cfg.port),
    ]


def _auth_args(cfg: Config) -> list[str]:
    """Auth-specific SSH options."""
    if cfg.auth_method == "key" and cfg.key_path:
        expanded = os.path.expanduser(cfg.key_path)
        return ["-i", expanded]
    return []


def _make_askpass(password: str) -> str:
    """Create a temporary SSH_ASKPASS script."""
    fd, path = tempfile.mkstemp(prefix="cselab_askpass_", suffix=".sh")
    with os.fdopen(fd, "w") as f:
        f.write(f"#!/bin/sh\necho '{password}'\n")
    os.chmod(path, stat.S_IRWXU)
    return path


def _askpass_env(password: str) -> tuple[dict, str]:
    """Create env dict with SSH_ASKPASS set. Returns (env, askpass_path)."""
    askpass_path = _make_askpass(password)
    env = os.environ.copy()
    env["SSH_ASKPASS"] = askpass_path
    env["SSH_ASKPASS_REQUIRE"] = "force"
    env["DISPLAY"] = env.get("DISPLAY", ":0")
    return env, askpass_path


def is_connected(cfg: Config) -> bool:
    """Check if SSH ControlMaster is running."""
    try:
        result = subprocess.run(
            ["ssh", "-O", "check"] + _ssh_base_args(cfg) + [f"{cfg.user}@{cfg.host}"],
            capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def connect(cfg: Config) -> bool:
    """Start SSH ControlMaster connection."""
    if is_connected(cfg):
        return True

    args = [
        "ssh", "-fNM",
        "-o", "ControlPersist=1800",
    ] + _ssh_base_args(cfg) + _auth_args(cfg) + [f"{cfg.user}@{cfg.host}"]

    askpass_path = None

    if cfg.auth_method == "password":
        password = cfg.password
        if not password:
            password = getpass.getpass(f"Password for {cfg.user}@{cfg.host}: ")

        env, askpass_path = _askpass_env(password)
        # Need to start ssh without a TTY for SSH_ASKPASS to work
        try:
            result = subprocess.run(
                args, env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True, timeout=30,
            )
        finally:
            if askpass_path and os.path.exists(askpass_path):
                os.unlink(askpass_path)
    else:
        result = subprocess.run(args, timeout=30)

    if result.returncode != 0:
        stderr = result.stderr.decode() if result.stderr else ""
        print(f"SSH connection failed: {stderr}", file=sys.stderr)
        return False

    return is_connected(cfg)


def disconnect(cfg: Config):
    """Stop SSH ControlMaster."""
    if is_connected(cfg):
        subprocess.run(
            ["ssh", "-O", "exit"] + _ssh_base_args(cfg) + [f"{cfg.user}@{cfg.host}"],
            capture_output=True, timeout=10,
        )


def ssh_exec(cfg: Config, command: str, interactive: bool = True, cwd: str | None = None) -> int:
    """Execute a command on the remote server via ControlMaster."""
    full_cmd = command
    if cwd:
        full_cmd = f"cd {cwd} && {command}"

    args = ["ssh"]
    # Only use -t for PTY when we actually have a terminal
    if interactive and sys.stdin.isatty():
        args.append("-tt")
    args += _ssh_base_args(cfg) + _auth_args(cfg) + [f"{cfg.user}@{cfg.host}", full_cmd]

    result = subprocess.run(args)
    return result.returncode


def rsync_up(cfg: Config, local_dir: str, remote_dir: str) -> bool:
    """Upload local directory to remote via rsync."""
    # Ensure remote dir exists (quiet)
    subprocess.run(
        ["ssh"] + _ssh_base_args(cfg) + _auth_args(cfg) +
        [f"{cfg.user}@{cfg.host}", f"mkdir -p {remote_dir}"],
        capture_output=True, timeout=30,
    )

    ssh_cmd = "ssh " + " ".join(_ssh_base_args(cfg) + _auth_args(cfg))

    # Ensure trailing slash for rsync behavior (sync contents, not dir itself)
    local = local_dir.rstrip("/") + "/"
    remote = f"{cfg.user}@{cfg.host}:{remote_dir}/"

    args = [
        "rsync", "-az", "--delete",
        "--filter=:- .gitignore",
        "--filter=:- .ignore",
    ]

    # Add exclude patterns from config
    for pat in cfg.exclude:
        args += ["--exclude", pat]

    args += [
        "-e", ssh_cmd,
        local, remote,
    ]

    result = subprocess.run(args, capture_output=True, timeout=120)
    return result.returncode == 0


def rsync_down(cfg: Config, remote_dir: str, local_dir: str) -> bool:
    """Download remote directory to local via rsync."""
    ssh_cmd = "ssh " + " ".join(_ssh_base_args(cfg) + _auth_args(cfg))

    remote = f"{cfg.user}@{cfg.host}:{remote_dir}/"
    local = local_dir.rstrip("/") + "/"

    args = [
        "rsync", "-az",
        "-e", ssh_cmd,
        remote, local,
    ]

    result = subprocess.run(args, capture_output=True, timeout=120)
    return result.returncode == 0
