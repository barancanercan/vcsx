"""GitHub Copilot generator — produces .github/copilot-instructions.md."""

from pathlib import Path

from vcsx.core.context import ProjectContext
from vcsx.core.inference import infer_formatter, infer_linter, infer_test_framework
from vcsx.generators.base import BaseGenerator


class CopilotGenerator(BaseGenerator):
    """Generates a GitHub Copilot setup."""

    @property
    def name(self) -> str:
        return "copilot"

    @property
    def output_files(self) -> list[str]:
        return [".github/copilot-instructions.md"]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        """Generate .github/copilot-instructions.md."""
        lines = [
            f"# {ctx.project_name} — Copilot Instructions",
            "",
            "## Project Overview",
            ctx.description or f"A {ctx.project_type} project.",
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
                "- NEVER commit secrets",
                "- ALWAYS run tests before committing",
                "- ALWAYS follow existing patterns",
            ]
        )

        content = "\n".join(lines)
        d = Path(output_dir) / ".github"
        d.mkdir(parents=True, exist_ok=True)
        (d / "copilot-instructions.md").write_text(content, encoding="utf-8")

        # New: scoped instructions (.github/instructions/*.instructions.md)
        self._generate_scoped_instructions(ctx, output_dir)

        return content

    def _generate_scoped_instructions(self, ctx: ProjectContext, output_dir: str) -> None:
        """Generate .github/instructions/ scoped instruction files.

        GitHub Copilot (2025+) supports scoped instructions with frontmatter:
        - applyTo: glob pattern for files this applies to
        - description: what this instruction set covers
        """
        instructions_dir = Path(output_dir) / ".github" / "instructions"
        instructions_dir.mkdir(parents=True, exist_ok=True)

        lang = (ctx.language or "").lower()

        # Code style instructions
        glob_pattern = "**/*.py" if lang == "python" else "**/*.ts,**/*.tsx,**/*.js,**/*.jsx"
        fmt = ctx.formatter or infer_formatter(ctx.language)
        lint = ctx.linter or infer_linter(ctx.language)
        (instructions_dir / "code-style.instructions.md").write_text(
            f"""---
applyTo: "{glob_pattern}"
---

# Code Style

- Format with `{fmt}` before committing.
- Run `{lint}` and fix all warnings.
- Keep functions small and focused — single responsibility.
- Prefer explicit over implicit.
- Use descriptive variable names.
{"- Use type hints on all public functions." if lang == "python" else "- Use explicit TypeScript types; avoid `any`."}
""",
            encoding="utf-8",
        )

        # Testing instructions
        test_glob = "tests/**,**/*.test.*,**/*.spec.*,test_*.py,*_test.py"
        test_fw = ctx.test_framework or infer_test_framework(ctx.language)
        (instructions_dir / "testing.instructions.md").write_text(
            f"""---
applyTo: "{test_glob}"
---

# Testing Guidelines

- Test framework: `{test_fw}`
- Every public function needs at least one test.
- Test names: `test_<function>_<scenario>_<expected>`.
- Mock external services — never hit real APIs in tests.
- Tests must be isolated — no shared mutable state.
- Aim for coverage on critical paths.
""",
            encoding="utf-8",
        )

        # Security instructions (all files)
        (instructions_dir / "security.instructions.md").write_text(
            """---
applyTo: "**"
---

# Security Guidelines

- Never hardcode API keys, tokens, or passwords.
- Store all secrets in environment variables.
- Never log sensitive data (tokens, passwords, PII).
- Validate and sanitize all user input.
- Avoid `eval()` and dynamic code execution with user data.
- Keep dependencies updated — watch for security advisories.
""",
            encoding="utf-8",
        )

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        return {"note": "Copilot hooks not supported — use pre-commit hooks"}

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        created = []
        created.append(_scaffold_gitignore(output_dir, ctx))
        created.append(_scaffold_readme(output_dir, ctx))
        if ctx.language in ("typescript", "javascript"):
            created.append(_scaffold_package_json(output_dir, ctx))
        elif ctx.language == "python":
            created.append(_scaffold_requirements(output_dir, ctx))
        elif ctx.language == "go":
            created.append(_scaffold_go_mod(output_dir, ctx))
        created.append(_scaffold_source_dirs(output_dir, ctx))
        return created


