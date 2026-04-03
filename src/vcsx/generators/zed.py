"""Zed AI generator — produces Zed-specific configuration.

Zed is a high-performance code editor with built-in AI assistance.
Reference: https://zed.dev/docs
"""

import json
from pathlib import Path

from vcsx.core.context import ProjectContext
from vcsx.generators._shared import get_build_cmd, get_setup_cmd, get_test_cmd
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
            ".zed/tasks.json",
        ]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        """Generate .zed/settings.json using Zed's actual settings schema."""
        lang = (ctx.language or "").lower()

        # Language-specific tab size
        tab_size = 4 if lang in ("python", "java", "rust") else 2

        # Build language overrides
        language_overrides: dict = {}
        if lang == "python":
            language_overrides["Python"] = {
                "language_servers": ["pyright", "ruff"],
                "format_on_save": {"language_server": {"name": "ruff"}},
                "formatter": {"language_server": {"name": "ruff"}},
            }
        elif lang in ("typescript", "javascript"):
            language_overrides["TypeScript"] = {
                "language_servers": ["typescript-language-server"],
                "format_on_save": {
                    "external": {
                        "command": "prettier",
                        "arguments": ["--stdin-filepath", "{buffer_path}"],
                    }
                },
            }
            language_overrides["JavaScript"] = language_overrides["TypeScript"].copy()
        elif lang == "go":
            language_overrides["Go"] = {
                "language_servers": ["gopls"],
                "format_on_save": {"language_server": {"name": "gopls"}},
            }
        elif lang == "rust":
            language_overrides["Rust"] = {
                "language_servers": ["rust-analyzer"],
                "format_on_save": {"language_server": {"name": "rust-analyzer"}},
            }

        settings: dict = {
            "$schema": "https://zed.dev/schema/settings.json",
            # Editor
            "tab_size": tab_size,
            "hard_tabs": lang == "go",  # Go uses tabs
            "soft_wrap": "none",
            "show_whitespaces": "selection",
            "format_on_save": "on",
            "remove_trailing_whitespace_on_save": True,
            "ensure_final_newline_on_save": True,
            # Assistant (AI)
            "assistant": {
                "version": "2",
                "default_model": {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-5",
                },
                "button": True,
            },
            # Git
            "git": {
                "inline_blame": {"enabled": True, "delay_ms": 600},
                "git_gutter": "tracked_files",
            },
            # Terminal
            "terminal": {
                "shell": "system",
                "working_directory": "current_project_directory",
            },
            # Vim mode (optional)
            "vim_mode": False,
            # File types
            "file_types": {
                "Plain Text": [".env.example", ".claudeignore"],
                "YAML": ["docker-compose.yml", "docker-compose.*.yml"],
            },
        }

        if language_overrides:
            settings["languages"] = language_overrides

        content = json.dumps(settings, indent=2)
        zed_dir = Path(output_dir) / ".zed"
        zed_dir.mkdir(parents=True, exist_ok=True)
        (zed_dir / "settings.json").write_text(content, encoding="utf-8")
        return content

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate .zed/context.md — project context for Zed AI."""
        zed_dir = Path(output_dir) / ".zed"
        zed_dir.mkdir(parents=True, exist_ok=True)

        setup = get_setup_cmd(ctx)
        build = get_build_cmd(ctx)
        test = get_test_cmd(ctx)

        context_content = f"""# {ctx.project_name} — Zed Project Context

> This file provides context to Zed's AI assistant.
> Edit it to improve AI suggestions for your project.

## Project Overview
{ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack or ctx.language}."}

## Tech Stack
- **Language**: {ctx.language or "Not specified"}
- **Framework**: {ctx.framework or "None"}
- **Test Framework**: {ctx.test_framework or "None"}
- **Hosting**: {ctx.hosting or "TBD"}

## Quick Commands
```bash
# Setup
{setup}

# Build
{build}

# Test
{test}
```

## Code Conventions
- Never commit `.env` or secrets
- Run formatter before committing
- All new functionality needs tests
- Follow existing code patterns in the codebase
- Keep functions small (< 30 lines)

## Project Structure
```
{ctx.project_name}/
├── src/           # Source code
├── tests/         # Test files
└── ...            # Config files
```

## Useful Context for AI
- This is a **{ctx.project_type}** project
- Primary language: **{ctx.language or "See tech stack"}**
- When suggesting code, follow the patterns in `src/`
- Always include error handling
- Prefer explicit over implicit
"""
        (zed_dir / "context.md").write_text(context_content, encoding="utf-8")
        return ["context.md"]

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        """Generate .zed/hooks.toml — pre-commit and on-save hooks."""
        zed_dir = Path(output_dir) / ".zed"
        zed_dir.mkdir(parents=True, exist_ok=True)
        lang = (ctx.language or "").lower()

        lint_cmd = ctx.linter or ("ruff check" if lang == "python" else "eslint .")
        fmt_cmd = ctx.formatter or ("ruff format" if lang == "python" else "prettier --write")
        test_cmd = get_test_cmd(ctx)

        hooks_content = f"""# Zed Hooks Configuration
# Reference: https://zed.dev/docs/tasks

[pre_commit]
# Lint before every commit
command = "{lint_cmd} ."
description = "Lint: {lint_cmd}"

[pre_commit.test]
# Run tests before commit
command = "{test_cmd}"
description = "Tests: {test_cmd}"

[on_save]
# Format on save (handled by Zed settings, but defined here as reference)
format_on_save = true
trim_whitespace = true
ensure_final_newline = true

# Format command (if using external formatter)
# format_command = "{fmt_cmd} {{file}}"
"""
        (zed_dir / "hooks.toml").write_text(hooks_content, encoding="utf-8")
        return {"hooks.toml": "pre-commit lint + test, format on save"}

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate .zed/tasks.json — Zed task definitions."""
        zed_dir = Path(output_dir) / ".zed"
        zed_dir.mkdir(parents=True, exist_ok=True)

        setup = get_setup_cmd(ctx)
        build = get_build_cmd(ctx)
        test = get_test_cmd(ctx)
        lang = (ctx.language or "").lower()
        lint_cmd = ctx.linter or ("ruff check" if lang == "python" else "eslint .")

        tasks = [
            {"label": "Build", "command": build},
            {"label": "Test", "command": test},
            {"label": "Test: watch", "command": test + " --watch" if "vitest" in test else test},
            {"label": "Lint", "command": lint_cmd + " ."},
            {"label": "Setup", "command": setup},
        ]

        if ctx.formatter:
            tasks.append({"label": "Format", "command": f"{ctx.formatter} ."})

        content = json.dumps(tasks, indent=2)
        (zed_dir / "tasks.json").write_text(content, encoding="utf-8")
        return ["tasks.json"]

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate project scaffold."""
        return []


def _get_lsp_cmd(ctx: ProjectContext) -> str:
    """Return LSP command for the given language (legacy compat)."""
    commands = {
        "typescript": "typescript-language-server --stdio",
        "javascript": "typescript-language-server --stdio",
        "python": "pyright-langserver --stdio",
        "go": "gopls",
        "rust": "rust-analyzer",
    }
    return commands.get((ctx.language or "").lower(), "typescript-language-server --stdio")
