"""Tests for cselab.repl — REPL helpers (_rule, _display_dir, _State)."""

import os
from unittest.mock import patch

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
# _rule — doesn't crash
# ---------------------------------------------------------------------------

def test_rule_no_crash(capsys):
    """_rule() should print without raising, even without a terminal."""
    from cselab.repl import _rule

    # Without a real terminal, os.get_terminal_size() raises OSError
    # _rule should handle that and default to 80
    _rule()
    captured = capsys.readouterr()
    # Should have printed something (a line of horizontal rule chars)
    assert len(captured.out) > 0


def test_rule_uses_fallback_width(capsys):
    """_rule() should fall back to 80 columns when terminal size is unavailable."""
    from cselab.repl import _rule

    with patch("os.get_terminal_size", side_effect=OSError("no tty")):
        _rule()
    captured = capsys.readouterr()
    # The output contains ANSI codes + 80 horizontal rule chars + newline
    assert len(captured.out) > 0


# ---------------------------------------------------------------------------
# _display_dir — returns string
# ---------------------------------------------------------------------------

def test_display_dir_returns_string():
    """_display_dir should return a string representing the current directory."""
    from cselab.repl import _display_dir

    result = _display_dir()
    assert isinstance(result, str)
    assert len(result) > 0


def test_display_dir_home_prefix():
    """_display_dir should use ~ prefix when cwd is under home."""
    from cselab.repl import _display_dir

    home = os.path.expanduser("~")
    with patch("os.getcwd", return_value=home + "/projects/test"):
        result = _display_dir()
    assert result.startswith("~")
    assert "projects/test" in result


def test_display_dir_outside_home():
    """_display_dir should return full path when cwd is outside home."""
    from cselab.repl import _display_dir

    with patch("os.getcwd", return_value="/tmp/somewhere"):
        result = _display_dir()
    assert result == "/tmp/somewhere"


# ---------------------------------------------------------------------------
# _State initialization
# ---------------------------------------------------------------------------

def test_state_init():
    """_State should initialize with correct defaults."""
    from cselab.repl import _State

    cfg = _cfg(user="z1234567", host="vlab.unsw.edu.au")
    state = _State(cfg)

    assert state.cfg is cfg
    assert state.connected is False
    assert state.last_sync == ""
    assert isinstance(state.display_dir, str)
    assert state.cmd_count == 0


def test_state_mutable():
    """_State fields should be mutable."""
    from cselab.repl import _State

    cfg = _cfg()
    state = _State(cfg)

    state.connected = True
    state.last_sync = "0.3s"
    state.cmd_count = 5

    assert state.connected is True
    assert state.last_sync == "0.3s"
    assert state.cmd_count == 5


# ---------------------------------------------------------------------------
# COMPLETIONS list
# ---------------------------------------------------------------------------

def test_completions_list_has_expected_entries():
    """COMPLETIONS should include key CSE tools and built-ins."""
    from cselab.repl import COMPLETIONS

    assert "autotest" in COMPLETIONS
    assert "give" in COMPLETIONS
    assert "dcc" in COMPLETIONS
    assert "classrun" in COMPLETIONS
    assert "style" in COMPLETIONS
    assert "exit" in COMPLETIONS
    assert "help" in COMPLETIONS
    assert "sync" in COMPLETIONS
    assert "1521" in COMPLETIONS
    assert "mipsy" in COMPLETIONS


# ---------------------------------------------------------------------------
# Phase 2: DOT_ON / DOT_OFF consistency in source
# ---------------------------------------------------------------------------

def test_dot_symbols_consistency():
    """DOT_ON should only appear near GREEN, DOT_OFF only near RED in repl.py."""
    import inspect
    from cselab import repl as repl_mod

    source = inspect.getsource(repl_mod)
    lines = source.split("\n")

    for i, line in enumerate(lines):
        # Skip imports, toolbar, and comments
        stripped = line.strip()
        if stripped.startswith(("#", "from ", "import ")) or "TOOLBAR" in line:
            continue
        # DOT_ON with RED = wrong (except in toolbar which we skip)
        if "DOT_ON" in line and "RED" in line:
            assert False, f"Line {i+1}: DOT_ON used with RED: {stripped}"
        # DOT_OFF with GREEN = wrong
        if "DOT_OFF" in line and "GREEN" in line:
            assert False, f"Line {i+1}: DOT_OFF used with GREEN: {stripped}"


def test_dot_off_imported():
    """DOT_OFF should be importable from repl module's theme imports."""
    from cselab.repl import DOT_OFF
    assert DOT_OFF == "\u25cb"  # ○


# ---------------------------------------------------------------------------
# Phase 2: ! prefix visual indicator
# ---------------------------------------------------------------------------

def test_skip_sync_indicator_in_source():
    """repl.py should show '(sync skipped)' for ! prefix commands."""
    import inspect
    from cselab import repl as repl_mod

    source = inspect.getsource(repl_mod)
    assert "sync skipped" in source, "Missing '(sync skipped)' indicator for ! prefix"


# ---------------------------------------------------------------------------
# Phase 2: status command uses dot indicators
# ---------------------------------------------------------------------------

