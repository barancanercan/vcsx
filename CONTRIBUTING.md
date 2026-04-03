# Contributing to vcsx

Thank you for your interest in contributing! This guide covers everything you need.

## Development Setup

```bash
# Fork and clone the repo
git clone https://github.com/barancanercan/vcsx.git
cd vcsx

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Running Tests

```bash
# Run all tests (currently 343 tests)
pytest

# Run with coverage report
pytest --cov=vcsx --cov-report=term-missing

# Run specific test file
pytest tests/test_cli.py -v

# Run specific test class
pytest tests/test_generators.py::TestClaudeCodeGenerator -v
```

**Coverage target: 85%+**

## Linting & Formatting

```bash
# Check for lint errors (must be clean)
ruff check src/

# Auto-fix lint errors
ruff check src/ --fix

# Format code
ruff format src/

# Check format without writing
ruff format src/ --check
```

## Project Structure

```
vcsx/
├── src/vcsx/
│   ├── cli.py              # All CLI commands (21 commands)
│   ├── discovery.py        # Interactive wizard phases
│   ├── implementation.py   # File generation orchestration
│   ├── planner.py          # Plan display
│   ├── core/
│   │   ├── context.py      # ProjectContext dataclass
│   │   ├── inference.py    # Language/framework inference (11 languages)
│   │   └── validators.py   # Input validation
│   ├── generators/
│   │   ├── _shared.py      # Shared command/style helpers
│   │   ├── base.py         # BaseGenerator abstract class
│   │   ├── claude_code.py  # Claude Code (CLAUDE.md, 22 skills, 13 hooks, 6 agents)
│   │   ├── cursor.py       # Cursor (.cursorrules + .cursor/rules/*.mdc)
│   │   ├── windsurf.py     # Windsurf (.windsurfrules + .windsurf/rules/*.md)
│   │   ├── copilot.py      # GitHub Copilot
│   │   ├── gemini.py       # Gemini CLI (GEMINI.md)
│   │   ├── agents_md.py    # AGENTS.md universal standard
│   │   ├── aider.py        # Aider (.aider.conf.yaml)
│   │   ├── bolt.py         # Bolt.new
│   │   ├── codex.py        # OpenAI Codex
│   │   ├── zed.py          # Zed editor
│   │   └── registry.py     # Tool registry
│   ├── templates/          # Project template system (10 presets)
│   └── plugins/            # Plugin system
├── tests/
│   ├── test_cli.py         # CLI integration tests (Click runner)
│   ├── test_generators.py  # Generator unit tests
│   └── test_core.py        # Core module tests
└── docs/                   # Documentation
```

## Adding a New AI Tool Generator

1. Create `src/vcsx/generators/my_tool.py`:
```python
from vcsx.generators.base import BaseGenerator
from vcsx.generators._shared import get_setup_cmd, get_test_cmd
from vcsx.core.context import ProjectContext

class MyToolGenerator(BaseGenerator):
    @property
    def name(self) -> str:
        return "my-tool"

    @property
    def output_files(self) -> list[str]:
        return ["MY_TOOL.md"]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        # Write your config file
        content = f"# {ctx.project_name} — My Tool Config\n"
        (Path(output_dir) / "MY_TOOL.md").write_text(content)
        return content

    def generate_skills(self, ctx, output_dir): return []
    def generate_hooks(self, ctx, output_dir): return {}
    def generate_agents(self, ctx, output_dir): return []
    def generate_scaffold(self, ctx, output_dir): return []
```

2. Register in `src/vcsx/generators/registry.py`:
```python
from vcsx.generators.my_tool import MyToolGenerator

CLI_TOOLS: dict[str, type[BaseGenerator]] = {
    ...
    "my-tool": MyToolGenerator,
}
```

3. Add tests in `tests/test_generators.py`:
```python
class TestMyToolGenerator:
    def test_generate_config(self, ctx, tmp_dir):
        gen = MyToolGenerator()
        gen.generate_config(ctx, tmp_dir)
        assert (Path(tmp_dir) / "MY_TOOL.md").exists()
```

## Adding a New Skill (Claude Code)

Skills are defined in `src/vcsx/generators/claude_code.py`.

```python
def _skill_my_skill(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "my-skill"
    d.mkdir(parents=True, exist_ok=True)
    content = f"""---
name: my-skill
description: What this skill does. Use when X.
---

# My Skill

## Process
1. Step one
2. Step two

## Rules
- Rule one
- Rule two
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "my-skill"
```

Then call it in `generate_skills()`:
```python
created.append(_skill_my_skill(skills_dir, ctx))
```

## Adding a New CLI Command

Commands are defined in `src/vcsx/cli.py` using Click:

```python
@main.command("my-command")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--flag", is_flag=True, help="Enable something")
def my_command(path, flag):
    """Brief description for help text."""
    target = Path(path).resolve()
    console.print(f"[bold]vcsx my-command[/] — {target}")
    # ... implementation
```

Add tests in `tests/test_cli.py`:
```python
class TestMyCommand:
    def test_basic(self, runner, tmp_dir):
        result = runner.invoke(main, ["my-command", tmp_dir])
        assert result.exit_code == 0
```

## Adding a Project Template

Templates are in `src/vcsx/templates/__init__.py`:

```python
def _create_my_template() -> Template:
    metadata = TemplateMetadata(
        name="my-template",
        description="My project template",
        tags=["python", "api"],
        tech_stack={"language": "python", "framework": "FastAPI", "type": "api"},
    )
    template = Template(metadata)
    template.add_file("README.md", "# My Project\n")
    template.add_file("requirements.txt", "fastapi\n")
    return template
```

Register it in `_load_default_templates()`:
```python
registry.register(_create_my_template())
```

## Pull Request Process

1. Branch from `main`: `git checkout -b feat/my-feature`
2. Write code + tests (coverage must stay ≥ 85%)
3. Run: `pytest && ruff check src/ && ruff format src/ --check`
4. Commit with conventional commits: `feat: add my feature`
5. Push and open PR against `main`

## Commit Convention

```
feat: new feature
fix: bug fix
refactor: code restructure
docs: documentation only
test: adding tests
chore: tooling, dependencies
```

## Questions?

Open an issue at https://github.com/barancanercan/vcsx/issues
