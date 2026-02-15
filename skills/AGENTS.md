# cselab — Agent Instructions (Codex CLI)

You help UNSW students run CSE server commands from their local machine using `cselab`.

## Setup

If cselab is not installed:
```bash
pip install git+https://github.com/Genius-Cai/cselab.git
cselab init  # prompts for zID + password
```

## Commands

```bash
cselab run "<command>"         # sync files + run on CSE
cselab run --no-sync "<cmd>"   # run without file sync
cselab sync                    # sync files only
cselab pull                    # pull files from server
cselab ssh                     # interactive SSH session
cselab watch "<command>"       # auto-run on file changes
cselab clean                   # remove remote workspaces
cselab disconnect              # close SSH connection
```

## Common Patterns

```bash
# Autotest
cd ~/COMP1521/lab01
cselab run "1521 autotest"

# Submit
cselab run "give cs1521 lab01 hello.s"

# Compile + run
cselab run "make && ./test"

# Info commands (no file sync needed)
cselab run --no-sync "1521 classrun -sturec"
```

## Course prefixes

- COMP1511 → `1511`
- COMP1521 → `1521`
- COMP2521 → `2521`

Pattern: last 4 digits of course code.

## Rules

- Always `cd` to the assignment directory before running cselab
- Use `cselab run` not raw SSH for testing
- Use `--no-sync` for non-file commands
- Don't modify `~/.config/cselab/config.toml` unless asked
- If connection fails, try `cselab disconnect` then retry
