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
        assert len(generators) >= 10  # 8 original + gemini + agents-md

    def test_invalid_tool_name(self):
        with pytest.raises(ValueError):
            get_generator("invalid-tool")


class TestGeminiGenerator:
    def test_generate_config(self, ctx, tmp_dir):
        from vcsx.generators.gemini import GeminiGenerator
        gen = GeminiGenerator()
        assert gen.name == "gemini"
        path = gen.generate_config(ctx, tmp_dir)
        assert (Path(tmp_dir) / "GEMINI.md").exists()
        content = (Path(tmp_dir) / "GEMINI.md").read_text()
        assert "test-project" in content
        assert "Gemini CLI" in content

    def test_data_pipeline_guidance(self, tmp_dir):
        from vcsx.generators.gemini import GeminiGenerator
        ctx = ProjectContext(
            project_name="scraper",
            project_type="data-pipeline",
            language="python",
        )
        gen = GeminiGenerator()
        gen.generate_config(ctx, tmp_dir)
        content = (Path(tmp_dir) / "GEMINI.md").read_text()
        assert "Data Pipeline" in content
        assert "SQLite" in content


class TestAgentsMdGenerator:
    def test_generate_config(self, ctx, tmp_dir):
        from vcsx.generators.agents_md import AgentsMdGenerator
        gen = AgentsMdGenerator()
        assert gen.name == "agents-md"
        path = gen.generate_config(ctx, tmp_dir)
        assert (Path(tmp_dir) / "AGENTS.md").exists()
        content = (Path(tmp_dir) / "AGENTS.md").read_text()
        assert "test-project" in content
        assert "pytest" in content
        assert "agents.md" in content.lower()

    def test_forbidden_actions(self, tmp_dir):
        from vcsx.generators.agents_md import AgentsMdGenerator
        ctx = ProjectContext(
            project_name="proj",
            language="python",
            forbidden_actions="kubectl delete, helm uninstall",
        )
        gen = AgentsMdGenerator()
        gen.generate_config(ctx, tmp_dir)
        content = (Path(tmp_dir) / "AGENTS.md").read_text()
        assert "kubectl delete" in content


class TestClaudeIgnore:
    def test_claudeignore_generated(self, ctx, tmp_dir):
        gen = ClaudeCodeGenerator()
        gen.generate_scaffold(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".claudeignore").exists()
        content = (Path(tmp_dir) / ".claudeignore").read_text()
        assert "node_modules/" in content
        assert "__pycache__/" in content
        assert ".env" in content

    def test_data_pipeline_extra_patterns(self, tmp_dir):
        ctx = ProjectContext(
            project_name="pipeline",
            project_type="data-pipeline",
            language="python",
        )
        gen = ClaudeCodeGenerator()
        gen.generate_scaffold(ctx, tmp_dir)
        content = (Path(tmp_dir) / ".claudeignore").read_text()
        assert "data/raw/" in content


class TestRegistryUpdated:
    def test_gemini_in_registry(self):
        gen = get_generator("gemini")
        assert gen is not None
        assert gen.name == "gemini"

    def test_agents_md_in_registry(self):
        gen = get_generator("agents-md")
        assert gen is not None
        assert gen.name == "agents-md"

    def test_all_tools_count(self):
        # Should have at least 10 tools now
        assert len(ALL_TOOLS) >= 10


class TestWindsurfNewFormat:
    def test_windsurf_rules_dir_created(self, ctx, tmp_dir):
        from vcsx.generators.windsurf import WindsurfGenerator
        gen = WindsurfGenerator()
        gen.generate_config(ctx, tmp_dir)
        rules_dir = Path(tmp_dir) / ".windsurf" / "rules"
        assert rules_dir.exists()
        assert (rules_dir / "core-conventions.md").exists()
        assert (rules_dir / "security.md").exists()
        assert (rules_dir / "testing.md").exists()

    def test_api_rules_generated(self, ctx, tmp_dir):
        from vcsx.generators.windsurf import WindsurfGenerator
        gen = WindsurfGenerator()
        gen.generate_config(ctx, tmp_dir)
        api_rules = Path(tmp_dir) / ".windsurf" / "rules" / "api-conventions.md"
        assert api_rules.exists()


class TestCopilotScopedInstructions:
    def test_scoped_instructions_created(self, ctx, tmp_dir):
        gen = CopilotGenerator()
        gen.generate_config(ctx, tmp_dir)
        instructions_dir = Path(tmp_dir) / ".github" / "instructions"
        assert instructions_dir.exists()
        assert (instructions_dir / "code-style.instructions.md").exists()
        assert (instructions_dir / "testing.instructions.md").exists()
        assert (instructions_dir / "security.instructions.md").exists()

    def test_applyto_frontmatter(self, ctx, tmp_dir):
        gen = CopilotGenerator()
        gen.generate_config(ctx, tmp_dir)
        content = (Path(tmp_dir) / ".github" / "instructions" / "security.instructions.md").read_text()
        assert "applyTo" in content
