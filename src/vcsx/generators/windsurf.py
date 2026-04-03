"""Windsurf AI generator — produces rules/workspace config."""

from pathlib import Path

from vcsx.core.context import ProjectContext
from vcsx.generators.base import BaseGenerator


class WindsurfGenerator(BaseGenerator):
    """Generates a complete Windsurf IDE setup."""

    @property
    def name(self) -> str:
        return "windsurf"

    @property
    def output_files(self) -> list[str]:
        return [
            ".windsurfrules",
            ".windsurf/workspace.json",
            ".windsurf/context.md",
        ]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        """Generate .windsurfrules file."""
        content = f"""# {ctx.project_name} — Windsurf Rules

## Project Context
{ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack}."}

## Architecture
- **Type**: {ctx.project_type}
- **Language**: {ctx.language}
- **Framework**: {ctx.framework or "None"}
- **Hosting**: {ctx.hosting or "TBD"}

## Quick Commands

### Setup
```
{_get_setup_cmd(ctx)}
```

### Build
```
{_get_build_cmd(ctx)}
```

### Test
```
{_get_test_cmd(ctx)}
```

## Code Style
{chr(10).join(_get_style_rules(ctx))}

## Rules
- NEVER commit secrets or API keys
- Run tests before committing
- Follow existing code patterns
- Keep changes focused and atomic
"""
        (Path(output_dir) / ".windsurfrules").write_text(content, encoding="utf-8")

        # New format: .windsurf/rules/*.md (MDC-style, scoped rules)
        self._generate_windsurf_rules(ctx, output_dir)

        return content

    def _generate_windsurf_rules(self, ctx: ProjectContext, output_dir: str) -> None:
        """Generate .windsurf/rules/ directory with scoped rule files (new format).

        Windsurf v2+ uses .windsurf/rules/*.md alongside legacy .windsurfrules.
        Rules support metadata: alwaysApply, glob patterns, description.
        """
        rules_dir = Path(output_dir) / ".windsurf" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

        lang = (ctx.language or "").lower()
        fmt = ctx.formatter or ("ruff format" if lang == "python" else "prettier")
        lint = ctx.linter or ("ruff check" if lang == "python" else "eslint")
        test_fw = ctx.test_framework or ("pytest" if lang == "python" else "vitest")

        # Core conventions rule (always apply)
        (rules_dir / "core-conventions.md").write_text(
            f"""---
alwaysApply: true
description: Core project conventions always applied
---

# Core Conventions — {ctx.project_name}

## Project
- **Language:** {ctx.language or "See tech stack"}
- **Framework:** {ctx.framework or "None"}
- **Type:** {ctx.project_type}
- **Test Framework:** {test_fw}

## Non-Negotiable Rules
- NEVER commit `.env` files, API keys, or tokens.
- Run `{fmt}` before every commit.
- Run `{lint}` and fix ALL warnings before submitting.
- Write tests for new functionality — no test, no merge.
- Keep PRs small and focused — one logical change per PR.
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`

## Code Quality
- Functions: max 30 lines. If longer, extract helper.
- Nesting: max 3 levels. If deeper, invert conditions or extract.
- No magic numbers — use named constants.
- No `# TODO` without a ticket/issue reference.

## Git Workflow
- Never force-push to `main` or `develop`.
- Always rebase feature branches before merging.
- Delete feature branches after merge.
""",
            encoding="utf-8",
        )

        # Testing conventions (auto-attached to test files)
        if lang == "python":
            test_glob = "tests/**,test_*.py,*_test.py"
        else:
            test_glob = "tests/**,**/*.test.*,**/*.spec.*,**/*.test.ts,**/*.spec.ts"

        (rules_dir / "testing.md").write_text(
            f"""---
alwaysApply: false
globs: {test_glob}
description: Testing conventions — applied when working on test files
---

# Testing Conventions

## Framework: {test_fw}

## Structure: AAA Pattern
```
Arrange → Act → Assert
```
Every test must follow this structure.

## Naming
`test_<function>_<scenario>_<expected>`
Examples:
- `test_create_user_valid_email_returns_id`
- `test_login_wrong_password_returns_401`

## Rules
- Tests must be independent — no shared mutable state between tests.
- Mock ALL external dependencies (database, HTTP, filesystem, time).
- Test both happy path AND error cases.
- Use fixtures/factories for test data — no hardcoded magic values.
- One assertion focus per test (can have multiple related asserts).

## Coverage
- Critical business logic: 100%
- API endpoints: test all success + error responses
- Do NOT test library internals or trivial getters/setters
""",
            encoding="utf-8",
        )

        # Security rules (always apply)
        (rules_dir / "security.md").write_text(
            r"""---
alwaysApply: true
description: Security guardrails — always enforced
---

# Security Rules

## Absolute Prohibitions
- NEVER hardcode API keys, passwords, tokens, or secrets in code.
- NEVER use `eval()`, `exec()`, or dynamic code execution with user input.
- NEVER trust user input — validate and sanitize at API boundaries.
- NEVER log tokens, passwords, session IDs, or PII.
- NEVER return stack traces or internal error details to API clients.

## Required Practices
- All secrets → environment variables (never in source code).
- All user input → validated before use (type, length, format).
- SQL queries → parameterized (never f-strings in queries).
- File paths → sanitized (no `../` traversal).
- Auth → checked on every protected endpoint, not just at login.

## Before Merging Any PR
- Run secret scan: `git log --all -S "password\|api_key\|token" --oneline`
- Check for hardcoded URLs, credentials, or environment-specific values.
""",
            encoding="utf-8",
        )

        # API conventions if applicable
        if ctx.project_type == "api":
            (rules_dir / "api-conventions.md").write_text(
                """---
alwaysApply: false
globs: src/routes/**,src/api/**,src/controllers/**,**/router*,**/endpoint*
description: REST API design conventions — applied to route/controller files
---

# API Conventions

## URL Design
- Plural nouns: `/v1/users`, `/v1/orders`
- Kebab-case: `/v1/user-profiles`
- Never verbs: `/v1/users` not `/v1/getUsers`
- Always versioned: `/v1/...`

## HTTP Methods & Codes
| Action | Method | Success |
|--------|--------|---------|
| Read | GET | 200 |
| Create | POST | 201 |
| Update | PATCH/PUT | 200 |
| Delete | DELETE | 204 |
| Not found | — | 404 |
| Validation error | — | 422 |
| Auth required | — | 401 |
| Forbidden | — | 403 |

## Response Shape
```json
{ "data": {...}, "meta": { "requestId": "..." } }
```

## Error Shape
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [] } }
```

## Rules
- Paginate ALL list endpoints.
- Validate ALL input at the boundary — don't let invalid data reach business logic.
- Return consistent error shapes across all endpoints.
""",
                encoding="utf-8",
            )

        # Data pipeline conventions
        if ctx.project_type in ("data-pipeline", "ml-model"):
            (rules_dir / "data-conventions.md").write_text(
                """---
alwaysApply: false
globs: src/**,scrapers/**,pipelines/**,processors/**
description: Data pipeline conventions
---

# Data Pipeline Conventions

## Memory Management
- Process data in chunks — NEVER load full datasets into memory.
- Use generators/iterators for large datasets.
- SQLite: always `PRAGMA journal_mode=WAL; PRAGMA synchronous=OFF;`

## Idempotency
- Every pipeline step must be safe to run twice.
- Use upsert, not insert, when possible.
- Record processing state to allow resume on failure.

## Data Quality
- Validate data at ingestion (schema, types, required fields).
- Log invalid records — don't silently drop them.
- Track record counts at each pipeline stage.

## Performance
- Add indexes before running large queries.
- Use `EXPLAIN QUERY PLAN` to verify SQLite uses indexes.
- Commit in batches (every 1000-10000 rows, not every row).
""",
                encoding="utf-8",
            )

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate Windsurf-specific skill files."""
        windsurf_dir = Path(output_dir) / ".windsurf"
        windsurf_dir.mkdir(parents=True, exist_ok=True)

        workspace = {
            "version": "1.0",
            "project": ctx.project_name,
            "language": ctx.language,
            "framework": ctx.framework,
            "testFramework": ctx.test_framework,
            "buildCommand": _get_build_cmd(ctx),
            "testCommand": _get_test_cmd(ctx),
            "lintCommand": f"{ctx.linter} src/",
            "formatCommand": f"{ctx.formatter} src/",
        }

        import json

        (windsurf_dir / "workspace.json").write_text(
            json.dumps(workspace, indent=2), encoding="utf-8"
        )

        context_content = f"""# Project Context

