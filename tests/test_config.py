"""Tests for cselab.config — load_config, init_config, Config dataclass."""

import sys
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest


# ---------------------------------------------------------------------------
# Config dataclass
# ---------------------------------------------------------------------------

def test_config_defaults():
    from cselab.config import Config

    cfg = Config()
    assert cfg.host == "cse.unsw.edu.au"
    assert cfg.port == 22
    assert cfg.user == ""
    assert cfg.auth_method == "password"
    assert cfg.password is None
    assert cfg.key_path is None
    assert ".git" in cfg.exclude


def test_config_socket_path():
    from cselab.config import Config

    cfg = Config(user="z1234567", host="cse.unsw.edu.au", port=22)
    sp = cfg.socket_path
    assert "cselab-z1234567@cse.unsw.edu.au-22" in str(sp)


def test_config_remote_workspace_deterministic():
    from cselab.config import Config

    cfg = Config()
    ws1 = cfg.remote_workspace("/tmp/myproject")
    ws2 = cfg.remote_workspace("/tmp/myproject")
    assert ws1 == ws2
    assert ws1.startswith(".cselab/workspaces/myproject-")


def test_config_remote_workspace_different_dirs():
    from cselab.config import Config

    cfg = Config()
    ws1 = cfg.remote_workspace("/tmp/projectA")
    ws2 = cfg.remote_workspace("/tmp/projectB")
    assert ws1 != ws2


# ---------------------------------------------------------------------------
# load_config — valid TOML
# ---------------------------------------------------------------------------

def test_load_config_valid(tmp_path):
    """Valid TOML file should produce a Config with correct values."""
    from cselab.config import Config

    toml_content = b"""
[server]
host = "vlab.unsw.edu.au"
port = 2222
user = "z9999999"

[auth]
method = "key"
key_path = "~/.ssh/id_ed25519"

[sync]
exclude = [".git", "__pycache__"]
"""
    config_file = tmp_path / "config.toml"
    config_file.write_bytes(toml_content)

    with patch("cselab.config.CONFIG_FILE", config_file):
        from cselab.config import load_config
        cfg = load_config()

    assert cfg.host == "vlab.unsw.edu.au"
    assert cfg.port == 2222
    assert cfg.user == "z9999999"
    assert cfg.auth_method == "key"
    assert cfg.key_path == "~/.ssh/id_ed25519"
    assert cfg.exclude == [".git", "__pycache__"]


# ---------------------------------------------------------------------------
# load_config — missing file → sys.exit(1)
# ---------------------------------------------------------------------------

def test_load_config_missing_file(tmp_path):
    """Missing config file should sys.exit(1)."""
    missing = tmp_path / "nonexistent.toml"

    with patch("cselab.config.CONFIG_FILE", missing):
        from cselab.config import load_config
        with pytest.raises(SystemExit) as exc_info:
            load_config()
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# load_config — corrupted TOML → sys.exit(1)
# ---------------------------------------------------------------------------

def test_load_config_corrupted_toml(tmp_path):
    """Corrupted TOML should sys.exit(1) with a friendly message."""
    bad_file = tmp_path / "config.toml"
    bad_file.write_bytes(b"this is [[[not valid toml !!!")

    with patch("cselab.config.CONFIG_FILE", bad_file):
        from cselab.config import load_config
        with pytest.raises(SystemExit) as exc_info:
            load_config()
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# load_config — OSError on read → sys.exit(1)
# ---------------------------------------------------------------------------

def test_load_config_oserror_on_read(tmp_path):
    """OSError when reading the config file should sys.exit(1)."""
    config_file = tmp_path / "config.toml"
    config_file.write_bytes(b"[server]\nhost = 'x'\n")

    def boom(*a, **kw):
        raise OSError("disk on fire")

    with patch("cselab.config.CONFIG_FILE", config_file), \
         patch("builtins.open", boom):
        from cselab.config import load_config
        with pytest.raises(SystemExit) as exc_info:
            load_config()
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# load_config — missing tomllib → sys.exit(1)
# ---------------------------------------------------------------------------

def test_load_config_no_tomllib(tmp_path):
    """When tomllib is None, load_config should sys.exit(1)."""
    config_file = tmp_path / "config.toml"
    config_file.write_bytes(b"[server]\nhost='x'\n")

    with patch("cselab.config.CONFIG_FILE", config_file), \
         patch("cselab.config.tomllib", None):
        from cselab.config import load_config
        with pytest.raises(SystemExit) as exc_info:
            load_config()
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# load_config — partial TOML (missing sections) → defaults
# ---------------------------------------------------------------------------

def test_load_config_minimal_toml(tmp_path):
    """TOML with no sections should fall back to all defaults."""
    config_file = tmp_path / "config.toml"
    config_file.write_bytes(b"# empty config\n")

    with patch("cselab.config.CONFIG_FILE", config_file):
        from cselab.config import load_config
        cfg = load_config()

    assert cfg.host == "cse.unsw.edu.au"
    assert cfg.port == 22
    assert cfg.user == ""


# ---------------------------------------------------------------------------
# init_config
# ---------------------------------------------------------------------------

def test_init_config_creates_file(tmp_path):
    """init_config should create a config file with the given user/password."""
    config_dir = tmp_path / "cselab"
    config_file = config_dir / "config.toml"

    with patch("cselab.config.CONFIG_DIR", config_dir), \
         patch("cselab.config.CONFIG_FILE", config_file):
        from cselab.config import init_config
        path = init_config(user="z1234567", password="secret123")

    assert path == config_file
    content = config_file.read_text()
    assert "z1234567" in content
    assert 'password = "secret123"' in content


def test_init_config_write_failure(tmp_path):
    """OSError during write should sys.exit(1)."""
    config_dir = tmp_path / "cselab"
    config_file = config_dir / "config.toml"

    # Make config_dir a file so mkdir succeeds but write fails
    with patch("cselab.config.CONFIG_DIR", config_dir), \
         patch("cselab.config.CONFIG_FILE", config_file):
        # Patch write_text to raise
        with patch.object(Path, "write_text", side_effect=OSError("no space")):
            from cselab.config import init_config
            with pytest.raises(SystemExit) as exc_info:
                init_config(user="z1234567")
    assert exc_info.value.code == 1
