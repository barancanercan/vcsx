"""Zed AI generator — produces Zed-specific configuration."""

from pathlib import Path

from vcsx.core.context import ProjectContext
from vcsx.generators.base import BaseGenerator


class ZedGenerator(BaseGenerator):
    """Generates a complete Zed IDE AI setup."""

    @property
    def name(self) -> str:
        return "zed"

    @property
    def output_files(self) -> list[str]:
        return [
            ".zed/settings.json",
            ".zed/context.md",
            ".zed/hooks.toml",
        ]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        """Generate Zed settings.json file."""
        import json

        settings = {
            "$schema": "https://zed.dev/schema/settings.json",
            "version": "1.0",
            "project": {
                "name": ctx.project_name,
                "type": ctx.project_type,
                "language": ctx.language,
                "framework": ctx.framework,
            },
            "assistant": {
                "version": "1.0",
                "profile": "default",
            },
            "language_server": {
                "enabled": True,
                "command": _get_lsp_cmd(ctx),
            },
        }

        content = json.dumps(settings, indent=2)
        zed_dir = Path(output_dir) / ".zed"
        zed_dir.mkdir(parents=True, exist_ok=True)
        (zed_dir / "settings.json").write_text(content, encoding="utf-8")
        return content

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate Zed-specific context files."""
        zed_dir = Path(output_dir) / ".zed"
        zed_dir.mkdir(parents=True, exist_ok=True)

        context_content = f"""# {ctx.project_name} — Project Context

## Overview
{ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack}."}

## Technical Stack
- **Language**: {ctx.language}
- **Framework**: {ctx.framework or "None"}
- **Testing**: {ctx.test_framework or "None"}
- **Hosting**: {ctx.hosting or "TBD"}

## Commands
- **Setup**: {_get_setup_cmd(ctx)}
- **Build**: {_get_build_cmd(ctx)}
- **Test**: {_get_test_cmd(ctx)}

## Architecture
```
{ctx.project_name}/
├── src/
├── tests/
└── config files
```

## Guidelines
- Always run tests before committing
- No secrets in code
- Follow existing code patterns
"""
        (zed_dir / "context.md").write_text(context_content, encoding="utf-8")
        return ["context.md"]

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        """Generate hooks configuration."""
        zed_dir = Path(output_dir) / ".zed"
        zed_dir.mkdir(parents=True, exist_ok=True)

        hooks_content = f"""# Zed Hooks Configuration
# https://zed.dev/docs/hooks

[pre_commit]
command = "{ctx.linter or "ruff"} ."
description = "Run linter before commit"

[pre_commit.test]
command = "{_get_test_cmd(ctx)}"
description = "Run tests before commit"

[on_save]
format_on_save = true
trim_whitespace = true
"""
        (zed_dir / "hooks.toml").write_text(hooks_content, encoding="utf-8")
        return {"hooks.toml": "pre-commit lint + test, format on save"}

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate agent definitions."""
        return []

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate project scaffold."""
        return []


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
    return {
        "vitest": "npx vitest run",
        "pytest": "pytest",
        "go test": "go test ./...",
    }.get(ctx.test_framework or "pytest", "npm test")


def _get_lsp_cmd(ctx: ProjectContext) -> str:
    commands = {
        "typescript": "typescript-language-server --stdio",
        "python": "pylsp",
        "go": "gopls",
    }
    return commands.get(ctx.language, "tsserver")
