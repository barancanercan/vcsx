# vcsx Supported AI Tools

vcsx supports 8+ AI coding tools. Each tool gets generated configuration files, skills, hooks, and agents.

## Overview

| Tool | Category | Description |
|------|----------|-------------|
| Claude Code | AI Editor | Anthropic's CLI AI assistant |
| Cursor | AI Editor | AI-first code editor |
| Windsurf | AI Editor | Codeium's AI IDE |
| Zed | AI Editor | Zed editor with AI |
| Aider | Terminal AI | Terminal-based pair programming |
| Bolt | Web AI | Web-first AI development |
| Codex | Code Assist | OpenAI Codex CLI |
| Copilot | Code Assist | GitHub Copilot CLI |

## Generated Files by Tool

### Claude Code
- `CLAUDE.md` — Project conventions
- `.claude/settings.json` — Hook configuration
- `.claude/skills/*/SKILL.md` — 20+ skills
- `.claude/agents/*.md` — Specialized agents
- `.claude/hooks/*.sh` — 13 hook scripts

### Cursor
- `.cursorrules` — Cursor rules
- `.cursor/rules/*.md` — Cursor rule files

### Windsurf
- `.windsurfrules` — Windsurf rules
- `.windsurf/workspace.json` — Workspace config
- `.windsurf/context.md` — Context file

### Zed
- `.zed/settings.json` — Zed settings
- `.zed/context.md` — Context file

### Aider
- `.aider.conf.yaml` — Aider configuration
- `.aider.context.md` — Context file

### Bolt
- `.bolt/workspace.json` — Workspace config
- `.bolt/setup.md` — Setup file

### Codex
- `.openai/instructions.md` — Codex instructions

### Copilot
- `.github/copilot-instructions.md` — Copilot instructions
