"""OpenAI Codex generator — produces .openai/ instructions."""

from pathlib import Path

from vcsx.core.context import ProjectContext
from vcsx.core.inference import infer_formatter, infer_linter, infer_test_framework
from vcsx.generators.base import BaseGenerator


class CodexGenerator(BaseGenerator):
    """Generates an OpenAI Codex setup."""

    @property
    def name(self) -> str:
        return "codex"

    @property
    def output_files(self) -> list[str]:
        return [".openai/instructions.md"]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        """Generate .openai/instructions.md."""
        lines = [
            f"# {ctx.project_name} — Codex Instructions",
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
        d = Path(output_dir) / ".openai"
        d.mkdir(parents=True, exist_ok=True)
        (d / "instructions.md").write_text(content, encoding="utf-8")
        return content

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        return {"note": "Codex hooks not supported — use pre-commit hooks"}

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
