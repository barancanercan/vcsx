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
        import json
        rules_dir = Path(output_dir) / ".windsurf" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

        # Core conventions rule (always apply)
        (rules_dir / "core-conventions.md").write_text(f"""---
alwaysApply: true
description: Core project conventions always applied
---

# Core Conventions for {ctx.project_name}

- **Language:** {ctx.language or "See tech stack"}
- **Framework:** {ctx.framework or "None"}
- **Type:** {ctx.project_type}

## Non-negotiable Rules
- Never commit `.env` files or secrets.
- Run `{ctx.formatter or "formatter"}` before every commit.
- Run `{ctx.linter or "linter"}` and fix all warnings.
- Write tests for new functionality.
- Keep PRs small and focused.
""", encoding="utf-8")

        # Testing conventions (auto-attached to test files)
        lang_glob = "**/*.py" if ctx.language == "python" else "**/*.ts,**/*.tsx,**/*.js"
        test_glob = "tests/**,**/*.test.*,**/*.spec.*"
        (rules_dir / "testing.md").write_text(f"""---
alwaysApply: false
globs: {test_glob}
description: Testing conventions — applied when working on test files
---

# Testing Conventions

- Test framework: {ctx.test_framework or "project standard"}
- Every new function must have at least one test.
- Tests should be independent — no shared mutable state.
- Use descriptive test names: `test_<function>_<scenario>_<expected>`.
- Mock external services; never hit real APIs in unit tests.
""", encoding="utf-8")

        # Security rules (always apply)
        (rules_dir / "security.md").write_text("""---
alwaysApply: true
description: Security guardrails — always enforced
---

# Security Rules

- NEVER hardcode API keys, passwords, or tokens.
- NEVER use `eval()` or `exec()` with user input.
- NEVER trust user input — validate and sanitize everything.
- NEVER log sensitive data (tokens, passwords, PII).
- Use environment variables for all secrets.
- Dependencies: check for known vulnerabilities before adding.
""", encoding="utf-8")

        # API conventions if applicable
        if ctx.project_type == "api":
            (rules_dir / "api-conventions.md").write_text("""---
alwaysApply: false
globs: src/routes/**,src/api/**,src/controllers/**
description: REST API design conventions
---

# API Conventions

- Use correct HTTP verbs: GET (read), POST (create), PUT/PATCH (update), DELETE.
- Return consistent response shapes: `{data, error, message}`.
- Use HTTP status codes correctly: 200, 201, 400, 401, 403, 404, 409, 422, 500.
- Validate all request body fields — return 422 with field-level errors.
- Paginate list endpoints: `{data, page, limit, total}`.
- Version the API: `/api/v1/`.
""", encoding="utf-8")

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
