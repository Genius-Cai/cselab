"""Welcome banner — Zap mascot + text, side by side, like Claude Code."""

import os

from cselab.theme import GREEN, TEAL, DIM, BOLD, RESET
from cselab.mascot import render_lines, MASCOT_WIDTH


def print_init_banner() -> None:
    """Print small banner for init/setup flow — Zap + 'cselab setup'."""
    mascot = render_lines()
    text = [f"{BOLD}{TEAL}cselab{RESET} {DIM}setup{RESET}"]
    gap = "  "

    print()
    for i, art in enumerate(mascot):
        text_idx = i - 1
        if 0 <= text_idx < len(text):
            print(f"  {art}{gap}{text[text_idx]}")
        else:
            print(f"  {art}")
    print()


def print_banner(version: str, user: str, host: str) -> None:
    """Print banner with mascot on left, info on right.

      ▄▄    ▄▄
      ██████████      cselab v0.2.0
      ░█░██░█░██      z5555555@cse.unsw.edu.au
     ████████████     ~/COMP1521/lab01
       ▀  ▀
    """
    try:
        cwd = os.getcwd()
    except OSError:
        cwd = "."
    home = os.path.expanduser("~")
    display_dir = "~" + cwd[len(home):] if cwd.startswith(home) else cwd

    mascot = render_lines()
    text = [
        f"{BOLD}cselab{RESET} v{version}",
        f"{DIM}{user}@{host}{RESET}",
        f"{DIM}{display_dir}{RESET}",
    ]

    # Align: mascot has 4 rows, text has 3 rows
    # Text starts at mascot row 1 (skip the ears row)
    gap = "  "
    pad = " " * MASCOT_WIDTH

    print()
    for i, art in enumerate(mascot):
        text_idx = i - 1  # offset: text starts one row below mascot top
        if 0 <= text_idx < len(text):
            print(f"  {art}{gap}{text[text_idx]}")
        else:
            print(f"  {art}")
    print()
