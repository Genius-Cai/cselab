# cselab — Context for Gemini CLI

cselab is a CLI tool that lets UNSW CSE students run server commands locally.

It syncs files via rsync and executes commands on cse.unsw.edu.au via SSH ControlMaster.

## Commands

- `cselab run "<cmd>"` — sync + run command on CSE server
- `cselab run --no-sync "<cmd>"` — run without syncing
- `cselab sync` — sync files only
- `cselab pull` — pull files from server
- `cselab ssh` — interactive SSH session
- `cselab watch "<cmd>"` — auto-run on file change

## Usage

```bash
cd ~/COMP1521/lab01
cselab run "1521 autotest"      # test
cselab run "give cs1521 lab01 hello.s"  # submit
cselab watch "1521 autotest"    # auto-test on save
```

Course prefix = last 4 digits (COMP1521 → 1521).

Always cd to the assignment directory first.
