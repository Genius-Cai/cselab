#!/usr/bin/env bash
# Example: Run autotest for a COMP1521 lab
# Usage: ./autotest.sh [course_prefix] [task]
# Example: ./autotest.sh 1521 lab01

set -euo pipefail

PREFIX="${1:-1521}"
TASK="${2:-}"

if [ -n "$TASK" ]; then
    cd "$HOME/COMP${PREFIX}/${TASK}" 2>/dev/null || {
        echo "Directory ~/COMP${PREFIX}/${TASK} not found"
        exit 1
    }
fi

echo "Running ${PREFIX} autotest in $(pwd)..."
cselab run "${PREFIX} autotest"
