# cselab

Run UNSW CSE commands from your local machine — fast, reliable, interactive.

## Why cselab?

UNSW CSE students must run `autotest`, `give`, and other course commands on the CSE server (`cse.unsw.edu.au`). The typical workflow is:

1. SSH into CSE server
2. Edit code there (or manually copy files back and forth)
3. Run the command
4. Repeat

This is painful. You lose your local editor, extensions, and tools. Or you waste time copying files manually.

**cselab lets you write code locally and run CSE commands as if you were on the server.** One command syncs your files and executes remotely — your local VS Code / Vim stays untouched.

## How It Works

```
Local Machine (your laptop)              CSE Server
┌─────────────────────────┐              ┌──────────────────────┐
│                         │   1. SSH     │                      │
│  ~/COMP1521/lab01/      │──────────────│  ControlMaster       │
│    hello.c              │  (once)      │  (persistent conn)   │
│    Makefile             │              │                      │
│                         │   2. rsync   │  ~/.cselab/          │
│                         │──────────────│    workspaces/       │
│                         │  (delta)     │      lab01-a3f2/     │
│                         │              │        hello.c       │
│                         │   3. ssh     │        Makefile      │
│                         │──────────────│                      │
│                         │  (exec)      │  $ 1521 autotest     │
│                         │              │                      │
│  Terminal:              │   4. output  │                      │
│  ✅ All tests passed    │◄─────────────│                      │
│                         │  (stream)    │                      │
└─────────────────────────┘              └──────────────────────┘
```

### Step-by-step flow

When you run `cselab run "1521 autotest"`:

1. **Connect** — Establishes an SSH ControlMaster connection (reused across all subsequent commands, password entered only once)
2. **Sync** — `rsync` uploads your local directory to the server, using delta compression (only changed bytes are transferred)
3. **Execute** — Runs your command on the server in the synced directory, with full interactive terminal support
4. **Stream** — Output streams back to your terminal in real-time, exit code is preserved

Subsequent runs reuse the SSH connection (0ms reconnect) and rsync only transfers changes (sub-second for typical edits).

## Installation

**Requirements:** Python 3.10+, `rsync`, `ssh` (pre-installed on macOS and most Linux)

```sh
pip install git+https://github.com/geniuscai/cselab.git
```

Or clone and install locally:

```sh
git clone https://github.com/geniuscai/cselab.git
cd cselab
pip install .
```

## Quick Start

```sh
# 1. One-time setup
cselab init
# Enter your zID and password when prompted

# 2. Go to your assignment directory
cd ~/COMP1521/lab01

# 3. Run any CSE command
cselab run "1521 autotest"
```

That's it. Your local files are synced and the command runs on CSE.

## Usage

### `cselab run <command>`

Sync files + run command on CSE server.

```sh
cselab run "1521 autotest"             # sync + autotest
cselab run "2521 autotest"             # works with any course
cselab run "give cs1521 lab01 hello.c" # submit assignment
cselab run --no-sync "1521 classrun -sturec"  # skip sync for non-file commands
```

Example output:

```
[1/3] Connecting to cse.unsw.edu.au... OK (0.0s)
[2/3] Syncing files... OK (0.2s)
[3/3] Running: 1521 autotest
========================================
Test 1 - ... passed
Test 2 - ... passed
All tests passed!
========================================
Exit: OK
```

### `cselab pull`

Download files from the server back to your local machine. Useful when the server generates output files.

```sh
cselab run "make"        # compile on server, generates binary
cselab pull              # pull generated files back
```

### `cselab watch <command>`

Watch for local file changes and auto-run a command. Save a file, autotest runs automatically.

```sh
cselab watch "1521 autotest"
# Now edit hello.c in your editor, save, and autotest runs automatically
```

### `cselab ssh`

Open an interactive SSH session directly in your synced workspace directory.

```sh
cselab ssh
# You're now in a shell on CSE, in the same directory as your local files
```

### `cselab sync`

Sync files without running a command.

```sh
cselab sync
```

### Other commands

```sh
cselab config       # show config file location and contents
cselab clean        # remove all remote workspace directories
cselab disconnect   # close SSH connection
cselab --help       # full help
```

## Configuration

Config file: `~/.config/cselab/config.toml`

