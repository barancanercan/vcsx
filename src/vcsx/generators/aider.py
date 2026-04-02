"""Aider AI generator — produces Aider-specific configuration.

Aider docs: https://aider.chat/docs/config/aider_conf.html
Valid .aider.conf.yaml keys align with Aider's CLI flags.
"""

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
        """Generate .aider.conf.yaml using valid Aider CLI flags.

        Key valid settings: model, weak-model, editor-model, auto-commits,
        dirty-commits, git, auto-lint, lint-cmd, auto-test, test-cmd,
        read, map-tokens, cache-prompts, suggest-shell-commands.
        """
        lang = (ctx.language or "").lower()

        # Derive test command
        test_cmd = _get_test_cmd(ctx)

        # Derive lint command
        lint_cmd = ctx.linter or ("ruff check" if lang == "python" else "eslint .")

        # Language-specific file patterns for --read (context files to always include)
        read_files = _get_read_files(ctx)

        content = f"""# {ctx.project_name} — Aider Configuration
# Reference: https://aider.chat/docs/config/aider_conf.html

##############################################################
# Model Configuration
##############################################################
# Claude Sonnet is recommended for best coding performance.
# Uncomment the model you want to use:

# model: anthropic/claude-sonnet-4-5
# model: openai/gpt-4o
model: openai/gpt-4o

# Weaker model for simple tasks (faster + cheaper)
weak-model: openai/gpt-4o-mini

##############################################################
# Git Integration
##############################################################
# Auto-commit AI changes with a generated commit message
auto-commits: true

# Allow commits even when repo has uncommitted changes
dirty-commits: true

# Git integration (disable to use aider outside a git repo)
git: true

##############################################################
# Linting & Testing
##############################################################
# Run linter after every code change
auto-lint: true
lint-cmd: {lint_cmd}

# Run tests after every code change
auto-test: false
test-cmd: {test_cmd}

##############################################################
# Context Management
##############################################################
# Files to always include in context (read-only)
{_format_read_files(read_files)}
# Repository map token budget (higher = more context, more tokens)
map-tokens: 2048

# Cache AI prompts to reduce costs (requires aider >= 0.50)
cache-prompts: true

##############################################################
# UX
##############################################################
# Suggest shell commands when appropriate
suggest-shell-commands: true

# Show diffs after applying changes
show-diffs: false
"""
        (Path(output_dir) / ".aider.conf.yaml").write_text(content, encoding="utf-8")
        return content

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate .aider.context.md — always-loaded project context."""
        content = f"""# {ctx.project_name} — Aider Project Context

> This file is automatically loaded by Aider as project context.
> Edit it to give Aider better understanding of your project.

## Overview
{ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack}."}

## Purpose & Problem
{"**Purpose:** " + ctx.purpose if ctx.purpose else "*(not specified)*"}
{"**Problem:** " + ctx.problem if ctx.problem else ""}

## Tech Stack
- **Language**: {ctx.language or "Not specified"}
- **Framework**: {ctx.framework or "None"}
- **Testing**: {ctx.test_framework or "None"}
- **Hosting**: {ctx.hosting or "TBD"}

## Commands
```bash
# Setup
{_get_setup_cmd(ctx)}

# Build
{_get_build_cmd(ctx)}

# Test
{_get_test_cmd(ctx)}
```

## Code Conventions
- Follow conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Never commit secrets, API keys, or `.env` files
- Write tests for new functionality
- Keep commits atomic — one logical change per commit

## Architecture
The project is organized as a `{ctx.project_type}` application.
{"Primary language: " + ctx.language if ctx.language else ""}
{"Framework: " + ctx.framework if ctx.framework else ""}

## What NOT to Do
- Do not run `git push --force`
- Do not modify production database migrations
- Do not install global packages without updating requirements
"""
        (Path(output_dir) / ".aider.context.md").write_text(content, encoding="utf-8")
        return [".aider.context.md"]

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        """Aider handles hooks via auto-lint and auto-test in config."""
        return {}

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []


# ─── Private helpers ──────────────────────────────────────────────────────────

def _get_setup_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm install",
        "javascript": "npm install",
        "python": "pip install -e '.[dev]'" if "pyproject" in (ctx.tech_stack or "").lower() else "pip install -r requirements.txt",
        "go": "go mod tidy",
        "rust": "cargo build",
    }.get((ctx.language or "").lower(), "npm install")


def _get_build_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm run build",
        "javascript": "npm run build",
        "python": "python -m build",
        "go": "go build ./...",
        "rust": "cargo build --release",
    }.get((ctx.language or "").lower(), "npm run build")


def _get_test_cmd(ctx: ProjectContext) -> str:
    fw = (ctx.test_framework or "").lower()
    if fw == "pytest" or (not fw and (ctx.language or "").lower() == "python"):
        return "pytest"
    if fw in ("vitest", "jest"):
        return f"npx {fw} run"
    if fw == "go test":
        return "go test ./..."
    if (ctx.language or "").lower() == "rust":
        return "cargo test"
    return "npm test"


def _get_read_files(ctx: ProjectContext) -> list[str]:
    """Return files Aider should always read as context."""
    candidates = ["README.md", "AGENTS.md", "CLAUDE.md"]
    lang = (ctx.language or "").lower()
    if lang == "python":
        candidates.extend(["pyproject.toml", "requirements.txt"])
    elif lang in ("typescript", "javascript"):
        candidates.append("package.json")
    elif lang == "go":
        candidates.append("go.mod")
    elif lang == "rust":
        candidates.append("Cargo.toml")
    return candidates


def _format_read_files(files: list[str]) -> str:
    if not files:
        return ""
    lines = ["read:"]
    for f in files:
        lines.append(f"  - {f}")
    return "\n".join(lines) + "\n"
