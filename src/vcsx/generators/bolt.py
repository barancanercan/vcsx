"""Bolt.new generator — produces Bolt.new-specific configuration."""

from pathlib import Path

from vcsx.core.context import ProjectContext
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
        """Generate Bolt setup configuration."""
        import json

        content = {
            "version": "1.0",
            "project": {
                "name": ctx.project_name,
                "description": ctx.description or f"A {ctx.project_type} project",
                "type": ctx.project_type,
                "techStack": {
                    "language": ctx.language,
                    "framework": ctx.framework,
                    "testing": ctx.test_framework,
                },
            },
            "ai": {
                "model": "claude-sonnet-4-5",
                "temperature": 0.7,
                "maxTokens": 8192,
            },
            "sandbox": {
                "enabled": True,
                "autoReload": True,
                "port": 3000,
            },
            "build": {
                "command": _get_build_cmd(ctx),
                "devCommand": _get_dev_cmd(ctx),
            },
        }

        bolt_dir = Path(output_dir) / ".bolt"
        bolt_dir.mkdir(parents=True, exist_ok=True)
        content_str = json.dumps(content, indent=2)
        (bolt_dir / "workspace.json").write_text(content_str, encoding="utf-8")
        return content_str

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate Bolt-specific setup file."""
        bolt_dir = Path(output_dir) / ".bolt"
        bolt_dir.mkdir(parents=True, exist_ok=True)

        content = f"""# {ctx.project_name} — Bolt.new Setup

## Project
{ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack}."}

## Tech Stack
- **Language**: {ctx.language}
- **Framework**: {ctx.framework or "None"}
- **Testing**: {ctx.test_framework or "None"}

## Development
- **Dev Server**: {_get_dev_cmd(ctx)}
- **Build**: {_get_build_cmd(ctx)}
- **Test**: {_get_test_cmd(ctx)}

## Guidelines
1. Start dev server: `{_get_dev_cmd(ctx)}`
2. Make changes in browser
3. Run tests before commit
4. No secrets in code

## Architecture
```
{ctx.project_name}/
├── src/
├── public/
├── tests/
└── config
```
"""

        (bolt_dir / "setup.md").write_text(content, encoding="utf-8")

        prompts_content = f"""# Bolt.new AI Prompts

## Project Context
{ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack}."}

## Tech Stack
- Language: {ctx.language}
- Framework: {ctx.framework or "None"}
- Testing: {ctx.test_framework or "None"}

## Quick Commands
- Setup: `{_get_setup_cmd(ctx)}`
- Dev: `{_get_dev_cmd(ctx)}`
- Build: `{_get_build_cmd(ctx)}`
- Test: `{_get_test_cmd(ctx)}`

## Prompt Templates

### New Feature
```
Create a new feature: <feature-name>
Requirements:
- <requirement 1>
- <requirement 2>

Test with: {_get_test_cmd(ctx)}
```

### Bug Fix
```
Fix bug: <bug-description>
Expected behavior: <what should happen>
Actual behavior: <what is happening>

Test with: {_get_test_cmd(ctx)}
```

### Refactor
```
Refactor: <what to refactor>
Reason: <why this refactor is needed>
Keep the same external API
```

### Run Tests
```
Run tests and fix any failures
Command: {_get_test_cmd(ctx)}
```
"""
        (bolt_dir / "prompts.md").write_text(prompts_content, encoding="utf-8")

        return ["setup.md", "prompts.md"]

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        """Generate hooks configuration."""
        return {}

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate agent definitions."""
        return []

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate project scaffold."""
        return []


def _get_dev_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm run dev",
        "javascript": "npm run dev",
        "python": "python -m flask run",
    }.get(ctx.language, "npm run dev")


def _get_build_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm run build",
        "javascript": "npm run build",
        "python": "python -m compileall src/",
    }.get(ctx.language, "npm run build")


def _get_test_cmd(ctx: ProjectContext) -> str:
    return {
        "vitest": "npx vitest run",
        "pytest": "pytest",
    }.get(ctx.test_framework or "pytest", "npm test")


def _get_setup_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm install",
        "javascript": "npm install",
        "python": "pip install -r requirements.txt",
    }.get(ctx.language, "npm install")