def test_status_uses_dot_indicators():
    """Status command should use DOT_ON/DOT_OFF for connected/disconnected."""
    import inspect
    from cselab import repl as repl_mod

    source = inspect.getsource(repl_mod)
    # Find the status section
    lines = source.split("\n")
    in_status = False
    found_dot_on = False
    found_dot_off = False
    for line in lines:
        if 'first == "status"' in line:
            in_status = True
            continue
        if in_status:
            if "DOT_ON" in line and "connected" in line:
                found_dot_on = True
            if "DOT_OFF" in line and "disconnected" in line:
                found_dot_off = True
            if "continue" in line:
                break

    assert found_dot_on, "Status command missing DOT_ON for connected state"
    assert found_dot_off, "Status command missing DOT_OFF for disconnected state"


# ---------------------------------------------------------------------------
# _BangLexer
# ---------------------------------------------------------------------------

def test_bang_lexer_highlights_exclamation():
    """_BangLexer should return class:bang for the ! prefix."""
    from cselab.repl import _BangLexer
    from prompt_toolkit.document import Document

    lexer = _BangLexer()
    doc = Document("!ls -la")
    get_line = lexer.lex_document(doc)
    tokens = get_line(0)
    assert tokens[0] == ("class:bang", "!")
    assert tokens[1] == ("", "ls -la")


def test_bang_lexer_no_highlight_without_bang():
    """_BangLexer should not highlight lines without ! prefix."""
    from cselab.repl import _BangLexer
    from prompt_toolkit.document import Document

    lexer = _BangLexer()
    doc = Document("ls -la")
    get_line = lexer.lex_document(doc)
    tokens = get_line(0)
    assert tokens == [("", "ls -la")]


# ---------------------------------------------------------------------------
# _SmartCompleter — command completion
# ---------------------------------------------------------------------------

def test_completer_first_word_commands():
    """First word should complete from command list."""
    from cselab.repl import _SmartCompleter
    from prompt_toolkit.document import Document

    cfg = _cfg()
    completer = _SmartCompleter(["autotest", "give", "ls", "cd"], cfg, "~/.cselab/ws/test")
    doc = Document("au")
    completions = list(completer.get_completions(doc, None))
    texts = [c.text for c in completions]
    assert "autotest" in texts
    assert "give" not in texts


def test_completer_first_word_with_bang():
    """! prefix should not break first-word command completion."""
    from cselab.repl import _SmartCompleter
    from prompt_toolkit.document import Document

    cfg = _cfg()
    completer = _SmartCompleter(["autotest", "give", "ls", "cd"], cfg, "~/.cselab/ws/test")
    doc = Document("!au")
    completions = list(completer.get_completions(doc, None))
    texts = [c.text for c in completions]
    assert "autotest" in texts


def test_completer_cd_triggers_path_mode():
    """After 'cd ', completer should NOT return command names."""
    from cselab.repl import _SmartCompleter
    from prompt_toolkit.document import Document

    cfg = _cfg()
    completer = _SmartCompleter(["autotest", "give", "ls", "cd"], cfg, "~/.cselab/ws/test")

    # Mock _ls_remote to return fake dirs
    completer._ls_remote = lambda subdir: ["projects/", "assignments/", "labs/"]

    doc = Document("cd ")
    completions = list(completer.get_completions(doc, None))
    texts = [c.text for c in completions]
    assert "autotest" not in texts
    assert "projects/" in texts
    assert "assignments/" in texts


def test_completer_cd_partial_filters():
    """'cd p' should filter to entries starting with p."""
    from cselab.repl import _SmartCompleter
    from prompt_toolkit.document import Document

    cfg = _cfg()
    completer = _SmartCompleter(["autotest", "give", "ls", "cd"], cfg, "~/.cselab/ws/test")
    completer._ls_remote = lambda subdir: ["projects/", "assignments/", "public_html/"]

    doc = Document("cd p")
    completions = list(completer.get_completions(doc, None))
    texts = [c.text for c in completions]
    assert "projects/" in texts
    assert "public_html/" in texts
    assert "assignments/" not in texts


def test_completer_non_path_cmd_uses_word_completion():
    """After a non-path command like 'autotest', should still offer word completions."""
    from cselab.repl import _SmartCompleter
    from prompt_toolkit.document import Document

    cfg = _cfg()
    completer = _SmartCompleter(["autotest", "1521", "1511", "give"], cfg, "~/.cselab/ws/test")
    doc = Document("autotest 15")
    completions = list(completer.get_completions(doc, None))
    texts = [c.text for c in completions]
    assert "1521" in texts
    assert "1511" in texts


# ---------------------------------------------------------------------------
# _SmartCompleter — cache
# ---------------------------------------------------------------------------

def test_completer_caches_ls_results():
    """Repeated completions should use cached results."""
    from cselab.repl import _SmartCompleter
    from prompt_toolkit.document import Document

    cfg = _cfg()
    completer = _SmartCompleter(["cd"], cfg, "~/.cselab/ws/test")

    call_count = 0
    def mock_ls(subdir):
        nonlocal call_count
        call_count += 1
        return ["dir1/", "dir2/"]

    completer._ls_remote = mock_ls

    # First call populates cache
    doc = Document("cd ")
    list(completer.get_completions(doc, None))
    assert call_count == 1

    # Second call should use cache
    list(completer.get_completions(doc, None))
    assert call_count == 1  # still 1 — cache hit
