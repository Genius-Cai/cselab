"""cselab brand theme — centralized colors, styles, and visual constants.

Single source of truth for all visual decisions. Every module imports from here.
"""

# ── Brand ──
BRAND_NAME = "cselab"
BRAND_TAGLINE = "Run CSE commands locally"

# ── ANSI Colors (for print output, not prompt_toolkit) ──
# Primary: Teal — matches mascot Zap
TEAL = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
DIM = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"

# ── prompt_toolkit Hex Colors ──
# Toolbar
TOOLBAR_BG = "#1a1a2e"
TOOLBAR_FG = "#8888aa"
TOOLBAR_ACCENT = "#4ecdc4"       # teal — connected dot, highlights
TOOLBAR_DANGER = "#ff6b6b"       # soft red — disconnected
TOOLBAR_DIM = "#666688"          # sync time, secondary info
# Prompt
PROMPT_STYLE = "ansigreen bold"

# ── Box Drawing (rounded corners — Ink's borderStyle: "round") ──
TL = "\u256d"  # ╭
TR = "\u256e"  # ╮
BL = "\u2570"  # ╰
BR = "\u256f"  # ╯
H = "\u2500"   # ─
V = "\u2502"   # │

# ── Status Indicators ──
DOT_ON = "\u25cf"   # ● connected
DOT_OFF = "\u25cb"  # ○ disconnected

# ── Separator ──
SEP = "=" * 40
