"""Tests for cselab.connection — SSH/rsync transport with timeout handling."""

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from cselab.config import Config


def _cfg(**overrides) -> Config:
    """Create a Config with sensible test defaults."""
    defaults = dict(
        host="cse.unsw.edu.au",
        port=22,
        user="z0000000",
        auth_method="password",
        password="testpass",
    )
    defaults.update(overrides)
    return Config(**defaults)


# ---------------------------------------------------------------------------
# is_connected
# ---------------------------------------------------------------------------

def test_is_connected_returns_true_on_success():
    from cselab.connection import is_connected

    mock_result = MagicMock(returncode=0)
    with patch("cselab.connection.subprocess.run", return_value=mock_result):
        assert is_connected(_cfg()) is True


def test_is_connected_returns_false_on_failure():
    from cselab.connection import is_connected

    mock_result = MagicMock(returncode=1)
    with patch("cselab.connection.subprocess.run", return_value=mock_result):
        assert is_connected(_cfg()) is False


def test_is_connected_returns_false_on_timeout():
    from cselab.connection import is_connected

    with patch("cselab.connection.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=5)):
        assert is_connected(_cfg()) is False


def test_is_connected_returns_false_on_file_not_found():
    from cselab.connection import is_connected

    with patch("cselab.connection.subprocess.run",
               side_effect=FileNotFoundError("ssh not found")):
        assert is_connected(_cfg()) is False


# ---------------------------------------------------------------------------
# connect — password branch
# ---------------------------------------------------------------------------

def test_connect_returns_false_on_timeout_password():
    """connect() with password auth should return False when subprocess times out."""
    from cselab.connection import connect

    cfg = _cfg(auth_method="password", password="pw")

    with patch("cselab.connection.is_connected", return_value=False), \
         patch("cselab.connection.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=30)), \
         patch("cselab.connection._askpass_env", return_value=({}, "/tmp/fake_askpass")), \
         patch("os.path.exists", return_value=False):
        result = connect(cfg)

    assert result is False


def test_connect_returns_false_on_nonzero_exit():
    """connect() should return False and print error when SSH returns non-zero."""
    from cselab.connection import connect

    cfg = _cfg(auth_method="password", password="pw")
    mock_result = MagicMock(returncode=255, stderr=b"Permission denied")

    with patch("cselab.connection.is_connected", return_value=False), \
         patch("cselab.connection.subprocess.run", return_value=mock_result), \
         patch("cselab.connection._askpass_env", return_value=({}, "/tmp/fake_askpass")), \
         patch("os.path.exists", return_value=False):
        result = connect(cfg)

    assert result is False


# ---------------------------------------------------------------------------
# connect — key branch
# ---------------------------------------------------------------------------

def test_connect_returns_false_on_timeout_key():
    """connect() with key auth should return False on timeout."""
    from cselab.connection import connect

    cfg = _cfg(auth_method="key", key_path="~/.ssh/id_rsa", password=None)

    with patch("cselab.connection.is_connected", return_value=False), \
         patch("cselab.connection.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=30)):
        result = connect(cfg)

    assert result is False


def test_connect_already_connected():
    """connect() should return True immediately if already connected."""
    from cselab.connection import connect

    with patch("cselab.connection.is_connected", return_value=True):
        assert connect(_cfg()) is True


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------

def test_disconnect_no_crash_on_timeout():
    """disconnect() should not raise when subprocess times out."""
    from cselab.connection import disconnect

    with patch("cselab.connection.is_connected", return_value=True), \
         patch("cselab.connection.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=10)):
        # Should not raise
        disconnect(_cfg())


def test_disconnect_skips_when_not_connected():
    """disconnect() should do nothing when not connected."""
    from cselab.connection import disconnect

    with patch("cselab.connection.is_connected", return_value=False) as mock_check, \
         patch("cselab.connection.subprocess.run") as mock_run:
        disconnect(_cfg())
        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# rsync_up
# ---------------------------------------------------------------------------

def test_rsync_up_returns_false_on_mkdir_timeout():
    """rsync_up should return False if the remote mkdir times out."""
    from cselab.connection import rsync_up

    with patch("cselab.connection.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=10)):
        result = rsync_up(_cfg(), "/tmp/local", "/tmp/remote", timeout=30)

    assert result is False


def test_rsync_up_returns_false_on_rsync_timeout():
    """rsync_up should return False if rsync itself times out."""
    from cselab.connection import rsync_up

    call_count = [0]

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            # mkdir succeeds
            return MagicMock(returncode=0)
        # rsync times out
        raise subprocess.TimeoutExpired(cmd="rsync", timeout=30)

    with patch("cselab.connection.subprocess.run", side_effect=side_effect):
        result = rsync_up(_cfg(), "/tmp/local", "/tmp/remote", timeout=30)

    assert result is False


def test_rsync_up_returns_true_on_success():
    """rsync_up should return True when both mkdir and rsync succeed."""
    from cselab.connection import rsync_up

    call_count = [0]

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        return MagicMock(returncode=0)

    with patch("cselab.connection.subprocess.run", side_effect=side_effect):
        result = rsync_up(_cfg(), "/tmp/local", "/tmp/remote", timeout=30)

    assert result is True


def test_rsync_up_returns_false_on_nonzero():
    """rsync_up should return False when rsync returns non-zero."""
    from cselab.connection import rsync_up

    call_count = [0]

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return MagicMock(returncode=0)  # mkdir
        return MagicMock(returncode=23)  # rsync partial transfer

    with patch("cselab.connection.subprocess.run", side_effect=side_effect):
        result = rsync_up(_cfg(), "/tmp/local", "/tmp/remote", timeout=30)

    assert result is False


# ---------------------------------------------------------------------------
# rsync_down
# ---------------------------------------------------------------------------

def test_rsync_down_returns_false_on_timeout():
    """rsync_down should return False on timeout."""
    from cselab.connection import rsync_down

    with patch("cselab.connection.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="rsync", timeout=30)):
        result = rsync_down(_cfg(), "/tmp/remote", "/tmp/local", timeout=30)

    assert result is False


def test_rsync_down_returns_true_on_success():
    """rsync_down should return True on success."""
    from cselab.connection import rsync_down

    with patch("cselab.connection.subprocess.run",
               return_value=MagicMock(returncode=0)):
        result = rsync_down(_cfg(), "/tmp/remote", "/tmp/local", timeout=30)

    assert result is True


def test_rsync_down_returns_false_on_nonzero():
    """rsync_down should return False on non-zero rsync exit."""
    from cselab.connection import rsync_down

    with patch("cselab.connection.subprocess.run",
               return_value=MagicMock(returncode=12)):
        result = rsync_down(_cfg(), "/tmp/remote", "/tmp/local", timeout=30)

    assert result is False


# ---------------------------------------------------------------------------
# _translate_ssh_error
# ---------------------------------------------------------------------------

def test_translate_ssh_error_permission_denied():
    from cselab.connection import _translate_ssh_error
    assert "password" in _translate_ssh_error("Permission denied").lower() or \
           "Wrong" in _translate_ssh_error("Permission denied")


def test_translate_ssh_error_connection_refused():
    from cselab.connection import _translate_ssh_error
    msg = _translate_ssh_error("Connection refused")
    assert "down" in msg.lower() or "refused" in msg.lower()


def test_translate_ssh_error_timeout():
    from cselab.connection import _translate_ssh_error
    msg = _translate_ssh_error("Connection timed out")
    assert "timed out" in msg.lower()


def test_translate_ssh_error_empty():
    from cselab.connection import _translate_ssh_error
    msg = _translate_ssh_error("")
    assert "failed" in msg.lower()


def test_translate_ssh_error_unknown():
    from cselab.connection import _translate_ssh_error
    msg = _translate_ssh_error("Some weird error xyz")
    assert "SSH error" in msg or "weird" in msg.lower()


# ---------------------------------------------------------------------------
# _make_askpass
# ---------------------------------------------------------------------------

def test_make_askpass_returns_empty_on_oserror():
    """_make_askpass should return empty string on OSError."""
    from cselab.connection import _make_askpass

    with patch("cselab.connection.tempfile.mkstemp", side_effect=OSError("no tmp")):
        result = _make_askpass("password123")

    assert result == ""


# ---------------------------------------------------------------------------
# _ssh_base_args / _auth_args
# ---------------------------------------------------------------------------

def test_ssh_base_args_contains_control_path():
    from cselab.connection import _ssh_base_args

    cfg = _cfg()
    args = _ssh_base_args(cfg)
    # Should contain ControlPath with socket path
    assert any("ControlPath" in str(a) for a in args)
    assert any(str(cfg.port) in str(a) for a in args)


def test_auth_args_key_method():
    from cselab.connection import _auth_args

    cfg = _cfg(auth_method="key", key_path="~/.ssh/id_ed25519")
    args = _auth_args(cfg)
    assert "-i" in args


def test_auth_args_password_method():
    from cselab.connection import _auth_args

    cfg = _cfg(auth_method="password")
    args = _auth_args(cfg)
    assert args == []
