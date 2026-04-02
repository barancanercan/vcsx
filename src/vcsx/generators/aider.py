"""Aider AI generator — produces Aider-specific configuration."""

from pathlib import Path

from vcsx.core.context import ProjectContext
from vcsx.generators.base import BaseGenerator


class AiderGenerator(BaseGenerator):
    """Generates a complete Aider terminal AI setup."""

    @property
    def name(self) -> str:
        return "aider"

    @property
    def output_files(self) -> list[str]:
        return [
            ".aider.conf.yaml",
            ".aider.context.md",
        ]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        """Generate Aider configuration file."""
        content = f"""# {ctx.project_name} — Aider Configuration

# Aider Settings
# https://aider.chat/

# Model Configuration
model: gpt-4o
edit-model: gpt-4o
weak-model: gpt-4o-mini

# Repository
repo: {ctx.project_name}

# Commit Message Prompt
commit-prompt: |
    Write a concise commit message following conventional commits.

    ## Format
    <type>(<scope>): <description>

    ## Types
    - feat: New feature
    - fix: Bug fix
    - docs: Documentation
    - style: Code style (formatting)
    - refactor: Code refactoring
    - test: Testing
    - chore: Maintenance

    ## Rules
    - Use imperative mood
    - Keep under 72 characters
    - No period at end
    - Reference issues: Closes #123

    ## Example
    feat(auth): add OAuth2 login flow
    fix(api): handle null response from endpoint
    docs(readme): update installation steps

# File Patterns
only:
    - "*.py"
    - "*.ts"
    - "*.js"
    - "*.go"
    - "*.rs"

# Tools
tools:
    - bash
    - format
    - lint
    - test

# Commands
command:
    format: {ctx.formatter or "black"} {{file}}
    lint: {ctx.linter or "ruff"} {{file}}
    test: pytest

# Safety
no-auto-commit: false
skip-untracked: false
dangerous-allow-write: false

# Context
max-context-characters: 100000
"""

        (Path(output_dir) / ".aider.conf.yaml").write_text(content, encoding="utf-8")
        return content

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate Aider context file."""
        content = f"""# {ctx.project_name} — Project Context

## Overview
{ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack}."}

## Technical Stack
- **Language**: {ctx.language}
- **Framework**: {ctx.framework or "None"}
- **Testing**: {ctx.test_framework or "None"}

## Commands
- **Setup**: {_get_setup_cmd(ctx)}
- **Build**: {_get_build_cmd(ctx)}
- **Test**: {_get_test_cmd(ctx)}

## Guidelines
- Always run tests before committing
- No secrets in code
- Write atomic commits
- Follow conventional commits
"""
        (Path(output_dir) / ".aider.context.md").write_text(content, encoding="utf-8")
        return [".aider.context.md"]

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
