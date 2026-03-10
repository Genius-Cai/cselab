<div align="center">

<img src="assets/zap-teal.png" alt="Zap — cselab mascot" width="80" />

# cselab

**Run UNSW CSE commands from your local machine — fast, reliable, interactive.**

<p>
  <img src="https://img.shields.io/pypi/v/cselab?style=flat&color=4ecdc4&label=PyPI" alt="PyPI version" />
  <img src="https://img.shields.io/badge/Python-3.10+-4ecdc4?style=flat&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/License-MIT-4ecdc4?style=flat" alt="MIT License" />
  <img src="https://img.shields.io/badge/SSH-ControlMaster-4ecdc4?style=flat" alt="SSH ControlMaster" />
  <img src="https://img.shields.io/badge/Sync-rsync-4ecdc4?style=flat" alt="rsync" />
</p>

English | [简体中文](README_CN.md)

[Features](#why-cselab) · [Comparison](#comparison-with-other-approaches) · [Quick Start](#quick-start) · [For CSE Staff](#for-cse-staff--administrators) · [AI Integration](#ai-platform-integration)

<p><img src="assets/demo-repl.gif" alt="cselab REPL — interactive mode demo" width="700" /></p>

</div>

---

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

**One-line install (recommended):**

```sh
curl -sSL https://raw.githubusercontent.com/Genius-Cai/cselab/master/install.sh | bash
```

**Or via pip:**

```sh
pip install cselab
```

**Or clone and install locally:**

```sh
git clone https://github.com/Genius-Cai/cselab.git
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

## Interactive Mode

Just type `cselab` with no arguments to enter the REPL:

```
$ cd ~/COMP1521/lab01
$ cselab

  cselab v0.2.0
  z5502277@cse.unsw.edu.au

  Type any CSE command. Ctrl+C to exit.

  Connecting... OK

⚡ 1521 autotest collatz
[sync] OK (0.1s)
5 tests passed 0 tests failed

⚡ give cs1521 lab01 collatz.c
[sync] OK (0.1s)
Submission received.

⚡ exit
```

Same commands as the CSE server — zero learning curve.

The headless mode still works for scripts and CI:

```bash
cselab run "1521 autotest collatz"
```

<p align="center"><img src="assets/demo-hero.gif" alt="cselab headless mode — run any CSE command" width="700" /></p>

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

## Comparison with Other Approaches

Every UNSW CSE student needs to run `autotest` and `give` on the CSE server. Here's how the available options stack up:

| | VLAB | SSH FS | Remote-SSH | cserun | **cselab** |
|---|:---:|:---:|:---:|:---:|:---:|
| **Use local editor** (VS Code, Cursor, Vim) | No | Partial | Yes | Yes | **Yes** |
| **Run autotest/give** | Yes | Needs separate terminal | Yes | Yes | **Yes** |
| **Server load** | High | Low | **Very High** | Low | **Near Zero** |
| **Reliability** | Disconnects after 2h idle | Good | Process reapers kill it | 45% (libssh2 failures) | **100%** |
| **Watch mode** (auto-test on save) | No | No | No | No | **Yes** |
| **Install difficulty** | None (browser) | Medium (FUSE) | Medium (VS Code ext) | Hard (Rust toolchain) | **Easy** (`pip install`) |
| **AI editor support** (Cursor, Windsurf) | No | No | No | No | **Yes** |
| **Offline editing** | No | No | No | No | **Yes** |
| **Pull files from server** | N/A | Automatic | Automatic | No | **Yes** |
| **Interactive SSH** | Yes (full desktop) | No | Yes | No | **Yes** |

> **Key insight:** VS Code Remote-SSH gives the best editing experience, but CSE [explicitly discourages it](https://taggi.cse.unsw.edu.au/FAQ/VS_Code_Remote-SSH/) because it spawns Node.js processes that consume ~200-500MB RAM per student. CSE runs reaper scripts to kill these processes, and students risk account restrictions.
>
> cselab gives you the same local editing workflow with **zero server-side footprint**.

---

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

## AI Platform Integration

cselab ships with skill files for popular AI coding assistants — let AI help you run CSE commands:

| Platform | File | Install |
|----------|------|---------|
| **Claude Code** | `skills/cselab.md` | `cp skills/cselab.md ~/.claude/commands/` |
| **Codex CLI** | `skills/AGENTS.md` | `cp skills/AGENTS.md ./AGENTS.md` |
| **Gemini CLI** | `skills/GEMINI.md` | `cp skills/GEMINI.md ./GEMINI.md` |
| **Claude.ai** | `skills/cselab.md` | Upload to Project Knowledge |
| **Cursor** | `skills/cselab.md` | `cp skills/cselab.md .cursor/rules/` |
| **Windsurf** | `skills/cselab.md` | `cp skills/cselab.md .windsurfrules/` |

See [docs/deployment.md](docs/deployment.md) for detailed setup instructions.

## For CSE Staff / Administrators

If you manage CSE infrastructure or coordinate a course, here's why cselab benefits the server environment.

### The Problem: Remote-SSH is Straining Login Servers

Students increasingly use VS Code Remote-SSH for local editing convenience. But each Remote-SSH session spawns a persistent Node.js server on the login machines, causing:

- **200-500MB RAM per student** from VS Code Server + file watchers + language indexing
- Persistent connections that last entire coding sessions (hours)
- CSE has had to deploy **reaper scripts**, dedicate **vscode.cse/vscode2.cse** servers, and impose **SSH rate limits** (20/min firewall ban)

Students use Remote-SSH because the alternatives (VLAB, SSH FS) don't provide a satisfactory local editing experience. They need a better option.

### How cselab Differs

```
Server resource comparison (100 concurrent students):

VS Code Remote-SSH:  Node.js resident process + file watchers + indexing
                     ~200-500MB RAM/student → 20-50GB total, persistent

SSH FS (SSHFS):      SFTP connection held open
                     ~50MB/student → ~5GB total, persistent

cselab:              rsync (0.3s) + SSH exec (<10s) + disconnect
                     ~0MB idle → near 0GB total, burst only
```

cselab uses **rsync** for file sync (0.3s delta transfer) and **short-lived SSH** for command execution. There are no background processes, no persistent connections, and no Node.js. After each command completes, the server resources are fully released.

### Benefits for CSE

1. **Zero server load at idle** -- no Node.js, no persistent connections
2. **Fewer SSH connections** -- SSH ControlMaster multiplexes over one socket, won't trigger rate limits
3. **Open source (MIT)** -- fully auditable, no server-side components
4. **Reduces support tickets** -- students stop asking about SSH disconnects and VLAB lag
5. **Compatible with all courses** -- autotest, give, classrun all work unchanged

### Recommendation

If you'd like to evaluate cselab, the source is at [github.com/Genius-Cai/cselab](https://github.com/Genius-Cai/cselab). It requires only standard `ssh` and `rsync` on the student's machine and makes no modifications to the server environment.

We'd welcome the opportunity to have cselab reviewed for inclusion in the [CSE Home Computing Guide](https://taggi.cse.unsw.edu.au/FAQ/Home_computing/).

---

## Project Structure

```
cselab/
├── src/cselab/
│   ├── cli.py             # CLI entry point (9 subcommands)
│   ├── config.py          # Config management
│   ├── connection.py      # SSH/rsync transport
│   ├── repl.py            # Interactive REPL mode
│   ├── banner.py          # Welcome banner with mascot
│   ├── mascot.py          # Zap mascot renderer (seasonal)
│   └── theme.py           # ANSI color constants
├── skills/
│   ├── cselab.md          # Claude Code skill
│   ├── AGENTS.md          # Codex CLI instructions
│   └── GEMINI.md          # Gemini CLI context
├── docs/
│   └── deployment.md      # Multi-platform deployment guide
├── examples/
│   ├── autotest.sh        # Run autotest
│   ├── submit.sh          # Submit via give
│   └── watch-test.sh      # Watch mode demo
├── install.sh             # One-line installer
├── README.md              # English docs
├── README_CN.md           # 中文文档
└── LICENSE                # MIT
```

## Author

**Steven Cai** ([@Genius-Cai](https://github.com/Genius-Cai))

UNSW Sydney — Bachelor of Commerce / Computer Science

## License

[MIT](LICENSE)
