# Contributing to vcsx

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# Fork and clone the repo
git clone https://github.com/YOUR_USERNAME/vibe-coding-setup-expert.git
cd vibe-coding-setup-expert

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vcsx --cov-report=term-missing

# Run specific test file
pytest tests/test_core.py -v
```

## Linting & Formatting

```bash
# Check for lint errors
ruff check src/

# Auto-fix lint errors
ruff check src/ --fix

# Check formatting
ruff format src/ --check

# Auto-format
ruff format src/
```

## Adding a New CLI Tool Generator

vcsx uses a plugin architecture. Adding a new CLI tool takes just 3 steps:

### Step 1: Create the Generator

Create `src/vcsx/generators/new_tool.py`:

```python
from pathlib import Path
from vcsx.core.context import ProjectContext
from vcsx.generators.base import BaseGenerator


class NewToolGenerator(BaseGenerator):
    @property
    def name(self) -> str:
        return "new-tool"

    @property
    def output_files(self) -> list[str]:
        return [".newtool/config.md"]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        content = f"# {ctx.project_name} — New Tool Config\n..."
        (Path(output_dir) / ".newtool" / "config.md").write_text(content)
        return content

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        return {}

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []
```

### Step 2: Register It

Add to `src/vcsx/generators/registry.py`:

```python
from vcsx.generators.new_tool import NewToolGenerator

CLI_TOOLS = {
    ...
    "new-tool": NewToolGenerator,
}
```

### Step 3: Write Tests

Add tests in `tests/test_generators.py`:

```python
def test_new_tool_generator(ctx, tmp_dir):
    gen = NewToolGenerator()
    content = gen.generate_config(ctx, tmp_dir)
    assert "config" in content
```

That's it! Your new CLI tool is now available:

```bash
vcsx init --cli new-tool
```

## Pull Request Guidelines

1. **Branch naming**: `feature/add-new-tool`, `fix/discovery-parsing`, `docs/update-readme`
2. **Commit messages**: Use conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`)
3. **Tests**: All new code must have tests
4. **Linting**: `ruff check` and `ruff format` must pass
5. **Documentation**: Update README if adding new features

## Architecture Overview

```
src/vcsx/
├── cli.py              # Click CLI entry point
├── __main__.py         # Module execution
├── discovery.py        # Interactive questionnaire
├── planner.py          # Plan generation
├── implementation.py   # Orchestration
├── core/
│   ├── context.py      # ProjectContext dataclass
│   ├── inference.py    # Tech stack → language/framework
│   └── validators.py   # Input validation
├── generators/
│   ├── base.py         # Abstract BaseGenerator
│   ├── registry.py     # CLI tool registry
│   ├── claude_code.py  # Claude Code generator
│   ├── cursor.py       # Cursor generator
│   ├── codex.py        # OpenAI Codex generator
│   └── copilot.py      # GitHub Copilot generator
└── utils/
    └── prompts.py      # TR/EN question bank
```

## Reporting Issues

- Use the issue template
- Include Python version, OS, and vcsx version
- Provide reproduction steps

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
