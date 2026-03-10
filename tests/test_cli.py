"""Tests for cselab.cli — subcommand handlers with mocked config/connection."""

import subprocess
import sys
from argparse import Namespace
from unittest.mock import patch, MagicMock

import pytest

from cselab.config import Config


def _cfg(**overrides) -> Config:
    defaults = dict(
        host="cse.unsw.edu.au",
        port=22,
        user="z0000000",
        auth_method="password",
        password="pw",
    )
    defaults.update(overrides)
    return Config(**defaults)


# ---------------------------------------------------------------------------
# cmd_run — connect timeout → sys.exit
# ---------------------------------------------------------------------------

def test_cmd_run_connect_timeout():
    """cmd_run should sys.exit(1) when connect raises TimeoutExpired."""
    from cselab.cli import cmd_run

    args = Namespace(command=["echo", "hi"], no_sync=False)

    with patch("cselab.cli.load_config", return_value=_cfg()), \
         patch("cselab.connection.is_connected", return_value=False), \
         patch("cselab.connection.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=30)), \
         patch("cselab.connection._askpass_env", return_value=({}, "")), \
         patch("os.path.exists", return_value=False):
        with pytest.raises(SystemExit) as exc_info:
            cmd_run(args)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# cmd_run — rsync_up timeout → sys.exit
# ---------------------------------------------------------------------------

def test_cmd_run_rsync_timeout():
    """cmd_run should sys.exit(1) when rsync_up times out."""
    from cselab.cli import cmd_run

    args = Namespace(command=["make"], no_sync=False)

    call_count = [0]

    def mock_connect(cfg):
        return True

    def mock_rsync_up(cfg, local, remote, **kw):
        raise subprocess.TimeoutExpired(cmd="rsync", timeout=30)

    with patch("cselab.cli.load_config", return_value=_cfg()), \
         patch("cselab.connection.connect", mock_connect), \
         patch("cselab.cli.cmd_run.__module__", "cselab.cli"):
        # Patch at the cli module level since cmd_run imports lazily
        with patch("cselab.connection.connect", return_value=True), \
             patch("cselab.connection.is_connected", return_value=True), \
             patch("cselab.connection.rsync_up", side_effect=subprocess.TimeoutExpired(cmd="rsync", timeout=30)):
            # cmd_run does lazy import, so we need to patch where it's used
            with patch.dict("sys.modules", {}):
                pass
            # Simpler approach: just patch subprocess.run
            pass

    # Use a cleaner approach — patch the lazy imports inside cmd_run
    with patch("cselab.cli.load_config", return_value=_cfg()):
        # cmd_run does: from cselab.connection import connect, rsync_up, ssh_exec
        mock_connect = MagicMock(return_value=True)
        mock_rsync = MagicMock(side_effect=subprocess.TimeoutExpired(cmd="rsync", timeout=30))

        with patch.dict("sys.modules"):
            import cselab.connection as conn_mod
            with patch.object(conn_mod, "connect", mock_connect), \
                 patch.object(conn_mod, "rsync_up", mock_rsync):
                with pytest.raises(SystemExit) as exc_info:
                    cmd_run(args)
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# cmd_sync — connect failure → sys.exit
# ---------------------------------------------------------------------------

def test_cmd_sync_connect_failure():
    """cmd_sync should sys.exit(1) when connect returns False."""
    from cselab.cli import cmd_sync

    args = Namespace()

    import cselab.connection as conn_mod
    with patch("cselab.cli.load_config", return_value=_cfg()), \
         patch.object(conn_mod, "connect", return_value=False):
        with pytest.raises(SystemExit) as exc_info:
            cmd_sync(args)
    assert exc_info.value.code == 1


def test_cmd_sync_connect_timeout():
    """cmd_sync should sys.exit(1) on connect TimeoutExpired."""
    from cselab.cli import cmd_sync

    args = Namespace()

    import cselab.connection as conn_mod
    with patch("cselab.cli.load_config", return_value=_cfg()), \
         patch.object(conn_mod, "connect",
                      side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=30)):
        with pytest.raises(SystemExit) as exc_info:
            cmd_sync(args)
    assert exc_info.value.code == 1


def test_cmd_sync_rsync_timeout():
    """cmd_sync should sys.exit(1) when rsync_up times out."""
    from cselab.cli import cmd_sync

    args = Namespace()

    import cselab.connection as conn_mod
    with patch("cselab.cli.load_config", return_value=_cfg()), \
         patch.object(conn_mod, "connect", return_value=True), \
         patch.object(conn_mod, "rsync_up",
                      side_effect=subprocess.TimeoutExpired(cmd="rsync", timeout=30)):
        with pytest.raises(SystemExit) as exc_info:
            cmd_sync(args)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# cmd_pull
