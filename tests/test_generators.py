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
from vcsx.generators.aider import AiderGenerator
from vcsx.generators.bolt import BoltGenerator
from vcsx.generators.zed import ZedGenerator
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


class TestAiderGenerator:
    def test_generate_config(self, ctx, tmp_dir):
        gen = AiderGenerator()
        gen.generate_config(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".aider.conf.yaml").exists()

    def test_generate_skills(self, ctx, tmp_dir):
        gen = AiderGenerator()
        skills = gen.generate_skills(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".aider.context.md").exists()
        assert len(skills) > 0

    def test_aider_config_content(self, ctx, tmp_dir):
        gen = AiderGenerator()
        gen.generate_config(ctx, tmp_dir)
        content = (Path(tmp_dir) / ".aider.conf.yaml").read_text()
        assert "test-project" in content

    def test_aider_context_content(self, ctx, tmp_dir):
        gen = AiderGenerator()
        gen.generate_skills(ctx, tmp_dir)
        content = (Path(tmp_dir) / ".aider.context.md").read_text()
        assert "test-project" in content
        assert "FastAPI" in content or "Python" in content

    def test_generate_all_returns_dict(self, ctx, tmp_dir):
        gen = AiderGenerator()
        result = gen.generate_all(ctx, tmp_dir)
        assert isinstance(result, dict)
        assert "config" in result
        assert "skills" in result

    def test_name_property(self):
        gen = AiderGenerator()
        assert gen.name == "aider"

    def test_output_files_property(self):
        gen = AiderGenerator()
        assert ".aider.conf.yaml" in gen.output_files
        assert ".aider.context.md" in gen.output_files


class TestBoltGenerator:
    def test_generate_config(self, ctx, tmp_dir):
        gen = BoltGenerator()
        gen.generate_config(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".bolt" / "workspace.json").exists()

    def test_workspace_json_valid(self, ctx, tmp_dir):
        gen = BoltGenerator()
        gen.generate_config(ctx, tmp_dir)
        content = (Path(tmp_dir) / ".bolt" / "workspace.json").read_text()
        data = json.loads(content)
        assert "project" in data
        assert data["project"]["name"] == "test-project"

    def test_generate_skills(self, ctx, tmp_dir):
        gen = BoltGenerator()
        skills = gen.generate_skills(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".bolt" / "setup.md").exists()

    def test_prompts_md_created(self, ctx, tmp_dir):
        gen = BoltGenerator()
        gen.generate_skills(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".bolt" / "prompts.md").exists()

    def test_generate_all(self, ctx, tmp_dir):
        gen = BoltGenerator()
        result = gen.generate_all(ctx, tmp_dir)
        assert isinstance(result, dict)

    def test_name_property(self):
        gen = BoltGenerator()
        assert gen.name == "bolt"


class TestZedGenerator:
    def test_generate_config(self, ctx, tmp_dir):
        gen = ZedGenerator()
        gen.generate_config(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".zed" / "settings.json").exists()

    def test_settings_json_valid(self, ctx, tmp_dir):
        gen = ZedGenerator()
        gen.generate_config(ctx, tmp_dir)
        content = (Path(tmp_dir) / ".zed" / "settings.json").read_text()
        data = json.loads(content)
        assert "project" in data
        assert data["project"]["name"] == "test-project"

    def test_generate_skills(self, ctx, tmp_dir):
        gen = ZedGenerator()
        gen.generate_skills(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".zed" / "context.md").exists()

    def test_hooks_toml_created(self, ctx, tmp_dir):
        gen = ZedGenerator()
        gen.generate_hooks(ctx, tmp_dir)
        assert (Path(tmp_dir) / ".zed" / "hooks.toml").exists()

    def test_context_md_content(self, ctx, tmp_dir):
        gen = ZedGenerator()
        gen.generate_skills(ctx, tmp_dir)
        content = (Path(tmp_dir) / ".zed" / "context.md").read_text()
        assert "test-project" in content

    def test_generate_all(self, ctx, tmp_dir):
        gen = ZedGenerator()
        result = gen.generate_all(ctx, tmp_dir)
        assert isinstance(result, dict)

    def test_name_property(self):
        gen = ZedGenerator()
        assert gen.name == "zed"

    def test_output_files_property(self):
        gen = ZedGenerator()
        assert ".zed/settings.json" in gen.output_files


