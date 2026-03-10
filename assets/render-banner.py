#!/usr/bin/env python3
"""Render the real cselab mascot banner for VHS demo."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from cselab.theme import GREEN, TEAL, DIM, BOLD, RESET
from cselab.mascot import render_lines, MASCOT_WIDTH

mascot = render_lines()
text = [
    f"{BOLD}cselab{RESET} v0.2.0",
    f"{DIM}z5502277@cse.unsw.edu.au{RESET}",
    f"{DIM}~/COMP1521/lab03{RESET}",
]

gap = "  "
print()
for i, art in enumerate(mascot):
    text_idx = i - 1
    if 0 <= text_idx < len(text):
        print(f"  {art}{gap}{text[text_idx]}")
    else:
        print(f"  {art}")
print()
