"""Config management for cselab."""

import os
import sys
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # Python < 3.11
    except ImportError:
        tomllib = None

CONFIG_DIR = Path.home() / ".config" / "cselab"
CONFIG_FILE = CONFIG_DIR / "config.toml"
SOCKET_DIR = Path("/tmp")

DEFAULT_CONFIG = """\
[server]
host = "cse.unsw.edu.au"
port = 22
user = "z5555555"  # your zID

[auth]
method = "password"
# password = ""  # optional, will prompt if missing

# [auth]
# method = "key"
# key_path = "~/.ssh/id_rsa"

[sync]
exclude = [".git", "__pycache__", "node_modules", ".venv", "target"]
"""


@dataclass
class Config:
    host: str = "cse.unsw.edu.au"
    port: int = 22
    user: str = ""
    auth_method: str = "password"
    password: str | None = None
    key_path: str | None = None
    exclude: list[str] = field(default_factory=lambda: [".git", "__pycache__", "node_modules", ".venv", "target"])

    @property
    def socket_path(self) -> Path:
        return SOCKET_DIR / f"cselab-{self.user}@{self.host}-{self.port}"

    def remote_workspace(self, local_dir: str | None = None) -> str:
        """Get remote workspace path based on local directory hash."""
        d = local_dir or os.getcwd()
        h = hashlib.md5(d.encode()).hexdigest()[:12]
        name = Path(d).name
        return f".cselab/workspaces/{name}-{h}"


def load_config() -> Config:
    if not CONFIG_FILE.exists():
        print(f"No config found. Run: cselab init", file=sys.stderr)
        sys.exit(1)

    if tomllib is None:
        print("Python 3.11+ required (or install tomli: pip install tomli)", file=sys.stderr)
        sys.exit(1)

    with open(CONFIG_FILE, "rb") as f:
        raw = tomllib.load(f)

    server = raw.get("server", {})
    auth = raw.get("auth", {})
    sync = raw.get("sync", {})

    return Config(
        host=server.get("host", "cse.unsw.edu.au"),
        port=server.get("port", 22),
        user=server.get("user", ""),
        auth_method=auth.get("method", "password"),
        password=auth.get("password"),
        key_path=auth.get("key_path"),
        exclude=sync.get("exclude", [".git", "__pycache__", "node_modules", ".venv", "target"]),
    )


def init_config(user: str = "", password: str = "") -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    content = DEFAULT_CONFIG
    if user:
        content = content.replace('z5555555', user)
    if password:
        # Escape backslashes and quotes for TOML
        escaped = password.replace('\\', '\\\\').replace('"', '\\"')
        content = content.replace('# password = ""', f'password = "{escaped}"')
    CONFIG_FILE.write_text(content)
    return CONFIG_FILE