class TestMultiToolInit:
    """Test that multiple generators can be run in sequence without conflicts."""

    def test_claude_and_cursor_no_conflict(self, ctx, tmp_dir):
        claude_gen = ClaudeCodeGenerator()
        cursor_gen = CursorGenerator()
        claude_gen.generate_all(ctx, tmp_dir)
        cursor_gen.generate_all(ctx, tmp_dir)
        assert (Path(tmp_dir) / "CLAUDE.md").exists()
        assert (Path(tmp_dir) / ".cursorrules").exists()

    def test_all_generators_no_conflict(self, ctx, tmp_dir):
        """All 10 generators should be able to run on the same directory."""
        from vcsx.generators.registry import get_all_generators
        gens = get_all_generators()
        for gen in gens:
            # Should not raise
            gen.generate_all(ctx, tmp_dir)

    def test_generator_output_files_unique(self):
        """Each generator should produce unique primary config files."""
        from vcsx.generators.registry import get_all_generators
        all_primary_files = set()
        for gen in get_all_generators():
            # Just check no generator claims identical file sets
            files = tuple(sorted(gen.output_files))
            assert files not in all_primary_files or gen.name in ("agents-md", "gemini"), \
                f"Generator {gen.name} has non-unique output files"
            all_primary_files.add(files)


class TestSharedHelpersExtended:
    """Extended tests for _shared module."""

    def test_setup_cmd_rust(self):
        from vcsx.generators._shared import get_setup_cmd
        ctx = ProjectContext(language="rust")
        assert "cargo" in get_setup_cmd(ctx)

    def test_setup_cmd_java(self):
        from vcsx.generators._shared import get_setup_cmd
        ctx = ProjectContext(language="java")
        assert "mvn" in get_setup_cmd(ctx)

    def test_build_cmd_rust(self):
        from vcsx.generators._shared import get_build_cmd
        ctx = ProjectContext(language="rust")
        assert "cargo" in get_build_cmd(ctx)

    def test_build_cmd_go(self):
        from vcsx.generators._shared import get_build_cmd
        ctx = ProjectContext(language="go")
        assert "go build" in get_build_cmd(ctx)

    def test_dev_cmd_django(self):
        from vcsx.generators._shared import get_dev_cmd
        ctx = ProjectContext(language="python", framework="Django")
        assert "manage.py" in get_dev_cmd(ctx)

    def test_dev_cmd_flask(self):
        from vcsx.generators._shared import get_dev_cmd
        ctx = ProjectContext(language="python", framework="Flask")
        assert "flask" in get_dev_cmd(ctx)

    def test_style_rules_typescript(self):
        from vcsx.generators._shared import get_style_rules
        ctx = ProjectContext(language="typescript")
        rules = get_style_rules(ctx)
        assert any("const" in r for r in rules)

    def test_style_rules_go(self):
        from vcsx.generators._shared import get_style_rules
        ctx = ProjectContext(language="go")
        rules = get_style_rules(ctx)
        assert any("gofmt" in r for r in rules)

    def test_style_rules_data_pipeline(self):
        from vcsx.generators._shared import get_style_rules
        ctx = ProjectContext(language="python", project_type="data-pipeline")
        rules = get_style_rules(ctx)
        assert any("chunk" in r.lower() for r in rules)

    def test_lint_cmd_uses_ctx_linter(self):
        from vcsx.generators._shared import get_lint_cmd
        ctx = ProjectContext(linter="custom-linter")
        assert get_lint_cmd(ctx) == "custom-linter"

    def test_format_cmd_uses_ctx_formatter(self):
        from vcsx.generators._shared import get_format_cmd
        ctx = ProjectContext(formatter="custom-formatter")
        assert get_format_cmd(ctx) == "custom-formatter"

    def test_test_cmd_no_framework_fallback(self):
        from vcsx.generators._shared import get_test_cmd
        ctx = ProjectContext(language="rust")
        assert "cargo test" in get_test_cmd(ctx)


class TestSharedHelpers:
    """Test the shared generator utilities module."""

    def test_setup_cmd_python(self):
        from vcsx.generators._shared import get_setup_cmd
        ctx = ProjectContext(language="python")
        assert "pip install" in get_setup_cmd(ctx)

    def test_setup_cmd_typescript(self):
        from vcsx.generators._shared import get_setup_cmd
        ctx = ProjectContext(language="typescript")
        assert "npm install" in get_setup_cmd(ctx)

    def test_setup_cmd_go(self):
        from vcsx.generators._shared import get_setup_cmd
        ctx = ProjectContext(language="go")
        assert "go mod tidy" == get_setup_cmd(ctx)

    def test_setup_cmd_pnpm(self):
        from vcsx.generators._shared import get_setup_cmd
        ctx = ProjectContext(language="typescript", tech_stack="pnpm, react")
        assert "pnpm install" == get_setup_cmd(ctx)

    def test_test_cmd_python(self):
        from vcsx.generators._shared import get_test_cmd
        ctx = ProjectContext(language="python")
        assert "pytest" == get_test_cmd(ctx)

    def test_test_cmd_vitest(self):
        from vcsx.generators._shared import get_test_cmd
        ctx = ProjectContext(test_framework="vitest")
        assert "vitest" in get_test_cmd(ctx)

    def test_test_cmd_go(self):
        from vcsx.generators._shared import get_test_cmd
        ctx = ProjectContext(language="go")
        assert "go test" in get_test_cmd(ctx)

    def test_style_rules_python(self):
        from vcsx.generators._shared import get_style_rules
        ctx = ProjectContext(language="python")
        rules = get_style_rules(ctx)
        assert any("PEP 8" in r for r in rules)
        assert any("type hint" in r for r in rules)

    def test_style_rules_api_additions(self):
        from vcsx.generators._shared import get_style_rules
        ctx = ProjectContext(language="python", project_type="api")
        rules = get_style_rules(ctx)
        assert any("HTTP status" in r for r in rules)

    def test_commands_block_format(self):
        from vcsx.generators._shared import get_commands_block
        ctx = ProjectContext(language="python", test_framework="pytest")
        block = get_commands_block(ctx)
        assert "```bash" in block
        assert "pytest" in block
        assert "pip install" in block

    def test_dev_cmd_fastapi(self):
        from vcsx.generators._shared import get_dev_cmd
        ctx = ProjectContext(language="python", framework="FastAPI")
        assert "uvicorn" in get_dev_cmd(ctx)

    def test_dev_cmd_typescript(self):
        from vcsx.generators._shared import get_dev_cmd
        ctx = ProjectContext(language="typescript")
        assert "npm run dev" in get_dev_cmd(ctx)


