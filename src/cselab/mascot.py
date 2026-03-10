"""Mascot rendering — Zap the pixel bug, rendered as ANSI block art.

Works in ALL terminals with truecolor support. No image protocols needed.
Seasonal mascots: add grids to _SEASONAL dict or drop PNGs in ~/.config/cselab/mascots/.
"""

from datetime import date

# ── Colors ──
TEAL = (78, 201, 176)
WHITE = (255, 255, 255)
DARK = (20, 100, 85)
LIGHT = (180, 245, 230)
_ = None  # transparent

# ── Shorthand ──
T, W, D, L = TEAL, WHITE, DARK, LIGHT

# ── Zap pixel grid (10×8, compact with tail from 16×16 original) ──
# fmt: off
ZAP_DEFAULT = [
    [_, T, _, _, _, _, T, _, _, _],  # ears
    [_, T, T, T, T, T, T, _, _, _],  # head
    [_, W, D, T, W, D, T, _, _, _],  # eyes
    [_, L, D, T, L, D, T, _, _, _],  # eyes lower
    [T, T, T, T, T, T, T, T, _, _],  # body
    [_, T, T, T, T, T, T, _, T, _],  # body + tail ←
    [_, _, T, _, _, T, _, _, _, _],  # legs
    [_, _, _, _, _, _, _, _, _, _],  # empty
]
# fmt: on

# Future seasonal variants go here:
# ZAP_CHRISTMAS = [...]  # with red hat pixels
# ZAP_HALLOWEEN = [...]  # with orange pumpkin
_SEASONAL = {
    # "christmas": ZAP_CHRISTMAS,  # Dec 15-31
    # "halloween": ZAP_HALLOWEEN,  # Oct 25-31
}

_SEASON_DATES = [
    ("christmas",      12, 15, 12, 31),
    ("lunar-new-year",  1, 20,  2, 15),
    ("halloween",      10, 25, 10, 31),
]


def _current_season() -> str | None:
    today = date.today()
    m, d = today.month, today.day
    for name, ms, ds, me, de in _SEASON_DATES:
        if (m == ms and d >= ds) or (m == me and d <= de) or (ms < m < me):
            return name
    return None


def _get_grid() -> list[list]:
    """Get the current mascot grid (seasonal or default)."""
    season = _current_season()
    if season and season in _SEASONAL:
        return _SEASONAL[season]
    return ZAP_DEFAULT


def _rgb_fg(r, g, b): return f"\033[38;2;{r};{g};{b}m"
def _rgb_bg(r, g, b): return f"\033[48;2;{r};{g};{b}m"
_RST = "\033[0m"


def render_lines() -> list[str]:
    """Render mascot as ANSI half-block art lines.

    Returns list of strings, each 10 visible chars wide.
    Uses ▀▄ half-blocks with truecolor — works in any modern terminal.
    """
    grid = _get_grid()
    lines = []

    for row in range(0, len(grid), 2):
        line = ""
        bot_row = row + 1 if row + 1 < len(grid) else None
        for col in range(len(grid[row])):
            top = grid[row][col]
            bot = grid[bot_row][col] if bot_row is not None else None

            if top and bot:
                line += f"{_rgb_fg(*top)}{_rgb_bg(*bot)}▀{_RST}"
            elif top:
                line += f"{_rgb_fg(*top)}▀{_RST}"
            elif bot:
                line += f"{_rgb_fg(*bot)}▄{_RST}"
            else:
                line += " "
        lines.append(line)

    return lines


# Visible width of the mascot (for padding)
MASCOT_WIDTH = 10
