# Deployment Guide

## Installation Methods

### One-line install (recommended)

```bash
curl -sSL https://raw.githubusercontent.com/Genius-Cai/cselab/master/install.sh | bash
```

This will:
1. Check Python 3.10+ is available
2. Install cselab via pipx/uv/pip (auto-detects best method)
3. Run `cselab init` for first-time setup
4. Test the connection

### pip install

```bash
pip install git+https://github.com/Genius-Cai/cselab.git
```

### Clone + install

```bash
git clone https://github.com/Genius-Cai/cselab.git
cd cselab
pip install .
```

### pipx (isolated environment)

```bash
pipx install git+https://github.com/Genius-Cai/cselab.git
```

### uv

```bash
uv tool install git+https://github.com/Genius-Cai/cselab.git
```

## AI Platform Integration

### Claude Code

```bash
# Option 1: Install as slash command
mkdir -p ~/.claude/commands
cp skills/cselab.md ~/.claude/commands/cselab.md

# Usage: /cselab in Claude Code

# Option 2: Add to project instructions
# Copy skills/cselab.md content to your project's CLAUDE.md
```

### Codex CLI (OpenAI)

```bash
# Copy to your project root
cp skills/AGENTS.md /path/to/your/project/AGENTS.md

# Usage
codex "run autotest for COMP1521 lab01"
```

### Gemini CLI (Google)

```bash
cp skills/GEMINI.md /path/to/your/project/GEMINI.md

gemini "test my COMP1521 code"
```

### Claude.ai (Web)

1. Create a Project in claude.ai
2. Upload `skills/cselab.md` to Project Knowledge
3. Chat: "Help me run autotest for COMP1521 lab01"

### Cursor

```bash
mkdir -p .cursor/rules
cp skills/cselab.md .cursor/rules/cselab.md
```

### Windsurf

```bash
mkdir -p .windsurfrules
cp skills/cselab.md .windsurfrules/cselab.md
```

### Aider

```bash
# Add as context file
aider --read skills/cselab.md
```

## Auto-Deploy Script

Deploy cselab + AI skills in one command:

```bash
curl -sSL https://raw.githubusercontent.com/Genius-Cai/cselab/master/install.sh | bash
```

The installer handles everything: Python check, install, init, and connection test.

To also install Claude Code skill:

```bash
# After cselab is installed
cselab skill install  # (planned feature)

# Manual for now:
mkdir -p ~/.claude/commands
curl -sSL https://raw.githubusercontent.com/Genius-Cai/cselab/master/skills/cselab.md \
  -o ~/.claude/commands/cselab.md
```

## Requirements

| Requirement | Notes |
|-------------|-------|
| Python 3.10+ | Pre-installed on macOS, most Linux |
| rsync | Pre-installed on macOS, most Linux |
| ssh | Pre-installed on macOS, most Linux |
| fswatch | Optional, for better watch mode on macOS (`brew install fswatch`) |

## Uninstall

```bash
pip uninstall cselab
rm -rf ~/.config/cselab
cselab disconnect  # close any active connection first
```