def _get_setup_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm install",
        "python": "pip install -r requirements.txt",
        "go": "go mod tidy",
    }.get(ctx.language, "npm install")


def _get_build_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm run build",
        "python": "python -m compileall src/",
        "go": "go build ./...",
    }.get(ctx.language, "npm run build")


def _get_test_cmd(ctx: ProjectContext) -> str:
    if ctx.test_level == "none":
        return "# No tests configured"
    return {
        "vitest": "npx vitest run",
        "pytest": "pytest",
        "go test": "go test ./...",
    }.get(ctx.test_framework or infer_test_framework(ctx.language), "npm test")


def _get_style_rules(ctx: ProjectContext) -> list[str]:
    rules = {
        "typescript": [
            "- Use TypeScript strict mode",
            "- Prefer `const` over `let`",
            "- Named exports",
            "- Type all parameters",
        ],
        "python": [
            "- Follow PEP 8",
            "- Type hints for public functions",
            "- `snake_case` for variables",
            "- Docstrings for public functions",
        ],
        "go": [
            "- Follow `gofmt`",
            "- Check errors immediately",
            "- Package names: lowercase",
        ],
    }
    return rules.get(ctx.language, ["- Follow language idioms"])


def _scaffold_gitignore(output_dir: str, ctx: ProjectContext) -> str:
    lines = [
        "node_modules/",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        ".env",
        ".env.local",
        "!.env.example",
        "dist/",
        "build/",
        ".idea/",
        ".vscode/",
        ".DS_Store",
        "coverage/",
    ]
    p = Path(output_dir) / ".gitignore"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ".gitignore"


def _scaffold_readme(output_dir: str, ctx: ProjectContext) -> str:
    content = f"# {ctx.project_name}\n\n{ctx.description or 'A project.'}\n\n## Setup\n```bash\n{_get_setup_cmd(ctx)}\n```\n\n## Test\n```bash\n{_get_test_cmd(ctx)}\n```\n"
    p = Path(output_dir) / "README.md"
    p.write_text(content, encoding="utf-8")
    return "README.md"


def _scaffold_package_json(output_dir: str, ctx: ProjectContext) -> str:
    import json

    content = {
        "name": ctx.project_name,
        "version": "0.1.0",
        "type": "module",
        "scripts": {
            "dev": "echo 'Add dev'",
            "build": "echo 'Add build'",
            "test": "npx vitest run",
        },
        "devDependencies": {"typescript": "^5.0.0", "vitest": "^2.0.0"},
    }
    p = Path(output_dir) / "package.json"
    p.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    return "package.json"


def _scaffold_requirements(output_dir: str, ctx: ProjectContext) -> str:
    lines = ["# Core", "# Add dependencies", "", "# Dev", "pytest>=7.0", "ruff>=0.1.0"]
    p = Path(output_dir) / "requirements.txt"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "requirements.txt"


def _scaffold_go_mod(output_dir: str, ctx: ProjectContext) -> str:
    content = f"module {ctx.project_name}\n\ngo 1.21\n"
    p = Path(output_dir) / "go.mod"
    p.write_text(content, encoding="utf-8")
    return "go.mod"


def _scaffold_source_dirs(output_dir: str, ctx: ProjectContext) -> str:
    base = Path(output_dir)
    dirs = ["src", "tests"]
    if ctx.project_type == "api":
        dirs.extend(["src/api", "src/models", "tests/unit"])
    elif ctx.project_type == "web":
        dirs.extend(["src/components", "src/pages", "tests/unit"])
    elif ctx.project_type == "cli":
        dirs.extend(["src/commands", "tests/unit"])
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
    if ctx.language == "python":
        for d in dirs:
            init_file = base / d / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")
    return "source directories"
