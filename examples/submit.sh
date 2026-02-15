#!/usr/bin/env bash
# Example: Submit assignment via give
# Usage: ./submit.sh <course> <task> <files...>
# Example: ./submit.sh cs1521 lab01 hello.s

set -euo pipefail

if [ $# -lt 3 ]; then
    echo "Usage: $0 <course> <task> <files...>"
    echo "Example: $0 cs1521 lab01 hello.s"
    exit 1
fi

COURSE="$1"
TASK="$2"
shift 2
FILES="$*"

echo "Submitting to ${COURSE} ${TASK}: ${FILES}"
cselab run "give ${COURSE} ${TASK} ${FILES}"
