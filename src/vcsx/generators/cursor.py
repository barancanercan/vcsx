"""Cursor generator — produces .cursorrules and .cursor/rules/."""

import json
from pathlib import Path

from vcsx.core.context import ProjectContext
from vcsx.core.inference import infer_formatter, infer_linter, infer_test_framework
from vcsx.generators.base import BaseGenerator


class CursorGenerator(BaseGenerator):
    """Generates a complete Cursor setup."""

    @property
    def name(self) -> str:
        return "cursor"

    @property
    def output_files(self) -> list[str]:
        return [".cursorrules", ".cursor/rules/*.md"]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        """Generate .cursorrules file."""
        lines = [
            f"# {ctx.project_name} — Cursor Rules",
            "",
            "## Project Overview",
            ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack}.",
            "",
            "## Commands",
            "```bash",
            f"# Setup: {_get_setup_cmd(ctx)}",
            f"# Build: {_get_build_cmd(ctx)}",
            f"# Test: {_get_test_cmd(ctx)}",
            f"# Lint: {ctx.linter or infer_linter(ctx.language)} src/",
            f"# Format: {ctx.formatter or infer_formatter(ctx.language)} src/",
            "```",
            "",
            "## Code Style",
        ]
        lines.extend(_get_style_rules(ctx))
        lines.extend(
            [
                "",
                "## Architecture",
                f"- **Type**: {ctx.project_type}",
                f"- **Language**: {ctx.language}",
                f"- **Framework**: {ctx.framework or 'None'}",
                "",
                "## Rules",
                "- NEVER commit secrets or API keys",
                "- ALWAYS run tests before committing",
                "- ALWAYS follow existing code patterns",
                "- Keep functions small and single-purpose",
            ]
        )

        content = "\n".join(lines)
        (Path(output_dir) / ".cursorrules").write_text(content, encoding="utf-8")
        return content

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate .cursor/rules/ files."""
        rules_dir = Path(output_dir) / ".cursor" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        created = []

        created.append(_rule_commit_message(rules_dir))
        created.append(_rule_pr_review(rules_dir))
        created.append(_rule_test_patterns(rules_dir, ctx))

        if ctx.project_type == "api":
            created.append(_rule_api_conventions(rules_dir))

        return created

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        """Cursor doesn't have hooks — return empty."""
        return {"note": "Cursor hooks not supported — use pre-commit hooks instead"}

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Cursor doesn't have agents — return empty."""
        return []

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate project scaffold."""
        created = []
        created.append(_scaffold_gitignore(output_dir, ctx))
        created.append(_scaffold_readme(output_dir, ctx))
        created.append(_scaffold_env_example(output_dir, ctx))

        if ctx.language in ("typescript", "javascript"):
            created.append(_scaffold_tsconfig(output_dir))
            created.append(_scaffold_package_json(output_dir, ctx))
        elif ctx.language == "python":
            created.append(_scaffold_requirements(output_dir, ctx))
            created.append(_scaffold_pyproject(output_dir, ctx))
        elif ctx.language == "go":
            created.append(_scaffold_go_mod(output_dir, ctx))

        created.append(_scaffold_source_dirs(output_dir, ctx))
        return created


# ─── Rule Templates ──────────────────────────────────────────────────────────


def _rule_commit_message(rules_dir: Path) -> str:
    d = rules_dir / "commit-message.md"
    content = """---
description: Generate conventional commit messages
---

# Commit Message Rules

Format: `<type>(<scope>): <description>`

