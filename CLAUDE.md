# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

cselab is a Python CLI that lets UNSW CSE students run server commands (`autotest`, `give`, etc.) from their local machine. It syncs files via rsync and executes remotely via SSH ControlMaster — no manual SSH or file copying needed.

## Build & Run

```bash
pip install -e .              # editable install
cselab --version              # verify
cselab init --user z5555555   # setup config
cselab run "echo hello"       # test
```

Build system is hatchling. No test suite yet. No linter configured.

## Architecture

Three modules in `src/cselab/`, zero external dependencies (stdlib only, except optional `tomli` for Python <3.11):

**`connection.py`** — SSH/rsync transport layer
- `connect()` starts an SSH ControlMaster (`ssh -fNM`) with ControlPersist=1800s
- Password auth uses a temp SSH_ASKPASS script (written to `/tmp/cselab_askpass_*`, cleaned up in finally block)
- `rsync_up/rsync_down` pass `-e "ssh <control-args>"` so rsync reuses the ControlMaster socket
- rsync respects `.gitignore` via `--filter=:- .gitignore`
- Socket path: `/tmp/cselab-{user}@{host}-{port}`

**`config.py`** — TOML config at `~/.config/cselab/config.toml`
- `Config` dataclass holds all settings
- `remote_workspace()` generates a deterministic remote path from MD5 of the local cwd: `~/.cselab/workspaces/{dirname}-{hash12}`
- Supports password auth (SSH_ASKPASS) and key auth (`-i`)

**`cli.py`** — 9 subcommands, all follow the same pattern: `load_config() → connect() → do_work()`
- `run` is the main command: connect → rsync_up → ssh_exec (3-step with timing output)
- `watch` uses fswatch on macOS (preferred) with polling fallback
- Lazy imports (`from cselab.connection import ...` inside functions) keep `--help` fast

## Key Design Decisions

- **SSH ControlMaster over libssh2**: persistent socket means 0ms reconnect on subsequent commands
- **rsync over SFTP**: delta compression, .gitignore support, `--delete` keeps remote clean
- **SSH_ASKPASS trick**: password auth without interactive TTY — creates temp script, sets `SSH_ASKPASS_REQUIRE=force`, connects with `stdin=DEVNULL`
- **No dependencies**: runs on stock Python 3.10+ with system ssh/rsync (pre-installed on macOS/Linux)

## Remote File Layout

On the CSE server, cselab creates:
```
~/.cselab/workspaces/{dirname}-{md5_12char}/
```
Each local directory maps to a unique remote workspace. `cselab clean` removes all of them.