This is a {ctx.project_type} project using {ctx.tech_stack}.

## Directory Structure
```
{ctx.project_name}/
├── src/
├── tests/
└── (config files)
```

## Key Files
- `CLAUDE.md` - Main project conventions
- `.windsurfrules` - Windsurf-specific rules

## Important Notes
- Tests are required before commit
- No secrets in code
- Follow existing patterns
"""
        (windsurf_dir / "context.md").write_text(context_content, encoding="utf-8")

        conventions_content = f"""# Project Conventions

## Architecture
- **Project Type**: {ctx.project_type}
- **Language**: {ctx.language}
- **Framework**: {ctx.framework or "N/A"}
- **Testing**: {ctx.test_framework or "N/A"}
- **Hosting**: {ctx.hosting or "TBD"}

## Development Commands
- **Setup**: {_get_setup_cmd(ctx)}
- **Build**: {_get_build_cmd(ctx)}
- **Test**: {_get_test_cmd(ctx)}
- **Lint**: {ctx.linter} src/
- **Format**: {ctx.formatter} src/

## Code Style
{chr(10).join(_get_style_rules(ctx))}

## Quality Gates
- All tests must pass before commit
- Linting must pass
- No secrets or API keys in code
- Follow existing code patterns
- Keep changes atomic and focused