# ---------------------------------------------------------------------------

def test_cmd_pull_connect_timeout():
    """cmd_pull should sys.exit(1) on connect timeout."""
    from cselab.cli import cmd_pull

    args = Namespace(dest=None)

    import cselab.connection as conn_mod
    with patch("cselab.cli.load_config", return_value=_cfg()), \
         patch.object(conn_mod, "connect",
                      side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=30)):
        with pytest.raises(SystemExit) as exc_info:
            cmd_pull(args)
    assert exc_info.value.code == 1


def test_cmd_pull_rsync_down_timeout():
    """cmd_pull should sys.exit(1) when rsync_down times out."""
    from cselab.cli import cmd_pull

    args = Namespace(dest=None)

    import cselab.connection as conn_mod
    with patch("cselab.cli.load_config", return_value=_cfg()), \
         patch.object(conn_mod, "connect", return_value=True), \
         patch.object(conn_mod, "rsync_down",
                      side_effect=subprocess.TimeoutExpired(cmd="rsync", timeout=30)):
        with pytest.raises(SystemExit) as exc_info:
            cmd_pull(args)
    assert exc_info.value.code == 1


def test_cmd_pull_rsync_down_failure():
    """cmd_pull should sys.exit(1) when rsync_down returns False."""
    from cselab.cli import cmd_pull

    args = Namespace(dest=None)

    import cselab.connection as conn_mod
    with patch("cselab.cli.load_config", return_value=_cfg()), \
         patch.object(conn_mod, "connect", return_value=True), \
         patch.object(conn_mod, "rsync_down", return_value=False):
        with pytest.raises(SystemExit) as exc_info:
            cmd_pull(args)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# cmd_ssh — connect timeout
# ---------------------------------------------------------------------------

def test_cmd_ssh_connect_timeout():
    """cmd_ssh should sys.exit(1) on connect timeout."""
    from cselab.cli import cmd_ssh

    args = Namespace()

    import cselab.connection as conn_mod
    with patch("cselab.cli.load_config", return_value=_cfg()), \
         patch.object(conn_mod, "connect",
                      side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=30)):
        with pytest.raises(SystemExit) as exc_info:
            cmd_ssh(args)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# cmd_clean — connect timeout
# ---------------------------------------------------------------------------

def test_cmd_clean_connect_timeout():
    """cmd_clean should sys.exit(1) on connect timeout."""
    from cselab.cli import cmd_clean

    args = Namespace()

    import cselab.connection as conn_mod
    with patch("cselab.cli.load_config", return_value=_cfg()), \
         patch.object(conn_mod, "connect",
                      side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=30)):
        with pytest.raises(SystemExit) as exc_info:
            cmd_clean(args)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# cmd_disconnect — doesn't crash
# ---------------------------------------------------------------------------

def test_cmd_disconnect_graceful():
    """cmd_disconnect should complete without raising."""
    from cselab.cli import cmd_disconnect

    args = Namespace()

    import cselab.connection as conn_mod
    with patch("cselab.cli.load_config", return_value=_cfg()), \
         patch.object(conn_mod, "disconnect"):
        cmd_disconnect(args)  # should not raise


# ---------------------------------------------------------------------------
# cmd_config — shows path
# ---------------------------------------------------------------------------

def test_cmd_config_shows_path(capsys, tmp_path):
    """cmd_config should print config file path."""
    from cselab.cli import cmd_config

    config_file = tmp_path / "config.toml"
    config_file.write_text("[server]\nhost = 'test'\n")

    args = Namespace()

    # cmd_config does: from cselab.config import CONFIG_FILE
    # so we patch at the source module
    import cselab.config as config_mod
    with patch.object(config_mod, "CONFIG_FILE", config_file):
        cmd_config(args)

    captured = capsys.readouterr()
    assert str(config_file) in captured.out


# ---------------------------------------------------------------------------
# Phase 2: no hardcoded ANSI in watch functions
# ---------------------------------------------------------------------------

def test_watch_functions_use_theme_constants():
    """_watch_fswatch and _watch_poll should not contain hardcoded ANSI codes."""
    import inspect
    from cselab.cli import _watch_fswatch, _watch_poll

    for fn in (_watch_fswatch, _watch_poll):
        source = inspect.getsource(fn)
        # Should not have raw \033[ escape codes
        assert "\\033[" not in source, (
            f"{fn.__name__} still has hardcoded ANSI escape codes"
        )
        # Should reference theme constants instead
        assert "TEAL" in source or "RESET" in source, (
            f"{fn.__name__} should use theme constants"
        )
