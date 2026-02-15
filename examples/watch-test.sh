#!/usr/bin/env bash
# Example: Watch mode — auto-run autotest on file save
# Usage: ./watch-test.sh [course_prefix]
# Example: ./watch-test.sh 1521

set -euo pipefail

PREFIX="${1:-1521}"

echo "Watching for changes in $(pwd)..."
echo "Autotest will run on every file save. Ctrl+C to stop."
echo

cselab watch "${PREFIX} autotest"
