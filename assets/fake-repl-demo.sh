#!/bin/bash
# Complete REPL demo — simulates typing, output, everything
# The tape just runs this script. No Hide/Show, no PS1 tricks.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

RST="\033[0m"
BOLD="\033[1m"
DIM="\033[90m"
GREEN="\033[32m"
MAGENTA="\033[35m"

# Simulate typing character by character
type_text() {
    local text="$1"
    local delay="${2:-0.06}"
    for (( i=0; i<${#text}; i++ )); do
        printf '%s' "${text:$i:1}"
        sleep "$delay"
    done
}

# Green bold prompt
prompt() {
    printf "${GREEN}${BOLD}> ${RST}"
}

# Dim separator line
sep() {
    printf "${DIM}"
    printf '─%.0s' {1..55}
    printf "${RST}\n"
}

# ── Clear screen ──
printf '\033[2J\033[H'
sleep 0.5

# ═══════════════════════════════════════════
# Scene 1: User types "cselab" → startup
# ═══════════════════════════════════════════
printf "$ "
type_text "cselab" 0.07
sleep 0.5
printf "\n\n"

# Connection
printf "  ${DIM}Connecting to cse.unsw.edu.au...${RST} "
sleep 0.8
printf "${GREEN}ok${RST}\n"

# Banner with real mascot
python3 "$SCRIPT_DIR/render-banner.py"

# First-time examples
echo -e "  ${DIM}Examples:${RST}"
echo -e "    1521 autotest lab03   ${DIM}run autotest${RST}"
echo -e "    give cs1521 lab03 *.c ${DIM}submit files${RST}"
echo -e "    dcc prog.c -o prog    ${DIM}compile C${RST}"
echo -e "  ${DIM}Start typing for suggestions.${RST} help ${DIM}for more.${RST}"
sep

sleep 1

# ═══════════════════════════════════════════
# Scene 2: Tab completion → run autotest
# ═══════════════════════════════════════════
prompt

# Type "15" then fast-complete to "1521 "
type_text "15" 0.08
sleep 0.5
type_text "21 " 0.02

sleep 0.2

# Type "aut" then fast-complete to "autotest "
type_text "aut" 0.08
sleep 0.5
type_text "otest " 0.02

sleep 0.15

# Type rest of command
type_text "collatz" 0.06
sleep 0.6
printf "\n"

# Autotest output
sleep 0.2
echo -e "  ${GREEN}●${RST} ${DIM}sync 0.3s${RST}"
sleep 0.3
echo -e "${MAGENTA}========================================${RST}"
sleep 0.1
echo "1521 check-recursion collatz.c"
echo "dcc -fsanitize=address -o collatz collatz.c"
sleep 0.15
echo "Test 0 (./collatz 1) - passed"
sleep 0.1
echo "Test 1 (./collatz 12) - passed"
sleep 0.1
echo "Test 2 (./collatz 10) - passed"
sleep 0.1
echo "Test 3 (./collatz 42) - passed"
sleep 0.1
echo "Test 4 (./collatz 100) - passed"
sleep 0.15
echo -e "${GREEN}5 tests passed${RST} 0 tests failed"
echo -e "${MAGENTA}========================================${RST}"
sep

sleep 1

# ═══════════════════════════════════════════
# Scene 3: dcc compile + run
# ═══════════════════════════════════════════
prompt
type_text "dcc hello.c -o hello && ./hello" 0.05
sleep 0.5
printf "\n"

sleep 0.2
echo -e "  ${GREEN}●${RST} ${DIM}sync 0.2s${RST}"
sleep 0.3
echo "  Hello, World!"
sep

sleep 1

# ═══════════════════════════════════════════
# Scene 4: exit
# ═══════════════════════════════════════════
prompt
type_text "exit" 0.08
sleep 0.4
printf "\n"
echo -e "  ${DIM}Bye.${RST}"
echo ""

sleep 0.8

# ═══════════════════════════════════════════
# Scene 5: Install hint
# ═══════════════════════════════════════════
printf "$ "
type_text "pip install cselab" 0.06
printf "\n"
sleep 3
