<div align="center">

# 🧠 Vibe Coding Setup Expert (vcsx)

**One command. Production-ready AI coding environment.**

[![CI](https://github.com/vibe-coding-setup-expert/vcsx/actions/workflows/ci.yml/badge.svg)](https://github.com/vibe-coding-setup-expert/vcsx/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI Downloads](https://static.pepy.tech/badge/vcsx)](https://pepy.tech/projects/vcsx)

**Claude Code** · **Cursor** · **OpenAI Codex** · **GitHub Copilot**

</div>

---

## ✨ What It Does

`vcsx` is a CLI tool that generates **production-ready AI coding environments** in seconds. It asks you about your project, presents a plan, and then creates all the configuration files, skills, hooks, agents, and project scaffolding you need.

```bash
$ vcsx init
🔍 PHASE 1: DISCOVERY    → 3 rounds of smart questions
📋 PHASE 2: PLAN         → Review & approve the setup plan
🛠️ PHASE 3: BUILD       → All files generated automatically
```

## 🚀 Quick Start

```bash
# Install
pip install -e .

# Start interactive wizard (Claude Code by default)
vcsx init

# Generate for specific AI tools
vcsx init --cli claude-code     # Claude Code
vcsx init --cli cursor          # Cursor
vcsx init --cli codex           # OpenAI Codex
vcsx init --cli copilot         # GitHub Copilot

# Turkish or English
vcsx init --lang en

# Custom output directory
vcsx init -o ./my-project

# List all supported tools
vcsx list
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      vcsx init                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │ DISCOVERY│───→│   PLAN   │───→│ IMPLEMENTATION   │  │
│  │          │    │          │    │                  │  │
│  │ Smart Q&A│    │ Review & │    │ File Generation  │  │
│  │ 3 rounds │    │ Approve  │    │ via Generators   │  │
│  └──────────┘    └──────────┘    └──────────────────┘  │
│                                         │               │
│                    ┌────────────────────┼────────────┐  │
│                    │                    │            │  │
│              ┌─────▼─────┐    ┌────────▼──┐  ┌──────▼─┐│
│              │CLAUDE.md  │    │ Skills    │  │ Hooks  ││
│              │+ Scaffold │    │ + Agents  │  │+ Scripts││
│              └───────────┘    └───────────┘  └───────┘│
└─────────────────────────────────────────────────────────┘
```

## 📦 What Gets Generated

### Claude Code
| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project conventions, build commands, code style (<200 lines) |
| `.claude/skills/*/SKILL.md` | 8 reusable workflows with proper frontmatter |
| `.claude/settings.json` | Hook configurations for automation |
| `.claude/hooks/*.sh` | 4 executable hook scripts (security, format, lint, scan) |
| `.claude/agents/*.md` | 3 specialized subagents |

### Other AI Tools
| Tool | Files Generated |
|------|----------------|
| **Cursor** | `.cursorrules`, `.cursor/rules/*.md` |
| **Codex** | `.openai/instructions.md` |
| **Copilot** | `.github/copilot-instructions.md` |

## 🧩 Built-in Skills

| Skill | Description | Auto-Trigger |
|-------|-------------|:---:|
| `/commit-message` | Generates conventional commit messages from git diff | ✅ |
| `/pr-review` | Reviews PRs against team standards | ✅ |
| `/deploy` | Deployment checklist with pre-flight checks | ✅ |
| `/test-patterns` | Test writing conventions for your framework | ✅ |
| `/api-conventions` | REST API design patterns (API projects) | ✅ |
| `/auth-conventions` | Auth patterns and flows (auth projects) | ✅ |
| `/security-review` | Security vulnerability checklist | ✅ |
| `/refactor` | Code improvement suggestions | ✅ |

## 🔒 Built-in Hooks

| Hook | Event | What It Does |
|------|-------|-------------|
| Block destructive | `PreToolUse` (Bash) | Blocks `rm -rf`, `git push --force`, `DROP TABLE`, etc. |
| Auto-format | `PostToolUse` (Write/Edit) | Runs your formatter on every file change |
| Auto-lint | `PostToolUse` (Write/Edit) | Runs your linter after edits |
| Secret scan | `PostToolUse` (Write/Edit) | Detects API keys, passwords, tokens in code |

## 🔌 Plugin Architecture

Adding a new AI tool takes **3 steps**:

```python
# 1. Create src/vcsx/generators/new_tool.py
class NewToolGenerator(BaseGenerator):
    @property
    def name(self) -> str: return "new-tool"
    # ... implement 5 methods

# 2. Register in src/vcsx/generators/registry.py
CLI_TOOLS["new-tool"] = NewToolGenerator

# 3. Done!
# $ vcsx init --cli new-tool
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

## 📁 Project Structure

```
vcsx/
├── src/vcsx/
│   ├── cli.py              # Click CLI entry point
│   ├── discovery.py        # Interactive questionnaire engine
│   ├── planner.py          # Plan generation & confirmation
│   ├── implementation.py   # Orchestration layer
│   ├── core/
│   │   ├── context.py      # ProjectContext dataclass
│   │   ├── inference.py    # Tech stack → language/framework
│   │   └── validators.py   # Input validation
│   ├── generators/
│   │   ├── base.py         # Abstract BaseGenerator interface
│   │   ├── registry.py     # CLI tool registry (extensible)
│   │   ├── claude_code.py  # Claude Code generator (~500 lines)
│   │   ├── cursor.py       # Cursor generator
│   │   ├── codex.py        # OpenAI Codex generator
│   │   └── copilot.py      # GitHub Copilot generator
│   └── utils/
│       └── prompts.py      # TR/EN question bank
├── tests/
│   ├── test_core.py        # Core module tests
│   └── test_generators.py  # Generator tests (all 4 tools)
├── examples/               # Sample generated files
├── .github/workflows/      # CI/CD pipeline
└── pyproject.toml          # Package configuration
```

## 🧪 Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=vcsx --cov-report=term-missing

# Lint
ruff check src/

# Format
ruff format src/

# Install pre-commit hooks
pre-commit install
```

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- How to add new CLI tool generators
- Pull request guidelines
- Testing standards

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Made with ❤️ for the AI-assisted development community**

[Report a Bug](https://github.com/vibe-coding-setup-expert/vcsx/issues) · [Request a Feature](https://github.com/vibe-coding-setup-expert/vcsx/issues) · [Contributing Guide](CONTRIBUTING.md)

</div>
