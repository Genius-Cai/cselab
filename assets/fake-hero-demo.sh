#!/bin/bash
# Hero demo — "old way vs cselab" for README / landing page
# The tape just runs this script. No Hide/Show tricks.

RST="\033[0m"
BOLD="\033[1m"
DIM="\033[90m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
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

# ═══════════════════════════════════════════
# Scene 1: The old way (painful)
# ═══════════════════════════════════════════
echo -e "${DIM}# The old way...${RST}"
sleep 0.8

printf "$ "
type_text "scp hello.c z5502277@cse.unsw.edu.au:COMP1521/lab01/" 0.04
printf "\n"
sleep 0.3
echo -e "${DIM}hello.c              100%  842     1.2MB/s   00:00${RST}"
sleep 0.5

printf "$ "
type_text "ssh z5502277@cse.unsw.edu.au" 0.04
printf "\n"
sleep 0.5
echo -e "${DIM}Password:${RST} ********"
sleep 0.8
echo -e "${DIM}Last login: Mon Mar 10 13:00:01 2026${RST}"
sleep 0.3

printf "$ "
type_text "cd COMP1521/lab01 && 1521 autotest hello" 0.04
printf "\n"
sleep 0.5
echo -e "${RED}1 test failed${RST}  ${DIM}(forgot to save latest edit)${RST}"
sleep 1.5

# ── Clear, switch to cselab ──
printf '\033[2J\033[H'
sleep 0.5

# ═══════════════════════════════════════════
# Scene 2: With cselab (one command)
# ═══════════════════════════════════════════
echo -e "${GREEN}# With cselab:${RST}"
sleep 0.8

printf "$ "
type_text "cselab run \"1521 autotest hello\"" 0.05
sleep 0.5
printf "\n"

# Real cselab output format
sleep 0.3
echo -e "${DIM}[1/3] Connecting to cse.unsw.edu.au...${RST} ${GREEN}OK${RST} (0.0s)"
sleep 0.3
echo -e "${DIM}[2/3] Syncing files...${RST} ${GREEN}OK${RST} (0.1s)"
sleep 0.2
echo -e "${DIM}[3/3] Running:${RST} ${YELLOW}1521 autotest hello${RST}"
sleep 0.1
echo -e "${MAGENTA}========================================${RST}"
sleep 0.1
echo "1521 check-recursion hello.c"
echo "dcc -fsanitize=address -o hello hello.c"
sleep 0.15
echo "Test 0 (./hello) - passed"
sleep 0.1
echo "Test 1 (./hello world) - passed"
sleep 0.1
echo "Test 2 (./hello 42) - passed"
sleep 0.1
echo "Test 3 (./hello COMP1521) - passed"
sleep 0.1
echo "Test 4 (./hello cselab) - passed"
sleep 0.15
echo -e "${GREEN}5 tests passed${RST} 0 tests failed"
echo -e "${MAGENTA}========================================${RST}"
echo -e "Exit: ${GREEN}OK${RST}"

sleep 1

# Install hint
printf "\n$ "
type_text "pip install cselab" 0.06
printf "\n"
sleep 3
