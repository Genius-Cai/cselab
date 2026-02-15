# cselab — Run UNSW CSE Commands Locally

You are helping a UNSW CSE student use `cselab` to run CSE server commands from their local machine.

## What is cselab?

cselab syncs local files to cse.unsw.edu.au via rsync and executes commands remotely via SSH ControlMaster. Students write code locally (VS Code, Cursor, etc.) and test on CSE with one command.

## Available Commands

| Command | Description |
|---------|-------------|
| `cselab init` | Setup config (zID + password) |
| `cselab run "<cmd>"` | Sync files + run command on CSE |
| `cselab run --no-sync "<cmd>"` | Run without syncing files |
| `cselab sync` | Sync files only (no command) |
| `cselab pull` | Pull remote files back to local |
| `cselab ssh` | Interactive SSH into workspace |
| `cselab watch "<cmd>"` | Auto-run on file changes |
| `cselab clean` | Remove all remote workspaces |
| `cselab config` | Show config file location |
| `cselab disconnect` | Close SSH connection |

## Usage Examples

### Run autotest
```bash
cd ~/COMP1521/lab01
cselab run "1521 autotest"
```

### Submit assignment
```bash
cd ~/COMP1521/ass1
cselab run "give cs1521 ass1_mips mips_bit_fields.s"
```

### Compile and test
```bash
cselab run "make && ./test"
```

### Watch mode (auto-run on save)
```bash
cselab watch "1521 autotest"
# Now edit files in your editor — autotest runs automatically on save
```

### Pull generated files from server
```bash
cselab run "make"     # compile on CSE
cselab pull           # download built files
```

### Interactive debugging on server
```bash
cselab ssh
# You're now in a shell on CSE, in your workspace directory
# Run gdb, valgrind, etc. interactively
```

### Non-file commands (skip sync)
```bash
cselab run --no-sync "1521 classrun -sturec"
cselab run --no-sync "acc"
```

## First-Time Setup

1. Install cselab:
```bash
pip install git+https://github.com/Genius-Cai/cselab.git
```

Or one-line install:
```bash
curl -sSL https://raw.githubusercontent.com/Genius-Cai/cselab/master/install.sh | bash
```

2. Initialize config:
```bash
cselab init
# Enter zID (e.g. z5555555)
# Enter password
```

3. Test:
```bash
cd ~/some-course-dir
cselab run "echo hello from CSE"
```

## Configuration

Config file: `~/.config/cselab/config.toml`

```toml
[server]
host = "cse.unsw.edu.au"
port = 22
user = "z5555555"

[auth]
method = "password"
password = "your_password"

# Or use SSH key:
# [auth]
# method = "key"
# key_path = "~/.ssh/id_rsa"

[sync]
exclude = [".git", "__pycache__", "node_modules", ".venv", "target"]
```

## How It Works

```
Local Machine                          CSE Server
┌──────────────────┐                   ┌──────────────────┐
│  Your code       │  1. SSH Master    │  ControlMaster   │
│  (VS Code/Vim)   │──────────────────→│  (persistent)    │
│                  │  2. rsync delta   │                  │
│                  │──────────────────→│  ~/.cselab/      │
│                  │  3. ssh exec      │    workspaces/   │
│                  │──────────────────→│      lab01-xxx/  │
│  Terminal output │  4. stream back   │  $ 1521 autotest │
│  ✅ All passed   │←──────────────────│                  │
└──────────────────┘                   └──────────────────┘
```

- SSH ControlMaster keeps connection alive (no reconnect per command)
- rsync uses delta compression (only changed bytes transfer)
- .gitignore is respected automatically

## Troubleshooting

### Connection failed
- Check zID and password: `cselab init`
- CSE server may be down: try `ssh z5555555@cse.unsw.edu.au` manually
- Stale socket: `cselab disconnect` then retry

### Sync failed
- Check local directory has files
- Large files? Add to `.gitignore` or config exclude list
- Permission issue: check rsync is installed (`which rsync`)

### Command not found on server
- Use full course prefix: `1521 autotest` not just `autotest`
- Some commands need specific PATH: try `cselab ssh` and test manually

### Watch mode not detecting changes
- macOS: install fswatch (`brew install fswatch`) for better performance
- Fallback polling has 2s delay

## Course Command Patterns

| Course | Autotest | Give |
|--------|----------|------|
| COMP1511 | `1511 autotest` | `give cs1511 lab01 main.c` |
| COMP1521 | `1521 autotest` | `give cs1521 lab01 hello.s` |
| COMP2521 | `2521 autotest` | `give cs2521 lab01 main.c` |
| COMP1531 | `1531 autotest` | `give cs1531 lab01 ...` |
| COMP6080 | `6080 autotest` | `give cs6080 ...` |

General pattern: `{course_code_last4} autotest` and `give cs{code} {task} {files}`

## Tips for AI Assistants

When helping a student with cselab:

1. **Always `cd` to the assignment directory first** before running cselab commands
2. **Use `cselab run` for testing**, not manual SSH + file copy
3. **If autotest fails**, read the output carefully — cselab streams the full server output
4. **For compilation errors**, the output is identical to what you'd see on the server
5. **Use `--no-sync` for info commands** that don't need files (classrun, sturec, etc.)
6. **Use `cselab watch`** when iterating on fixes — saves time vs. manual re-runs
7. **Don't modify `~/.config/cselab/config.toml`** unless the student asks
