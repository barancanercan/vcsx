# AI Tools Reference

vcsx supports 10 AI coding tools. Each generates production-ready configs automatically.

---

## Claude Code

**Category:** AI Editor  
**Config Files:** `CLAUDE.md`, `.claudeignore`, `.claude/skills/`, `.claude/hooks/`, `.claude/agents/`

Claude Code (Anthropic) is a terminal-based AI coding assistant. vcsx generates:

- **CLAUDE.md** — Project overview, quick commands, code style, forbidden actions
- **.claudeignore** — Context window optimization (same format as .gitignore)
- **.claude/skills/** — 20+ skill files (commit, deploy, review, test, security...)
- **.claude/hooks/** — Automated shell hooks (block destructive, auto-format, secret scan)
- **.claude/agents/** — Sub-agent definitions (security reviewer, test writer, researcher)

```bash
vcsx init -c claude-code
vcsx migrate claude-code  # Add missing .claudeignore + agents/
```

---

## Cursor

**Category:** AI Editor  
**Config Files:** `.cursorrules`, `.cursor/rules/*.mdc`

Cursor IDE with AI. vcsx generates both legacy and modern formats:

- **.cursorrules** — Legacy format (backward compatible)
- **.cursor/rules/*.mdc** — Modern scoped rules (description, globs, alwaysApply frontmatter)

```bash
vcsx init -c cursor
vcsx migrate cursor  # Upgrade .cursorrules → .cursor/rules/
```

---

## Windsurf

**Category:** AI Editor  
**Config Files:** `.windsurfrules`, `.windsurf/rules/*.md`

Windsurf IDE by Codeium. vcsx generates both legacy and v2 formats:

- **.windsurfrules** — Legacy format
- **.windsurf/rules/*.md** — New format with `alwaysApply` and glob support

```bash
vcsx init -c windsurf
vcsx migrate windsurf  # Upgrade to .windsurf/rules/ format
```

---

## Zed

**Category:** AI Editor  
**Config Files:** `.zed/settings.json`, `.zed/context.md`, `.zed/hooks.toml`

Zed editor with AI support.

```bash
vcsx init -c zed
```

---

## Aider

**Category:** Terminal AI  
**Config Files:** `.aider.conf.yaml`, `.aider.context.md`

Terminal-based AI pair programming. vcsx generates:

- **.aider.conf.yaml** — Valid Aider CLI flags (model, lint-cmd, test-cmd, read, map-tokens)
- **.aider.context.md** — Project context always loaded by Aider

> **Note:** vcsx uses only valid Aider CLI flags. Use `vcsx validate` to detect invalid configs.

```bash
vcsx init -c aider
vcsx validate  # Check for invalid .aider.conf.yaml keys
```

---

## Bolt

**Category:** Web AI  
**Config Files:** `.bolt/workspace.json`, `.bolt/setup.md`, `.bolt/prompts.md`

Bolt.new web-first AI development.

```bash
vcsx init -c bolt
```

---

## Codex

**Category:** Code Assist  
**Config Files:** `.openai/instructions.md`

OpenAI Codex CLI.

```bash
vcsx init -c codex
```

---

## Copilot

**Category:** Code Assist  
**Config Files:** `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`

GitHub Copilot. vcsx generates:

- **.github/copilot-instructions.md** — Main instructions
- **.github/instructions/** — Scoped instructions with `applyTo` frontmatter (code-style, testing, security)

```bash
vcsx init -c copilot
vcsx migrate copilot  # Add scoped instructions/
```

---

## Gemini CLI

**Category:** Terminal AI  
**Config Files:** `GEMINI.md`

Google Gemini CLI with 1M token context window. GEMINI.md includes project context, tech stack, and project-type-specific guidance.

> **Tip:** Also create `~/.gemini/GEMINI.md` for cross-project defaults.

```bash
vcsx init -c gemini
```

---

## AGENTS.md

**Category:** Universal  
**Config Files:** `AGENTS.md`

The Linux Foundation-stewarded universal AI coding standard. Supported by:
- OpenAI Codex CLI (primary config)
- Claude Code (fallback)
- Cursor, Gemini CLI, Aider, Continue.dev, OpenHands

```bash
vcsx init -c agents-md
vcsx update --tool agents-md  # Add to any existing project
```

---

## Multi-Tool Setup

All 10 tools can be configured simultaneously:

```bash
# Choose specific tools
vcsx init -c claude-code -c cursor -c gemini

# All tools at once
vcsx init --all-tools

# Add to existing project
vcsx update --tool gemini --tool agents-md
```

Tools don't conflict — each writes to its own files/directories.
