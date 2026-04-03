"""Bolt.new generator — produces Bolt.new-specific configuration.

Bolt.new is a browser-based AI development environment.
Reference: https://bolt.new
"""

import json
from pathlib import Path

from vcsx.core.context import ProjectContext
from vcsx.generators._shared import (
    get_build_cmd,
    get_dev_cmd,
    get_setup_cmd,
    get_test_cmd,
)
from vcsx.generators.base import BaseGenerator


class BoltGenerator(BaseGenerator):
    """Generates a complete Bolt.new web-first AI setup."""

    @property
    def name(self) -> str:
        return "bolt"

    @property
    def output_files(self) -> list[str]:
        return [
            ".bolt/setup.md",
            ".bolt/workspace.json",
            ".bolt/prompts.md",
        ]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        """Generate .bolt/workspace.json — Bolt sandbox configuration."""
        (ctx.language or "").lower()

        content = {
            "version": "1.0",
            "project": {
                "name": ctx.project_name,
                "description": ctx.description or f"A {ctx.project_type} project",
                "type": ctx.project_type,
                "techStack": {
                    "language": ctx.language,
                    "framework": ctx.framework or "",
                    "testing": ctx.test_framework or "",
                },
            },
            "ai": {
                # claude-sonnet-4-5 is the correct model identifier
                "model": "claude-sonnet-4-5",
                "temperature": 0.7,
                "maxTokens": 8192,
                "systemPrompt": _build_system_prompt(ctx),
            },
            "sandbox": {
                "enabled": True,
                "autoReload": True,
                "port": _get_default_port(ctx),
                "installCommand": get_setup_cmd(ctx),
                "startCommand": get_dev_cmd(ctx),
            },
            "build": {
                "command": get_build_cmd(ctx),
                "devCommand": get_dev_cmd(ctx),
                "testCommand": get_test_cmd(ctx),
            },
            "env": {
                "description": "Add required environment variables below",
                "required": _get_required_env_vars(ctx),
            },
        }

        bolt_dir = Path(output_dir) / ".bolt"
        bolt_dir.mkdir(parents=True, exist_ok=True)
        content_str = json.dumps(content, indent=2)
        (bolt_dir / "workspace.json").write_text(content_str, encoding="utf-8")
        return content_str

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate .bolt/setup.md and .bolt/prompts.md."""
        bolt_dir = Path(output_dir) / ".bolt"
        bolt_dir.mkdir(parents=True, exist_ok=True)

        setup = get_setup_cmd(ctx)
        dev = get_dev_cmd(ctx)
        build = get_build_cmd(ctx)
        test = get_test_cmd(ctx)

        setup_content = f"""# {ctx.project_name} — Bolt.new Setup

## Project
{ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack or ctx.language}."}

## Quick Start
```bash
# Install dependencies
{setup}

# Start dev server
{dev}

# Run tests
{test}

# Build for production
{build}
```

## Tech Stack
- **Language**: {ctx.language or "Not specified"}
- **Framework**: {ctx.framework or "None"}
- **Testing**: {ctx.test_framework or "None"}
- **Project type**: {ctx.project_type}

## Development Workflow
1. Start dev server: `{dev}`
2. Make changes in the Bolt.new browser editor
3. Run tests: `{test}`
4. Build: `{build}`

