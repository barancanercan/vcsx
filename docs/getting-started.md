# Getting Started with vcsx

## What is vcsx?

vcsx (Vibe Coding Setup Expert) is a CLI tool that generates **production-ready AI coding environments** in seconds.
It supports 10 AI coding tools and creates skills, hooks, agents, config files, and project scaffolding automatically.

## Installation

### Method 1: PyPI (Recommended)
```bash
pip install vcsx
vcsx init
```

### Method 2: Standalone Executable
```bash
# Download from GitHub Releases
curl -L https://github.com/barancanercan/vcsx/releases/latest/download/vcsx.exe -o vcsx.exe
./vcsx.exe init
```

### Method 3: Homebrew
```bash
brew tap vcsx/tap
brew install vcsx
```

### Method 4: npx
```bash
npx vcsx init
```

### Method 5: npm
```bash
npm install -g vcsx
vcsx init
```

## Quick Start

### Single tool setup (interactive wizard)
```bash
vcsx init
```

### Multi-tool setup (no wizard needed)
```bash
# Set up Claude Code + Cursor + Gemini in one shot
vcsx init -c claude-code -c cursor -c gemini

# Set up all 10 tools at once
vcsx init --all-tools
```

### Scaffold a new project
```bash
vcsx new my-api --type api --lang python
vcsx new my-app --type web --lang typescript --tool cursor
```

### Add configs to an existing project
```bash
vcsx update --tool gemini      # Add Gemini CLI config
vcsx update --tool agents-md   # Add AGENTS.md universal standard
vcsx update --dry-run          # Preview changes first
```

## Command Overview

| Command | Description |
|---------|-------------|
| `vcsx init` | Interactive wizard (single tool) |
| `vcsx init -c tool1 -c tool2` | Set up multiple tools at once |
| `vcsx init --all-tools` | All 10 tools |
| `vcsx new <name>` | Scaffold new project without wizard |
| `vcsx update` | Add missing configs to existing project |
| `vcsx check` | Score AI config quality (0-100%) |
| `vcsx validate` | Validate configs for best practices |
| `vcsx migrate <tool>` | Migrate old format to new format |
| `vcsx doctor` | Diagnose installation + detect project tools |
| `vcsx list` | List all supported AI tools |
| `vcsx info <tool>` | Show tool details + generated files |
| `vcsx completion <shell>` | Shell tab completion setup |

## Supported AI Tools

| Tool | Config Files |
|------|-------------|
| `claude-code` | CLAUDE.md, .claudeignore, .claude/skills/, .claude/hooks/, .claude/agents/ |
| `cursor` | .cursorrules, .cursor/rules/*.mdc |
| `windsurf` | .windsurfrules, .windsurf/rules/*.md |
| `zed` | .zed/settings.json, .zed/context.md, .zed/hooks.toml |
| `aider` | .aider.conf.yaml, .aider.context.md |
| `bolt` | .bolt/workspace.json, .bolt/setup.md, .bolt/prompts.md |
| `codex` | .openai/instructions.md |
| `copilot` | .github/copilot-instructions.md, .github/instructions/ |
| `gemini` | GEMINI.md |
| `agents-md` | AGENTS.md (universal standard) |

## Next Steps

- See [AI Tools Reference](ai-tools.md) for detailed per-tool documentation
- See [Skills Guide](skills.md) for using and customizing skill files
- See [Hooks Guide](hooks.md) for automation and safety hooks
