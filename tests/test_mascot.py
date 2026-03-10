"""Tests for cselab.mascot — Zap pixel art rendering and seasonal logic."""

import re
from datetime import date
from unittest.mock import patch

from cselab.mascot import (
    render_lines,
    MASCOT_WIDTH,
    _current_season,
    _get_grid,
    ZAP_DEFAULT,
)


# ---------------------------------------------------------------------------
# render_lines — line count
# ---------------------------------------------------------------------------

def test_render_lines_returns_4_lines():
    """8-row grid with half-block rendering should produce 4 lines."""
    lines = render_lines()
    assert len(lines) == 4


# ---------------------------------------------------------------------------
# render_lines — visible width
# ---------------------------------------------------------------------------

def test_render_lines_visible_width():
    """Each rendered line should have a visible width of MASCOT_WIDTH (10) chars.

    Visible width means stripping ANSI escape sequences and counting printable chars.
    """
    lines = render_lines()
    # Strip ANSI escape codes: \033[...m
    ansi_pattern = re.compile(r"\033\[[0-9;]*m")

    for i, line in enumerate(lines):
        visible = ansi_pattern.sub("", line)
        assert len(visible) == MASCOT_WIDTH, (
            f"Line {i} visible width is {len(visible)}, expected {MASCOT_WIDTH}. "
            f"Visible content: {repr(visible)}"
        )


def test_render_lines_are_strings():
    """render_lines should return a list of strings."""
    lines = render_lines()
    assert isinstance(lines, list)
    for line in lines:
        assert isinstance(line, str)


# ---------------------------------------------------------------------------
# _current_season — returns None or valid string
# ---------------------------------------------------------------------------

def test_current_season_returns_none_or_string():
    """_current_season should return None or a known season string."""
    result = _current_season()
    valid = {None, "christmas", "lunar-new-year", "halloween"}
    assert result in valid


def test_current_season_christmas():
    """December 25 should return 'christmas'."""
    with patch("cselab.mascot.date") as mock_date:
        mock_date.today.return_value = date(2025, 12, 25)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        result = _current_season()
    assert result == "christmas"


def test_current_season_halloween():
    """October 31 should return 'halloween'."""
    with patch("cselab.mascot.date") as mock_date:
        mock_date.today.return_value = date(2025, 10, 31)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        result = _current_season()
    assert result == "halloween"


def test_current_season_normal_day():
    """A regular day (e.g. March 10) should return None."""
    with patch("cselab.mascot.date") as mock_date:
        mock_date.today.return_value = date(2026, 3, 10)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        result = _current_season()
    assert result is None


def test_current_season_lunar_new_year():
    """February 1 should return 'lunar-new-year'."""
    with patch("cselab.mascot.date") as mock_date:
        mock_date.today.return_value = date(2025, 2, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        result = _current_season()
    assert result == "lunar-new-year"


# ---------------------------------------------------------------------------
# _get_grid — returns list of lists
# ---------------------------------------------------------------------------

def test_get_grid_returns_list_of_lists():
    """_get_grid should return a 2D list (list of row-lists)."""
    grid = _get_grid()
    assert isinstance(grid, list)
    assert len(grid) > 0
    for row in grid:
        assert isinstance(row, list)


def test_get_grid_default_is_zap():
    """Without seasonal override, _get_grid should return ZAP_DEFAULT."""
    # On a normal day (not Christmas/Halloween/Lunar New Year)
    with patch("cselab.mascot._current_season", return_value=None):
        grid = _get_grid()
    assert grid is ZAP_DEFAULT


def test_get_grid_dimensions():
    """Default grid should be 8 rows x 10 columns."""
    grid = _get_grid()
    assert len(grid) == 8
    for row in grid:
        assert len(row) == 10


# ---------------------------------------------------------------------------
# ZAP_DEFAULT structure
# ---------------------------------------------------------------------------

def test_zap_default_pixel_types():
    """Each pixel should be None (transparent) or an RGB tuple of 3 ints."""
    for row in ZAP_DEFAULT:
        for pixel in row:
            if pixel is not None:
                assert isinstance(pixel, tuple), f"Expected tuple, got {type(pixel)}"
                assert len(pixel) == 3, f"Expected 3-tuple, got {len(pixel)}"
                assert all(0 <= v <= 255 for v in pixel), f"RGB out of range: {pixel}"


# ---------------------------------------------------------------------------
# MASCOT_WIDTH constant
# ---------------------------------------------------------------------------

def test_mascot_width_is_10():
    """MASCOT_WIDTH should be 10."""
    assert MASCOT_WIDTH == 10