```toml
[server]
host = "cse.unsw.edu.au"
port = 22
user = "z5555555"  # your zID

[auth]
method = "password"
password = "your_password"  # optional, will prompt if missing

# Alternative: SSH key auth (no password needed)
# [auth]
# method = "key"
# key_path = "~/.ssh/id_rsa"

[sync]
# Directories excluded from sync (in addition to .gitignore)
exclude = [".git", "__pycache__", "node_modules", ".venv", "target"]
```

cselab respects `.gitignore` and `.ignore` files — directories like `node_modules/` and `__pycache__/` are automatically excluded from sync.

## How cselab Helps Students

### The problem

CSE students face a daily friction loop:

- **SSH + remote editing** — You lose VS Code, your extensions, copilot, your muscle memory. Editing in `vim` over SSH is a skill barrier unrelated to the course material.
- **Manual file copy** — `scp` files back and forth before every autotest. Easy to forget, easy to test stale code.
- **Slow iteration** — Each cycle (edit → copy → test) takes 30-60 seconds. Over a 10-week term, this adds up to hours of wasted time.
- **No local tooling** — Can't use local debuggers, linters, or formatters on code that must run on CSE.

### What cselab enables

- **Stay in your editor.** Write code in VS Code, Cursor, or any local editor with full language support, extensions, and AI assistance.
- **One-command testing.** `cselab run "1521 autotest"` replaces the entire SSH-copy-run cycle.
- **Sub-second iteration.** After the first run, syncing a single file change takes ~0.1s. Edit, save, test — near-instant feedback.
- **Watch mode.** `cselab watch "1521 autotest"` makes it fully automatic — save file, see test results.
- **Focus on learning.** Remove the tooling friction so students can focus on the actual course content: C, data structures, algorithms — not SSH workflows.

## Comparison with cserun

This project was inspired by [cserun](https://github.com/xxxbrian/cserun) by [@xxxbrian](https://github.com/xxxbrian), which pioneered the idea of running CSE commands from a local machine. cserun demonstrated the concept and solved a real pain point for UNSW students.

We chose to build a new project rather than contribute to cserun because the improvements we wanted required fundamental architectural changes — a different language, different SSH transport, and different sync mechanism. These aren't incremental fixes but a different technical foundation.

### Architectural differences

| | cselab | cserun |
|---|---|---|
| **Language** | Python | Rust |
| **SSH library** | Native OpenSSH (via subprocess) | libssh2 (C binding via `ssh2` crate) |
| **Connection** | SSH ControlMaster (persistent, reused) | Fresh TCP+SSH per invocation |
| **File sync** | `rsync` (delta compression, incremental) | SFTP (full file upload, one-by-one) |
| **Interactive I/O** | Full PTY via `ssh -tt` | Non-blocking poll loop, no stdin |
| **Dependencies** | Python 3.10+ (pre-installed on macOS) | Rust toolchain + C compiler (for libssh2) |

### Performance (real measurements, 50 files x 10KB)

| Metric | cselab | cserun | Improvement |
|--------|--------|--------|-------------|
| Command latency (warm) | **0.15s** | 0.73s | 4.9x faster |
| File sync (50 files) | **0.30s** | 2.13s | 7.1x faster |
| End-to-end (sync + compile + run) | **0.42s** | 2.14s | 5.0x faster |
| Cold connect | **0.48s** | 0.73s | 1.5x faster |

### Reliability (20 rapid sequential invocations)

| | cselab | cserun |
|---|---|---|
| Success rate | **20/20 (100%)** | 9/20 (45%) |
| Failure mode | — | `libssh2: Failed getting banner` |

The reliability issue stems from libssh2's SSH handshake implementation, which intermittently fails under rapid reconnection. cselab avoids this entirely by maintaining a persistent connection via ControlMaster.

### Feature comparison

| Feature | cselab | cserun |
|---------|--------|--------|
| Run commands | yes | yes |
| File sync | yes (rsync) | yes (SFTP) |
| .gitignore support | yes | yes |
| Skip sync (`--no-sync`) | yes | yes |
| Environment variables | planned | yes |
| **Pull files from server** | **yes** | no |
| **Interactive commands** | **yes** | no |
| **Watch mode** | **yes** | no |
| **Interactive SSH session** | **yes** | no |
| **Connection reuse** | **yes** | no |
| **Workspace cleanup** | **yes** | no |

### Acknowledgment

Thank you to [@xxxbrian](https://github.com/xxxbrian) for creating cserun and proving that local-to-CSE command execution is both possible and valuable. cselab builds on that vision with a different technical approach.

## License

MIT