## Code Conventions
- Never commit `.env` files or hardcoded secrets
- Write tests for new functionality
- Follow existing code patterns
- Keep components/functions small and focused
"""
        (bolt_dir / "setup.md").write_text(setup_content, encoding="utf-8")

        prompts_content = _build_prompts_md(ctx, dev, build, test)
        (bolt_dir / "prompts.md").write_text(prompts_content, encoding="utf-8")

        return ["setup.md", "prompts.md"]

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        return {}

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []


# ─── Private helpers ─────────────────────────────────────────────────────────


def _build_system_prompt(ctx: ProjectContext) -> str:
    """Build AI system prompt for this project."""
    lang = ctx.language or "the project language"
    fw = f" with {ctx.framework}" if ctx.framework else ""
    return (
        f"You are an expert {lang} developer{fw}. "
        f"This is a {ctx.project_type} project called {ctx.project_name}. "
        f"Always write clean, tested, production-ready code. "
        f"Never hardcode secrets. Always handle errors. "
        f"Follow the existing patterns in the codebase."
    )


def _get_default_port(ctx: ProjectContext) -> int:
    """Return the default dev server port based on framework."""
    framework_lower = (ctx.framework or "").lower()
    lang = (ctx.language or "").lower()

    if "next" in framework_lower:
        return 3000
    if "react" in framework_lower or "vue" in framework_lower or "svelte" in framework_lower:
        return 5173  # Vite default
    if "fastapi" in framework_lower or lang == "python":
        return 8000
    if "flask" in framework_lower:
        return 5000
    if "django" in framework_lower:
        return 8000
    if lang == "go":
        return 8080
    if lang == "rust":
        return 3000
    return 3000


def _get_required_env_vars(ctx: ProjectContext) -> list[str]:
    """Return list of likely required environment variables."""
    vars_list = []
    if ctx.auth_needed:
        vars_list.append(
            "JWT_SECRET" if "jwt" in (ctx.auth_method or "").lower() else "AUTH_SECRET"
        )
    if ctx.project_type in ("web", "api"):
        vars_list.append("DATABASE_URL")
    if ctx.hosting:
        vars_list.append("NODE_ENV")
    if not vars_list:
        vars_list = ["DATABASE_URL", "API_KEY"]
    return vars_list


def _build_prompts_md(ctx: ProjectContext, dev: str, build: str, test: str) -> str:
    """Build comprehensive prompt templates for Bolt.new."""
    project_context = f"""**Project:** {ctx.project_name}
**Type:** {ctx.project_type}
**Stack:** {ctx.tech_stack or ctx.language}
**Framework:** {ctx.framework or "None"}"""

    return f"""# {ctx.project_name} — Bolt.new AI Prompts

> Copy these prompts into Bolt.new's AI assistant for common tasks.

## Project Context (include in all prompts)
```
{project_context}
```

---

## 🆕 New Feature
```
[CONTEXT] {project_context}

Implement: <feature name>

Requirements:
- <requirement 1>
- <requirement 2>
- <requirement 3>

Acceptance criteria:
- <criterion 1>
- <criterion 2>

After implementing, run: {test}
All tests must pass before considering it done.
```

---

## 🐛 Bug Fix
```
[CONTEXT] {project_context}

Bug: <short description>

Steps to reproduce:
1. <step 1>
2. <step 2>

Expected: <what should happen>
Actual: <what is happening>

Fix the root cause (not just the symptom). Run {test} to verify.
```

---

## ♻️ Refactor
```
[CONTEXT] {project_context}

Refactor: <what to refactor and why>

Goals:
- Improve readability / reduce complexity / remove duplication
- Keep the SAME external behavior
- All existing tests must still pass

Constraints:
- Do NOT change functionality
- Do NOT introduce new dependencies
- Keep the diff minimal

Run {test} before and after to verify behavior is unchanged.
```

---

## ✅ Add Tests
```
[CONTEXT] {project_context}

Add tests for: <function/module name>

Test cases to cover:
- Happy path
- Edge cases (empty input, null, boundary values)
- Error cases (invalid input, network failure, etc.)

Use {ctx.test_framework or "the existing test framework"}.
Follow existing test patterns in the tests/ directory.
Run {test} to verify all tests pass.
```

---

## 🔍 Code Review
```
[CONTEXT] {project_context}

Review this code for:
- Correctness: does it do what it should?
- Security: any vulnerabilities?
- Performance: any obvious bottlenecks?
- Readability: is it clear and maintainable?
- Tests: is it adequately tested?

Rate each issue: [BLOCKING] [SUGGESTION] [NITPICK]
```

---

## 📦 Dependency Update
```
[CONTEXT] {project_context}

Update <package name> from <old version> to <new version>.

1. Update the dependency
2. Fix any breaking changes
3. Verify: {test}
4. Document breaking changes in CHANGELOG
```

---

## 🚀 Performance Optimization
```
[CONTEXT] {project_context}

Optimize: <what is slow and why it matters>

Measure first, then optimize. Show before/after benchmarks.
Do not sacrifice readability for micro-optimizations.
Run {test} to verify behavior is unchanged.
```
"""