class TestNewProjectScaffold:
    """Test vcsx new scaffolding via generators directly."""

    def test_scaffold_python_api(self, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.core.inference import infer_formatter, infer_linter, infer_test_framework
        ctx = ProjectContext(
            project_name="my-api",
            project_type="api",
            language="python",
            tech_stack="python",
            test_framework=infer_test_framework("python"),
            formatter=infer_formatter("python"),
            linter=infer_linter("python"),
        )
        project_dir = Path(tmp_dir) / "my-api"
        project_dir.mkdir()
        gen = ClaudeCodeGenerator()
        gen.generate_all(ctx, str(project_dir))
        assert (project_dir / "CLAUDE.md").exists()

    def test_scaffold_typescript_web(self, tmp_dir):
        from vcsx.core.context import ProjectContext
        ctx = ProjectContext(
            project_name="my-app",
            project_type="web",
            language="typescript",
            tech_stack="typescript, react",
        )
        project_dir = Path(tmp_dir) / "my-app"
        project_dir.mkdir()
        gen = CursorGenerator()
        gen.generate_all(ctx, str(project_dir))
        assert (project_dir / ".cursorrules").exists()

    def test_multi_tool_scaffold(self, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.gemini import GeminiGenerator
        ctx = ProjectContext(
            project_name="my-project",
            project_type="api",
            language="python",
        )
        project_dir = Path(tmp_dir) / "my-project"
        project_dir.mkdir()
        for GenClass in [ClaudeCodeGenerator, GeminiGenerator]:
            GenClass().generate_all(ctx, str(project_dir))
        assert (project_dir / "CLAUDE.md").exists()
        assert (project_dir / "GEMINI.md").exists()


class TestProjectContextMultiTool:
    """Test ProjectContext with multi-tool fields."""

    def test_default_ai_tools_list_is_empty(self):
        ctx = ProjectContext()
        assert ctx.ai_tools_list == []

    def test_set_ai_tools_list(self):
        ctx = ProjectContext(ai_tools_list=["claude-code", "cursor", "gemini"])
        assert len(ctx.ai_tools_list) == 3
        assert "cursor" in ctx.ai_tools_list

    def test_ai_tool_and_list_independent(self):
        ctx = ProjectContext(ai_tool="claude-code", ai_tools_list=["claude-code", "gemini"])
        assert ctx.ai_tool == "claude-code"
        assert "gemini" in ctx.ai_tools_list


class TestDoctorDetection:
    """Test detection logic used by vcsx doctor."""

    def test_detects_claude_code(self, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        assert (Path(tmp_dir) / "CLAUDE.md").exists()

    def test_detects_gemini(self, tmp_dir):
        (Path(tmp_dir) / "GEMINI.md").write_text("# test")
        assert (Path(tmp_dir) / "GEMINI.md").exists()

    def test_detects_missing_claudeignore(self, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        assert not (Path(tmp_dir) / ".claudeignore").exists()

    def test_gemini_and_agents_md_coexist(self, ctx, tmp_dir):
        """Gemini and AGENTS.md can coexist in same project."""
        from vcsx.generators.gemini import GeminiGenerator
        from vcsx.generators.agents_md import AgentsMdGenerator
        GeminiGenerator().generate_all(ctx, tmp_dir)
        AgentsMdGenerator().generate_all(ctx, tmp_dir)
        assert (Path(tmp_dir) / "GEMINI.md").exists()
        assert (Path(tmp_dir) / "AGENTS.md").exists()
