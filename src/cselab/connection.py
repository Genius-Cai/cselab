"""SSH ControlMaster and rsync transport."""

import os
import sys
import stat
import shlex
import subprocess
import tempfile
import getpass
from pathlib import Path

from cselab.config import Config


def _ssh_base_args(cfg: Config) -> list[str]:
    """Common SSH options."""
    return [
        "-o", f"ControlPath={cfg.socket_path}",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ConnectTimeout=5",
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=2",
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
    try:
        fd, path = tempfile.mkstemp(prefix="cselab_askpass_", suffix=".sh")
        with os.fdopen(fd, "w") as f:
            f.write(f"#!/bin/sh\necho {shlex.quote(password)}\n")
        os.chmod(path, stat.S_IRWXU)
    except OSError:
        return ""
    return path


def _askpass_env(password: str) -> tuple[dict, str]:
    """Create env dict with SSH_ASKPASS set. Returns (env, askpass_path)."""
    askpass_path = _make_askpass(password)
    env = os.environ.copy()
    env["SSH_ASKPASS"] = askpass_path
    env["SSH_ASKPASS_REQUIRE"] = "force"
    env["DISPLAY"] = env.get("DISPLAY", ":0")
    return env, askpass_path


def _translate_ssh_error(stderr: str) -> str:
    """Translate raw SSH errors into human-friendly messages."""
    s = stderr.lower()
    if "permission denied" in s:
        return "Wrong password? Run: cselab init"
    if "connection refused" in s:
        return "CSE server may be down. Try again later."
    if "no route to host" in s or "network is unreachable" in s:
        return "No network connection to CSE."
    if "connection timed out" in s or "timed out" in s:
        return "Connection timed out. Check your internet."
    if "host key verification" in s:
        return "Host key changed. Remove old key and retry."
    if stderr.strip():
        return f"SSH error: {stderr.strip().splitlines()[0]}"
    return "SSH connection failed."


def is_connected(cfg: Config) -> bool:
    """Check if SSH ControlMaster is running."""
    try:
        result = subprocess.run(
            ["ssh", "-O", "check"] + _ssh_base_args(cfg) + [f"{cfg.user}@{cfg.host}"],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def connect(cfg: Config, timeout: int = 30) -> bool:
    """Start SSH ControlMaster connection.

    Args:
        cfg: Connection configuration.
        timeout: Subprocess timeout in seconds. Use a shorter value (e.g. 10)
            for interactive reconnect in the REPL, default 30 for CLI commands.
    """
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
                capture_output=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return False
        finally:
            if askpass_path and os.path.exists(askpass_path):
                os.unlink(askpass_path)
    else:
        try:
            result = subprocess.run(
                args, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return False

    if result.returncode != 0:
        stderr = result.stderr.decode() if result.stderr else ""
        msg = _translate_ssh_error(stderr)
        print(f"  {msg}", file=sys.stderr)
        return False

    return is_connected(cfg)


def disconnect(cfg: Config):
    """Stop SSH ControlMaster."""
    if is_connected(cfg):
        try:
            subprocess.run(
                ["ssh", "-O", "exit"] + _ssh_base_args(cfg) + [f"{cfg.user}@{cfg.host}"],
                stdin=subprocess.DEVNULL, capture_output=True, timeout=10,
            )
        except subprocess.TimeoutExpired:
            pass


def ssh_exec(cfg: Config, command: str, interactive: bool = True, cwd: str | None = None) -> int:
    """Execute a command on the remote server via ControlMaster."""
    full_cmd = command
    if cwd:
        full_cmd = f"cd {shlex.quote(cwd)} && {command}"

    args = ["ssh"]
    # Only use -t for PTY when we actually have a terminal
    if interactive and sys.stdin.isatty():
        args.append("-tt")
    args += _ssh_base_args(cfg) + _auth_args(cfg) + [f"{cfg.user}@{cfg.host}", full_cmd]

    result = subprocess.run(args)
    return result.returncode


def rsync_up(cfg: Config, local_dir: str, remote_dir: str, timeout: int = 30) -> bool:
    """Upload local directory to remote via rsync."""
    # Ensure remote dir exists (quiet)
    try:
        subprocess.run(
            ["ssh"] + _ssh_base_args(cfg) + _auth_args(cfg) +
            [f"{cfg.user}@{cfg.host}", f"mkdir -p {shlex.quote(remote_dir)}"],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=min(timeout, 10),
        )
    except subprocess.TimeoutExpired:
        return False

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

    try:
        result = subprocess.run(
            args, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False
    return result.returncode == 0


def rsync_down(cfg: Config, remote_dir: str, local_dir: str, timeout: int = 30) -> bool:
    """Download remote directory to local via rsync."""
    ssh_cmd = "ssh " + " ".join(_ssh_base_args(cfg) + _auth_args(cfg))

    remote = f"{cfg.user}@{cfg.host}:{remote_dir}/"
    local = local_dir.rstrip("/") + "/"

    args = [
        "rsync", "-az",
        "-e", ssh_cmd,
        remote, local,
    ]

    try:
        result = subprocess.run(
            args, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False
    return result.returncode == 0
