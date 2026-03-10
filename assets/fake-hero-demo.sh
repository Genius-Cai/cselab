#!/bin/bash
# Hero demo — headless mode: one command, clean output
# Shows: $ cselab run "1521 autotest collatz" → 3-step output → tests passed

RST="\033[0m"
DIM="\033[90m"
GREEN="\033[32m"
YELLOW="\033[33m"
MAGENTA="\033[35m"

type_text() {
    local text="$1"
    local delay="${2:-0.06}"
    for (( i=0; i<${#text}; i++ )); do
        printf '%s' "${text:$i:1}"
        sleep "$delay"
    done
}

# ── Clear ──
printf '\033[2J\033[H'
sleep 0.5

# Type the command
printf "$ "
type_text 'cselab run "1521 autotest collatz"' 0.05
sleep 0.6
printf "\n"

# Step 1: Connect
sleep 0.3
printf "${DIM}[1/3] Connecting to cse.unsw.edu.au...${RST}"
sleep 0.8
printf " ${GREEN}OK${RST} (0.0s)\n"

# Step 2: Sync
sleep 0.2
printf "${DIM}[2/3] Syncing files...${RST}"
sleep 0.5
printf " ${GREEN}OK${RST} (0.1s)\n"

# Step 3: Run
sleep 0.2
printf "${DIM}[3/3] Running:${RST} ${YELLOW}1521 autotest collatz${RST}\n"
sleep 0.1
printf "${MAGENTA}========================================${RST}\n"

# Autotest output
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
printf "${GREEN}5 tests passed${RST} 0 tests failed\n"
printf "${MAGENTA}========================================${RST}\n"
printf "Exit: ${GREEN}OK${RST}\n"

sleep 3
