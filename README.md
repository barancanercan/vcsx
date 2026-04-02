<div align="center">

<pre>
╔══════════════════╗
║       *          ║
║      vcsx        ║
║     v3.3.0       ║
╚══════════════════╝
</pre>

**Vibe Coding Setup Expert**

**One command. Production-ready AI coding environment.**

[![CI](https://github.com/vibe-coding-setup-expert/vcsx/actions/workflows/ci.yml/badge.svg)](https://github.com/vibe-coding-setup-expert/vcsx/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**Claude Code** · **Cursor** · **Windsurf** · **Zed** · **Aider** · **Bolt** · **Codex** · **Copilot**

</div>

---

## ✨ What It Does

`vcsx` is a CLI tool that generates **production-ready AI coding environments** in seconds. It supports 8+ AI coding tools and creates skills, hooks, agents, and project scaffolding automatically.

```bash
$ vcsx init
🔍 PHASE 0: AI Tool Selection   → Auto-detect + confirm
🔍 PHASE 1: Project Foundation   → Purpose, problem, user stories
🔍 PHASE 2: User Stories         → Detailed requirements
🔍 PHASE 3: Technical Details    → Smart branching
🔍 PHASE 4: Development Standards → Test, CI/CD, linting
🔍 PHASE 5: Claude Code Config   → Skills, hooks, automations
📋 PHASE 6: PLAN                 → Detailed review & approval
🛠️ PHASE 7: BUILD               → All files generated automatically
```

## 🚀 Installation (5 Methods)

### 1. PyPI (Recommended)
```bash
pip install vcsx
```

### 2. Standalone EXE
```bash
curl -L https://github.com/vibe-coding-setup-expert/vcsx/releases/latest/download/vcsx.exe -o vcsx.exe
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

## 📦 Supported AI Tools (8 Tools)

| Tool | Category | Files Generated |
|------|----------|-----------------|
| **Claude Code** | AI Editor | CLAUDE.md, skills, hooks, agents |
| **Cursor** | AI Editor | .cursorrules, .cursor/rules/*.mdc |
| **Windsurf** | AI Editor | .windsurfrules, workspace.json, conventions.md |
| **Zed** | AI Editor | .zed/settings.json, context.md, hooks.toml |
| **Aider** | Terminal AI | .aider.conf.yaml, context.md |
| **Bolt** | Web AI | .bolt/workspace.json, setup.md, prompts.md |
| **Codex** | Code Assist | .openai/instructions.md |
| **Copilot** | Code Assist | .github/copilot-instructions.md |

## 🎯 Discovery Process (v3.3 - Enhanced)

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
| `vcsx init` | Start interactive wizard |
| `vcsx list` | List all AI tools |
| `vcsx info <tool>` | Show tool details |
| `vcsx install <method>` | Show install instructions |
| `vcsx doctor` | Check installation |
| `vcsx plugins` | List plugins |
| `vcsx templates` | List templates |
| `vcsx templates:install <name>` | Install template |

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

[Report a Bug](https://github.com/vibe-coding-setup-expert/vcsx/issues) · [Request a Feature](https://github.com/vibe-coding-setup-expert/vcsx/issues) · [Contributing Guide](CONTRIBUTING.md)

</div>
