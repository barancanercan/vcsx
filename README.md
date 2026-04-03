<div align="center">

<pre>
╔══════════════════╗
║       *          ║
║      vcsx        ║
║     v5.0.0       ║
╚══════════════════╝
</pre>

**Vibe Coding Setup Expert**

**One command. Production-ready AI coding environment.**

[![CI](https://github.com/barancanercan/vcsx/actions/workflows/ci.yml/badge.svg)](https://github.com/barancanercan/vcsx/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**Claude Code** · **Cursor** · **Windsurf** · **Zed** · **Aider** · **Bolt** · **Codex** · **Copilot** · **Gemini CLI** · **AGENTS.md**

</div>

---

## ✨ What It Does

`vcsx` is a CLI tool that generates **production-ready AI coding environments** in seconds.

- **10 AI tools** supported: Claude Code, Cursor, Windsurf, Zed, Aider, Bolt, Codex, Copilot, Gemini CLI, AGENTS.md
- **22 production-quality skills** with full content (commit, deploy, security, performance, migration...)
- **10 project presets** (fastapi-postgres, saas-nextjs, flutter-app, rust-api...)
- **11+ languages** with inference (Python, TypeScript, Go, Rust, Kotlin, Swift, Dart, C#, PHP, Ruby, Java)
- **20 CLI commands** for every workflow stage

```bash
# Full interactive wizard
$ vcsx init

# Fast mode (2 questions, no wizard)
$ vcsx init --fast -c claude-code

# Multi-tool at once
$ vcsx init -c claude-code -c cursor -c gemini
$ vcsx init --all-tools

# Scaffold from template
$ vcsx new my-api --preset fastapi-postgres
$ vcsx new my-saas --preset saas-nextjs --tool claude-code --tool cursor

# Audit & maintain
$ vcsx audit --fix        # comprehensive check + auto-fix
$ vcsx validate           # best-practice validation
$ vcsx compare a/ b/      # diff configs between projects
$ vcsx search "deploy"    # search inside skill files
```

## 🚀 Installation (5 Methods)

### 1. PyPI (Recommended)
```bash
pip install vcsx
```

### 2. Standalone EXE
```bash
curl -L https://github.com/barancanercan/vcsx/releases/latest/download/vcsx.exe -o vcsx.exe
```

### 3. Homebrew
```bash
brew tap vcsx/tap
brew install vcsx
```

### 4. npx
```bash
npx vcsx init
```

### 5. npm
```bash
npm install -g vcsx
```

## 📦 Supported AI Tools (10 Tools)

| Tool | Category | Files Generated |
|------|----------|-----------------|
| **Claude Code** | AI Editor | CLAUDE.md, .claudeignore, skills, hooks, agents |
| **Cursor** | AI Editor | .cursorrules, .cursor/rules/*.mdc |
| **Windsurf** | AI Editor | .windsurfrules, .windsurf/rules/*.md (new format) |
| **Zed** | AI Editor | .zed/settings.json, context.md, hooks.toml |
| **Aider** | Terminal AI | .aider.conf.yaml, context.md |
| **Bolt** | Web AI | .bolt/workspace.json, setup.md, prompts.md |
| **Codex** | Code Assist | .openai/instructions.md |
| **Copilot** | Code Assist | .github/copilot-instructions.md, .github/instructions/*.md |
| **Gemini CLI** | Terminal AI | GEMINI.md (1M token context) |
| **AGENTS.md** | Universal | AGENTS.md (Linux Foundation standard, all tools) |

## 🎯 Discovery Process (v4.0 - Enhanced)

The discovery phase now includes **purpose-driven questions** for a more intelligent setup:

### Phase 0: AI Tool & Platform
- Auto-detects existing AI tool configuration
- Detects platform (Windows/macOS/Linux/WSL)

### Phase 1: Project Foundation (Most Important)
- **Purpose**: What do you aim to achieve?
- **Problem**: What problem does this project solve?
- Project name, description, tech stack
- Project type (web/api/cli/mobile/desktop/library)

### Phase 2: User Stories & Success Criteria
- **User Stories**: Detailed "As a user, I can..." format
- **Success Criteria**: Measurable metrics for success
- MVP features, target users

### Phase 3: Technical Details
- Smart branching: Auth → Auth method
- Hosting, external services, monorepo

### Phase 4: Development Standards
- Test level (none/unit/integration/full)
- CI/CD pipeline
- Formatter, linter

### Phase 5: Claude Code Configuration
- Recurring tasks (becomes skills)
- Forbidden actions (blocked by hooks)
- Automations

## 🗂️ Project Templates (10 Presets)

Use `vcsx new <name> --preset <template>` or `vcsx init --fast` to scaffold from a template.

| Preset | Stack | Type |
|--------|-------|------|
| `fastapi-postgres` | Python + FastAPI + PostgreSQL | API |
| `django-api` | Python + Django REST Framework | API |
| `react-typescript` | TypeScript + React + Vite | Web |
| `nextjs` | TypeScript + Next.js (App Router) | Web |
| `saas-nextjs` | TypeScript + Next.js + Tailwind + Prisma + Auth | SaaS |
| `go-api` | Go + Gin | API |
| `rust-cli` | Rust + Clap | CLI |
| `rust-api` | Rust + Axum + Tokio | API |
| `flutter-app` | Dart + Flutter | Mobile |
| `python-cli` | Python + Click + Rich | CLI |

```bash
vcsx new my-api --preset fastapi-postgres
vcsx new my-saas --preset saas-nextjs --tool claude-code --tool cursor
```

## 🧩 Generated Skills (20+)

| Skill | Category | Trigger |
|-------|----------|:--------:|
| `/commit-message` | Git | ✅ |
| `/pr-review` | Git | ✅ |
| `/squash` | Git | Manual |
| `/revert` | Git | Manual |
| `/deploy` | Deployment | Manual |
| `/rollback` | Deployment | Manual |
| `/migration` | Database | Manual |
| `/orm-conventions` | Database | Auto |
| `/query-optimization` | Database | Manual |
| `/docker-conventions` | DevOps | Auto |
| `/k8s-conventions` | DevOps | Auto |
| `/ci-cd-builder` | DevOps | Manual |
| `/test-patterns` | Testing | Auto |
| `/mutation-testing` | Testing | Manual |
| `/e2e-patterns` | Testing | Auto |
| `/api-conventions` | API | Auto |
| `/openapi-generator` | API | Manual |
| `/grpc-conventions` | API | Auto |
| `/security-review` | Security | ✅ |
| `/auth-conventions` | Security | Auto |
| `/refactor` | Quality | Manual |
| `/performance` | Quality | Manual |
| `/debt-analyzer` | Quality | Manual |

## 🔌 Generated Hooks (13)

### PreToolUse
- `block_destructive` — Blocks dangerous commands
- `validate_syntax` — Validates code syntax
- `check_permissions` — Warns on permission changes

### PostToolUse
- `auto_format` — Auto-formats on save
- `auto_lint` — Runs linter after edits
- `type_check` — Type checking
- `secret_scan` — Scans for secrets

### SessionStart
- `check_env` — Checks environment variables
- `check_deps` — Verifies dependencies
- `git_status` — Shows git status

### Stop
- `run_tests` — Runs test suite
- `cleanup_temp` — Cleans temp files
- `commit_prompt` — Prompts for commit

## 📋 vcsx Commands

| Command | Description |
|---------|-------------|
| `vcsx init` | Start interactive wizard (single tool) |
| `vcsx init -c claude-code -c cursor` | Set up multiple tools at once |
| `vcsx init --all-tools` | Set up all 10 tools at once |
| `vcsx update` | Add missing AI configs to existing project |
| `vcsx update --dry-run` | Preview what would be added |
| `vcsx update --tool gemini` | Add a specific tool config |
| `vcsx update --auto` | Auto-apply all detected upgrades |
| `vcsx list` | List all AI tools |
| `vcsx info <tool>` | Show tool details and generated files |
| `vcsx install <method>` | Show install instructions |
| `vcsx doctor` | Check installation + detect project AI tools |
| `vcsx doctor --dir /path/to/project` | Check a specific project |
| **Quality & Analysis** | |
| `vcsx check` | Score AI config quality (0-100%) |
| `vcsx check ~/my-project --json` | JSON output for CI integration |
| `vcsx validate` | Validate configs for best practices |
| `vcsx audit` | Comprehensive audit: check + validate + stats |
| `vcsx audit --fix` | Audit and auto-fix safe issues |
| `vcsx stats` | Count skills, hooks, agents, rules |
| `vcsx search <query>` | Search inside AI config files |
| `vcsx compare <a> <b>` | Compare configs between two projects |
| **Scaffolding** | |
| `vcsx new my-app` | Scaffold new project without wizard |
| `vcsx new my-api --type api --lang python` | Scaffold typed project |
| `vcsx new my-app --preset fastapi-postgres` | Use a template preset |
| `vcsx generate <tool>` | Generate one tool's config files directly |
| **Migration & Maintenance** | |
| `vcsx migrate windsurf` | Migrate .windsurfrules → .windsurf/rules/ |
| `vcsx migrate cursor` | Migrate .cursorrules → .cursor/rules/*.mdc |
| `vcsx export` | Export all AI configs to ZIP archive |
| `vcsx changelog` | Show release changelog |
| `vcsx completion bash` | Print bash shell completion setup |
| `vcsx plugins` | List plugins |
| `vcsx templates` | List available templates (10 presets) |

## 🧪 Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/

# Format
ruff format src/

# Build wheel
python -m build

# Build standalone exe
pyinstaller src/vcsx/cli.py --name vcsx --onefile
```

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

MIT License — see [LICENSE](LICENSE).

---

<div align="center">

**Made with ❤️ for the AI-assisted development community**

[Report a Bug](https://github.com/barancanercan/vcsx/issues) · [Request a Feature](https://github.com/barancanercan/vcsx/issues) · [Contributing Guide](CONTRIBUTING.md)

</div>
