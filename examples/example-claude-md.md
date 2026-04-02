# Example: Generated CLAUDE.md for a Python FastAPI Project
# This is what vcsx generates when you run: vcsx init --cli claude-code

# MyAPI — CLAUDE.md

## Project Overview
A REST API built with FastAPI for managing user data and authentication.

## Quick Commands

### Setup
```bash
pip install -r requirements.txt
```

### Build
```bash
python -m compileall src/
```

### Lint & Format
```bash
ruff check src/
ruff format src/
```

### Test
```bash
pytest
```

### Run Single Test
```bash
pytest tests/test_file.py::test_name -v
```

## Code Style

- Follow PEP 8 style guide
- Use type hints for all public functions
- `snake_case` for variables/functions, `PascalCase` for classes
- Prefer f-strings over .format()
- Use dataclasses for simple data containers
- Docstrings for all public functions and classes

## Architecture

- **Type**: api
- **Language**: python
- **Framework**: FastAPI
- **Hosting**: Railway
- **Auth**: JWT

## Absolute Rules

- NEVER commit secrets or API keys
- NEVER run destructive commands without explicit confirmation
- ALWAYS run tests before committing
- ALWAYS follow existing code patterns
- Keep CLAUDE.md under 200 lines — move domain knowledge to skills

## Skills (Auto-Triggered)

- `/commit-message` — Generate conventional commit messages
- `/pr-review` — Review against team standards
- `/deploy` — Deployment checklist
- `/api-conventions` — REST API design patterns
- `/test-patterns` — Test writing conventions

## Hooks (Deterministic)

- PreToolUse: Blocks destructive commands (rm -rf, git push --force)
- PostToolUse: Auto-runs ruff format on file changes
- PostToolUse: Auto-runs ruff check after edits
