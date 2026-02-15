#!/usr/bin/env bash
# cselab installer — run UNSW CSE commands locally
# Usage: curl -sSL https://raw.githubusercontent.com/Genius-Cai/cselab/main/install.sh | bash
set -euo pipefail

REPO="https://github.com/Genius-Cai/cselab.git"
MIN_PYTHON="3.10"

info()  { printf '\033[1;34m→\033[0m %s\n' "$*"; }
ok()    { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
err()   { printf '\033[1;31m✗\033[0m %s\n' "$*" >&2; }
die()   { err "$*"; exit 1; }

# --- Python check ---
info "Checking Python..."
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        if [ -n "$ver" ] && "$cmd" -c "
import sys
req = tuple(map(int, '$MIN_PYTHON'.split('.')))
sys.exit(0 if sys.version_info[:2] >= req else 1)
" 2>/dev/null; then
            PYTHON="$cmd"
            break
        fi
    fi
done
[ -n "$PYTHON" ] || die "Python $MIN_PYTHON+ required. Install from https://python.org"
ok "Found $PYTHON ($ver)"

# --- Install cselab ---
info "Installing cselab..."
if command -v pipx &>/dev/null; then
    info "Using pipx for isolated install"
    pipx install "git+${REPO}" --force 2>&1
elif command -v uv &>/dev/null; then
    info "Using uv for install"
    uv tool install "git+${REPO}" --force 2>&1
else
    "$PYTHON" -m pip install --user "git+${REPO}" 2>&1
fi

# Verify
if ! command -v cselab &>/dev/null; then
    # pip --user installs might not be on PATH
    USER_BIN=$("$PYTHON" -m site --user-base)/bin
    if [ -x "$USER_BIN/cselab" ]; then
        err "cselab installed but not on PATH"
        info "Add to your shell profile: export PATH=\"$USER_BIN:\$PATH\""
        info "Then restart your terminal and re-run this script"
        exit 1
    fi
    die "Installation failed — cselab command not found"
fi
ok "cselab installed at $(which cselab)"

# --- Initialize ---
info "Running cselab init..."
info "Enter your zID and password when prompted"
echo
cselab init
echo

# --- Test ---
info "Testing connection..."
if cselab run --no-sync "echo cselab_ok" 2>&1 | grep -q "cselab_ok"; then
    ok "Connection works!"
else
    err "Test failed — check your credentials with: cselab init"
    exit 1
fi

echo
ok "cselab is ready!"
info "Usage: cd ~/COMP1521/lab01 && cselab run \"1521 autotest\""