## Types
- `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Process
1. Run `git diff --cached`
2. Determine type from changes
3. Generate concise description (max 72 chars)
4. Suggest separate commits if multiple types
"""
    d.write_text(content, encoding="utf-8")
    return "commit-message"


def _rule_pr_review(rules_dir: Path) -> str:
    d = rules_dir / "pr-review.md"
    content = """---
description: Review PRs against team standards
---

# PR Review Rules

## Checklist
- [ ] Code follows style guidelines
- [ ] No secrets committed
- [ ] Tests cover new functionality
- [ ] Error handling is appropriate
- [ ] Documentation updated

## Process
1. Run `git diff main...HEAD`
2. Check each file against checklist
3. Report findings with line references
"""
    d.write_text(content, encoding="utf-8")
    return "pr-review"


def _rule_test_patterns(rules_dir: Path, ctx: ProjectContext) -> str:
    d = rules_dir / "test-patterns.md"
    content = f"""---
description: Test writing patterns using {ctx.test_framework or infer_test_framework(ctx.language)}
---

# Test Patterns

## Framework: {ctx.test_framework or infer_test_framework(ctx.language)}

## Structure
1. Arrange — Set up test data
2. Act — Execute code under test
3. Assert — Verify outcome

## Guidelines
- Test behavior, not implementation
- One assertion per test when possible
- Descriptive test names
- Mock external dependencies
"""
    d.write_text(content, encoding="utf-8")
    return "test-patterns"


def _rule_api_conventions(rules_dir: Path) -> str:
    d = rules_dir / "api-conventions.md"
    content = """---
description: REST API design patterns
---

# API Conventions

- kebab-case for paths: `/api/user-profiles`
- Nouns not verbs: `/api/users`
- Version in URL: `/api/v1/users`
- Plural nouns for collections
- GET/POST/PUT/PATCH/DELETE for CRUD
"""
    d.write_text(content, encoding="utf-8")
    return "api-conventions"


# ─── Scaffold (reused from claude_code) ──────────────────────────────────────


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
    if ctx.test_level == "none":
        return "# No tests configured"
    return {
        "vitest": "npx vitest run",
        "jest": "npx jest",
        "pytest": "pytest",
        "go test": "go test ./...",
    }.get(ctx.test_framework or infer_test_framework(ctx.language), "npm test")


def _get_style_rules(ctx: ProjectContext) -> list[str]:
    rules = {
        "typescript": [
            "- Use TypeScript strict mode",
            "- Prefer `const` over `let`",
            "- Named exports over default exports",
            "- Type all function parameters",
            "- camelCase for variables, PascalCase for types",
        ],
        "python": [
            "- Follow PEP 8",
            "- Type hints for all public functions",
            "- `snake_case` for variables, `PascalCase` for classes",
            "- Prefer f-strings",
            "- Docstrings for all public functions",
        ],
        "go": [
            "- Follow `gofmt`",
            "- `camelCase` for local, `PascalCase` for exported",
            "- Check errors immediately",
            "- Package names: lowercase, single word",
        ],
    }
    return rules.get(ctx.language, ["- Follow language idioms"])


def _scaffold_gitignore(output_dir: str, ctx: ProjectContext) -> str:
    lines = [
        "# Dependencies",
        "node_modules/",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        "vendor/",
        "",
        "# Build",
        "dist/",
        "build/",
        "",
        "# Environment",
        ".env",
        ".env.local",
        "!.env.example",
        "",
        "# IDE",
        ".idea/",
        ".vscode/",
        "",
        "# OS",
        ".DS_Store",
        "Thumbs.db",
        "",
        "# Coverage",
        "coverage/",
        "htmlcov/",
    ]
    p = Path(output_dir) / ".gitignore"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ".gitignore"


def _scaffold_readme(output_dir: str, ctx: ProjectContext) -> str:
    content = f"""# {ctx.project_name}

{ctx.description or f"A {ctx.project_type} project."}

## Setup
```bash
{_get_setup_cmd(ctx)}
```

## Test
```bash
{_get_test_cmd(ctx)}
```

## Architecture
- **Type**: {ctx.project_type}
- **Language**: {ctx.language}
- **Framework**: {ctx.framework or "None"}
"""
    p = Path(output_dir) / "README.md"
    p.write_text(content, encoding="utf-8")
    return "README.md"


def _scaffold_env_example(output_dir: str, ctx: ProjectContext) -> str:
    lines = [
        "# Application",
        "NODE_ENV=development",
        "PORT=3000",
        "",
        "# Database",
        "DATABASE_URL=postgresql://user:password@localhost:5432/dbname",
    ]
    if ctx.auth_needed:
        lines.extend(["", "# Auth", "JWT_SECRET=your-secret-key-here"])
    p = Path(output_dir) / ".env.example"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ".env.example"


def _scaffold_tsconfig(output_dir: str) -> str:
    content = '{"compilerOptions":{"target":"ES2022","module":"ESNext","moduleResolution":"bundler","strict":true,"esModuleInterop":true,"skipLibCheck":true,"forceConsistentCasingInFileNames":true,"resolveJsonModule":true,"isolatedModules":true,"noEmit":true,"outDir":"./dist","rootDir":"./src","baseUrl":".","paths":{"@/*":["src/*"]}},"include":["src/**/*"],"exclude":["node_modules","dist"]}'
    p = Path(output_dir) / "tsconfig.json"
    p.write_text(content, encoding="utf-8")
    return "tsconfig.json"


def _scaffold_package_json(output_dir: str, ctx: ProjectContext) -> str:

    content = {
        "name": ctx.project_name,
        "version": "0.1.0",
        "type": "module",
        "scripts": {
            "dev": "echo 'Add dev command'",
            "build": "echo 'Add build command'",
            "test": "npx vitest run",
            "lint": "eslint src/",
            "format": "prettier --write src/",
        },
        "devDependencies": {
            "eslint": "^9.0.0",
            "prettier": "^3.0.0",
            "typescript": "^5.0.0",
            "vitest": "^2.0.0",
        },
    }
    p = Path(output_dir) / "package.json"
    p.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    return "package.json"


def _scaffold_requirements(output_dir: str, ctx: ProjectContext) -> str:
    lines = [
        "# Core",
        "# Add dependencies",
        "",
        "# Dev",
        "pytest>=7.0",
        "ruff>=0.1.0",
        "mypy>=1.0",
    ]
    p = Path(output_dir) / "requirements.txt"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "requirements.txt"


def _scaffold_pyproject(output_dir: str, ctx: ProjectContext) -> str:
    content = f"""[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{ctx.project_name}"
version = "0.1.0"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
"""
    p = Path(output_dir) / "pyproject.toml"
    p.write_text(content, encoding="utf-8")
    return "pyproject.toml"


def _scaffold_go_mod(output_dir: str, ctx: ProjectContext) -> str:
    content = f"module {ctx.project_name}\n\ngo 1.21\n"
    p = Path(output_dir) / "go.mod"
    p.write_text(content, encoding="utf-8")
    return "go.mod"


def _scaffold_source_dirs(output_dir: str, ctx: ProjectContext) -> str:
    base = Path(output_dir)
    dirs = ["src", "tests"]
    if ctx.project_type == "api":
        dirs.extend(
            [
                "src/api",
                "src/models",
                "src/middleware",
                "tests/unit",
                "tests/integration",
            ]
        )
    elif ctx.project_type == "web":
        dirs.extend(
            [
                "src/components",
                "src/pages",
                "src/utils",
                "tests/unit",
                "tests/integration",
            ]
        )
    elif ctx.project_type == "cli":
        dirs.extend(["src/commands", "src/utils", "tests/unit"])
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
    if ctx.language == "python":
        for d in dirs:
            init_file = base / d / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")
    return "source directories"