## File Patterns
- Source files: `src/**/*.{_get_ext(ctx)}`
- Test files: `tests/**/*.{_get_ext(ctx)}`
- Config files: `.env`, `*.config.js`, `pyproject.toml`

## Best Practices
1. Write tests for new features
2. Use type hints where applicable
3. Keep functions small and focused
4. Document complex logic
5. Review changes before committing
"""
        (windsurf_dir / "conventions.md").write_text(conventions_content, encoding="utf-8")

        return ["workspace.json", "context.md", "conventions.md"]

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        """Generate hooks configuration."""
        return {}

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate agent definitions."""
        return []

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate project scaffold."""
        return []


def _get_setup_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm install",
        "javascript": "npm install",
        "python": "pip install -r requirements.txt",
        "go": "go mod tidy",
    }.get(ctx.language, "npm install")


def _get_build_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm run build",
        "javascript": "npm run build",
        "python": "python -m compileall src/",
        "go": "go build ./...",
    }.get(ctx.language, "npm run build")


def _get_test_cmd(ctx: ProjectContext) -> str:
    return {
        "vitest": "npx vitest run",
        "jest": "npx jest",
        "pytest": "pytest",
        "go test": "go test ./...",
    }.get(ctx.test_framework or "pytest", "npm test")


def _get_style_rules(ctx: ProjectContext) -> list[str]:
    rules = {
        "typescript": [
            "Use TypeScript strict mode",
            "Prefer const over let",
            "Type all function parameters",
            "Use async/await over raw promises",
        ],
        "python": [
            "Follow PEP 8 style guide",
            "Use type hints",
            "snake_case for variables",
            "Docstrings for public functions",
        ],
    }
    return rules.get(ctx.language, ["Follow language idioms"])


def _get_ext(ctx: ProjectContext) -> str:
    exts = {
        "typescript": "ts",
        "javascript": "js",
        "python": "py",
        "go": "go",
    }
    return exts.get(ctx.language, "*")
