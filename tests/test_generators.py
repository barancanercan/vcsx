"""Tests for generators."""

import json
import tempfile
from pathlib import Path
import pytest

from vcsx.core.context import ProjectContext
from vcsx.generators.claude_code import ClaudeCodeGenerator
from vcsx.generators.cursor import CursorGenerator
from vcsx.generators.codex import CodexGenerator
from vcsx.generators.copilot import CopilotGenerator
from vcsx.generators.registry import get_generator, get_all_generators, ALL_TOOLS


@pytest.fixture
def ctx():
    return ProjectContext(
        project_name="test-project",
        description="A test project",
        project_type="api",
        tech_stack="Python, FastAPI, PostgreSQL",
        language="python",
        framework="FastAPI",
        mvp_features="User auth, CRUD API, Health check",
        hosting="Railway",
        auth_needed=True,
        auth_method="JWT",
        test_level="unit",
        test_framework="pytest",
        formatter="ruff format",
        linter="ruff check",
    )


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestClaudeCodeGenerator:
    def test_generate_config(self, ctx, tmp_dir):
        gen = ClaudeCodeGenerator()
        content = gen.generate_config(ctx, tmp_dir)
        assert (Path(tmp_dir) / "CLAUDE.md").exists()
        assert "test-project" in content
        assert len(content.splitlines()) <= 200

    def test_generate_skills(self, ctx, tmp_dir):
        gen = ClaudeCodeGenerator()
        skills = gen.generate_skills(ctx, tmp_dir)
        assert "commit-message" in skills
        assert "pr-review" in skills
        assert "deploy" in skills
        assert "security-review" in skills
        assert "refactor" in skills
        assert "auth-conventions" in skills
        assert "api-conventions" in skills
        assert "test-patterns" in skills

    def test_skill_frontmatter(self, ctx, tmp_dir):
        gen = ClaudeCodeGenerator()
        gen.generate_skills(ctx, tmp_dir)
        sf = Path(tmp_dir) / ".claude" / "skills" / "commit-message" / "SKILL.md"
        content = sf.read_text()
        assert "---" in content
        assert "name:" in content
        assert "description:" in content

    def test_generate_hooks(self, ctx, tmp_dir):
        gen = ClaudeCodeGenerator()
        settings = gen.generate_hooks(ctx, tmp_dir)
        assert "hooks" in settings
        assert (Path(tmp_dir) / ".claude" / "settings.json").exists()
        assert (Path(tmp_dir) / ".claude" / "hooks" / "block_destructive.sh").exists()
        assert (Path(tmp_dir) / ".claude" / "hooks" / "auto_format.sh").exists()
        assert (Path(tmp_dir) / ".claude" / "hooks" / "secret_scan.sh").exists()

    def test_generate_agents(self, ctx, tmp_dir):
        gen = ClaudeCodeGenerator()
        agents = gen.generate_agents(ctx, tmp_dir)
        assert "security-reviewer" in agents
        assert "test-writer" in agents
        assert "researcher" in agents

    def test_generate_scaffold(self, ctx, tmp_dir):
        gen = ClaudeCodeGenerator()
        scaffold = gen.generate_scaffold(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".gitignore").exists()
        assert (Path(tmp_dir) / "README.md").exists()
        assert (Path(tmp_dir) / ".env.example").exists()
        assert (Path(tmp_dir) / "pyproject.toml").exists()
        assert (Path(tmp_dir) / "requirements.txt").exists()

    def test_generate_all(self, ctx, tmp_dir):
        gen = ClaudeCodeGenerator()
        result = gen.generate_all(ctx, tmp_dir)
        assert "config" in result
        assert "skills" in result
        assert "hooks" in result
        assert "agents" in result
        assert "scaffold" in result


class TestCursorGenerator:
    def test_generate_config(self, ctx, tmp_dir):
        gen = CursorGenerator()
        content = gen.generate_config(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".cursorrules").exists()
        assert "test-project" in content

    def test_generate_skills(self, ctx, tmp_dir):
        gen = CursorGenerator()
        skills = gen.generate_skills(ctx, tmp_dir)
        assert "commit-message" in skills
        assert "pr-review" in skills

    def test_hooks_empty(self, ctx, tmp_dir):
        gen = CursorGenerator()
        hooks = gen.generate_hooks(ctx, tmp_dir)
        assert "note" in hooks


class TestCodexGenerator:
    def test_generate_config(self, ctx, tmp_dir):
        gen = CodexGenerator()
        content = gen.generate_config(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".openai" / "instructions.md").exists()
        assert "test-project" in content


class TestCopilotGenerator:
    def test_generate_config(self, ctx, tmp_dir):
        gen = CopilotGenerator()
        content = gen.generate_config(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".github" / "copilot-instructions.md").exists()
        assert "test-project" in content


class TestRegistry:
    def test_all_tools_registered(self):
        assert "claude-code" in ALL_TOOLS
        assert "cursor" in ALL_TOOLS
        assert "codex" in ALL_TOOLS
        assert "copilot" in ALL_TOOLS

    def test_get_generator(self):
        gen = get_generator("claude-code")
        assert isinstance(gen, ClaudeCodeGenerator)

        gen = get_generator("cursor")
        assert isinstance(gen, CursorGenerator)

    def test_get_all_generators(self):
        generators = get_all_generators()
        assert len(generators) == 8

    def test_invalid_tool_name(self):
        with pytest.raises(ValueError):
            get_generator("invalid-tool")
