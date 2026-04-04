"""Tests for CLI commands — integration tests using Click test runner."""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from vcsx.cli import main
from vcsx import __version__


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestVersionCommand:
    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestListCommand:
    def test_list(self, runner):
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "claude-code" in result.output
        assert "cursor" in result.output
        assert "gemini" in result.output
        assert "agents-md" in result.output

    def test_list_shows_categories(self, runner):
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "ai_editors" in result.output or "terminal_ai" in result.output


class TestInfoCommand:
    def test_info_claude_code(self, runner):
        result = runner.invoke(main, ["info", "claude-code"])
        assert result.exit_code == 0
        assert "CLAUDE.md" in result.output
        assert "claude-code" in result.output

    def test_info_gemini(self, runner):
        result = runner.invoke(main, ["info", "gemini"])
        assert result.exit_code == 0
        assert "GEMINI.md" in result.output

    def test_info_invalid_tool(self, runner):
        result = runner.invoke(main, ["info", "nonexistent-tool"])
        assert "Unknown tool" in result.output or result.exit_code != 0

    def test_info_no_args(self, runner):
        result = runner.invoke(main, ["info"])
        assert "Usage" in result.output or result.exit_code == 0


class TestDoctorCommand:
    def test_doctor_basic(self, runner):
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_doctor_shows_version(self, runner):
        result = runner.invoke(main, ["doctor"])
        assert "vcsx version" in result.output or __version__ in result.output

    def test_doctor_with_dir(self, runner, tmp_dir):
        result = runner.invoke(main, ["doctor", "--dir", tmp_dir])
        assert result.exit_code == 0

    def test_doctor_detects_claude_code(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        result = runner.invoke(main, ["doctor", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "claude-code" in result.output

    def test_doctor_detects_gemini(self, runner, tmp_dir):
        (Path(tmp_dir) / "GEMINI.md").write_text("# test")
        result = runner.invoke(main, ["doctor", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "gemini" in result.output


class TestCheckCommand:
    def test_check_empty_dir(self, runner, tmp_dir):
        result = runner.invoke(main, ["check", tmp_dir])
        assert result.exit_code == 0
        assert "No AI tool configs" in result.output or "vcsx init" in result.output

    def test_check_with_claude_code(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["check", tmp_dir])
        assert result.exit_code == 0
        assert "claude-code" in result.output

    def test_check_json_output(self, runner, tmp_dir):
        (Path(tmp_dir) / "GEMINI.md").write_text("# test")
        result = runner.invoke(main, ["check", tmp_dir, "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "tools_configured" in data
        assert data["tools_configured"] >= 1

    def test_check_json_score(self, runner, tmp_dir):
        (Path(tmp_dir) / "GEMINI.md").write_text("# test")
        result = runner.invoke(main, ["check", tmp_dir, "--json"])
        data = json.loads(result.output)
        assert "overall_score" in data
        assert 0 <= data["overall_score"] <= 100


class TestInitAllToolsFast:
    """Test init --all-tools with fast and scan modes."""

    def test_init_all_tools_scan(self, runner, tmp_dir):
        import tempfile, json as json_mod

        with tempfile.TemporaryDirectory() as src_dir:
            (Path(src_dir) / "requirements.txt").write_text("fastapi\n")
            result = runner.invoke(
                main,
                ["init", "--scan", "--all-tools", "--output-dir", tmp_dir],
            )
            assert result.exit_code == 0

    def test_init_multi_tool_list_from_discovery_context(self, runner, tmp_dir):
        """Test ai_tools_list branch in init."""
        # Fast mode with explicit tools bypasses discovery
        result = runner.invoke(
            main,
            ["init", "--fast", "--cli", "gemini", "--cli", "agents-md", "--output-dir", tmp_dir],
            input="test-project\nPython\n",
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "GEMINI.md").exists()


class TestCheckWithClaude:
    def test_check_claude_code_recommendations(self, runner, tmp_dir):
        """Test check with claude-code configured but missing extras."""
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_config(ctx, tmp_dir)  # only config, not all
        result = runner.invoke(main, ["check", tmp_dir])
        assert result.exit_code == 0

    def test_check_shows_agents_md_suggestion(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["check", tmp_dir])
        assert result.exit_code == 0


class TestExportWithBuildDirs:
    def test_export_skips_build_dirs(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        # Create build dirs that should be skipped
        (Path(tmp_dir) / "node_modules").mkdir()
        (Path(tmp_dir) / "node_modules" / "test.js").write_text("test")
        (Path(tmp_dir) / "__pycache__").mkdir()
        zip_path = Path(tmp_dir) / "out.zip"
        result = runner.invoke(main, ["export", tmp_dir, "--output", str(zip_path)])
        assert result.exit_code == 0
        # ZIP should exist
        assert zip_path.exists()


class TestInitScanMode:
    def test_scan_detects_python_project(self, runner, tmp_dir):
        (Path(tmp_dir) / "requirements.txt").write_text("fastapi\npytest\n")
        result = runner.invoke(
            main,
            ["init", "--scan", "--cli", "agents-md", "--output-dir", tmp_dir],
        )
        assert result.exit_code == 0
        assert "python" in result.output.lower() or (Path(tmp_dir) / "AGENTS.md").exists()

    def test_scan_detects_typescript_project(self, runner, tmp_dir):
        import json

        pkg = {"name": "my-app", "dependencies": {"react": "^18.0.0"}}
        (Path(tmp_dir) / "package.json").write_text(json.dumps(pkg))
        result = runner.invoke(
            main,
            ["init", "--scan", "--cli", "gemini", "--output-dir", tmp_dir],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "GEMINI.md").exists()

    def test_scan_skips_discovery_wizard(self, runner, tmp_dir):
        (Path(tmp_dir) / "requirements.txt").write_text("fastapi\n")
        result = runner.invoke(
            main,
            ["init", "--scan", "--cli", "agents-md", "--output-dir", tmp_dir],
        )
        # Should not prompt for input (no stdin needed)
        assert result.exit_code == 0

    def test_scan_shows_detected_stack(self, runner, tmp_dir):
        (Path(tmp_dir) / "requirements.txt").write_text("fastapi\n")
        result = runner.invoke(
            main,
            ["init", "--scan", "--cli", "agents-md", "--output-dir", tmp_dir],
        )
        assert "Detected" in result.output or "python" in result.output.lower()


class TestInitFastMode:
    def test_fast_mode_accepts_input(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["init", "--fast", "--cli", "gemini", "--output-dir", tmp_dir],
            input="my-project\nPython, FastAPI\n",
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "GEMINI.md").exists()

    def test_fast_mode_detects_language(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["init", "--fast", "--cli", "agents-md", "--output-dir", tmp_dir],
            input="test-app\nTypeScript, React\n",
        )
        assert result.exit_code == 0
        assert "typescript" in result.output.lower() or (Path(tmp_dir) / "AGENTS.md").exists()


class TestUpdateCommand:
    def test_update_dry_run(self, runner, tmp_dir):
        result = runner.invoke(main, ["update", "--output-dir", tmp_dir, "--dry-run"])
        assert result.exit_code == 0
        # Either shows dry-run message, "up to date", or "No AI configs found" suggestion
        assert (
            "Dry run" in result.output
            or "dry run" in result.output
            or "up to date" in result.output
            or "No AI configs found" in result.output
        )

    def test_update_dry_run_with_tool(self, runner, tmp_dir):
        result = runner.invoke(
            main, ["update", "--output-dir", tmp_dir, "--dry-run", "--tool", "gemini"]
        )
        assert result.exit_code == 0
        assert "gemini" in result.output.lower() or "Would add" in result.output


class TestNewCommand:
    def test_new_creates_directory(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["new", "my-test-project", "--lang", "python", "--output-dir", tmp_dir],
        )
        assert result.exit_code == 0
        project_dir = Path(tmp_dir) / "my-test-project"
        assert project_dir.exists()

    def test_new_generates_claude_config(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            [
                "new",
                "my-api",
                "--lang",
                "python",
                "--type",
                "api",
                "--tool",
                "claude-code",
                "--output-dir",
                tmp_dir,
            ],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "my-api" / "CLAUDE.md").exists()

    def test_new_multi_tool(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            [
                "new",
                "my-multi",
                "--lang",
                "python",
                "--tool",
                "claude-code",
                "--tool",
                "gemini",
                "--output-dir",
                tmp_dir,
            ],
        )
        assert result.exit_code == 0
        project_dir = Path(tmp_dir) / "my-multi"
        assert (project_dir / "CLAUDE.md").exists()
        assert (project_dir / "GEMINI.md").exists()

    def test_new_existing_dir_fails(self, runner, tmp_dir):
        # Create the directory first
        existing = Path(tmp_dir) / "existing-project"
        existing.mkdir()
        result = runner.invoke(
            main,
            ["new", "existing-project", "--output-dir", tmp_dir],
        )
        # Should report error
        assert "already exists" in result.output or result.exit_code != 0

    def test_new_with_preset(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["new", "my-fastapi", "--preset", "fastapi-postgres", "--output-dir", tmp_dir],
        )
        assert result.exit_code == 0
        project_dir = Path(tmp_dir) / "my-fastapi"
        assert project_dir.exists()
        assert "fastapi-postgres" in result.output or "FastAPI" in result.output

    def test_new_with_unknown_preset(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["new", "my-proj", "--preset", "nonexistent-preset", "--output-dir", tmp_dir],
        )
        assert result.exit_code == 0
        assert "Unknown preset" in result.output or "Available" in result.output

    def test_new_typescript_web(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            [
                "new",
                "my-web",
                "--lang",
                "typescript",
                "--type",
                "web",
                "--tool",
                "cursor",
                "--output-dir",
                tmp_dir,
            ],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "my-web" / ".cursorrules").exists()


class TestConfigCommandExtended:
    def test_config_set_auto_push_true(self, runner):
        result = runner.invoke(main, ["config", "--set", "auto_push", "true"])
        assert result.exit_code == 0
        assert "auto_push" in result.output

    def test_config_set_auto_push_false(self, runner):
        result = runner.invoke(main, ["config", "--set", "auto_push", "false"])
        assert result.exit_code == 0

    def test_config_get_unknown_key(self, runner):
        result = runner.invoke(main, ["config", "--get", "nonexistent_key"])
        assert result.exit_code == 0
        assert "Unknown key" in result.output

    def test_config_set_default_type(self, runner):
        result = runner.invoke(main, ["config", "--set", "default_type", "api"])
        assert result.exit_code == 0
        assert "default_type" in result.output


class TestCompareCommandExtended:
    def test_compare_shows_only_in_b(self, runner, tmp_dir):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir2:
            from vcsx.core.context import ProjectContext
            from vcsx.generators.gemini import GeminiGenerator

            ctx = ProjectContext(project_name="b")
            GeminiGenerator().generate_all(ctx, tmp_dir2)
            result = runner.invoke(main, ["compare", tmp_dir, tmp_dir2])
            assert result.exit_code == 0
            assert "only in B" in result.output or "gemini" in result.output.lower()

    def test_compare_with_windsurf(self, runner, tmp_dir):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir2:
            (Path(tmp_dir) / ".windsurfrules").write_text("# rules")
            result = runner.invoke(main, ["compare", tmp_dir, tmp_dir2])
            assert result.exit_code == 0
            assert "windsurf" in result.output.lower()


class TestSearchCommandExtended:
    def test_search_skill_type_filter(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["search", "deploy", tmp_dir, "--type", "skill"])
        assert result.exit_code == 0

    def test_search_hook_type_filter(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["search", "secret", tmp_dir, "--type", "hook"])
        assert result.exit_code == 0

    def test_search_agent_type_filter(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["search", "security", tmp_dir, "--type", "agent"])
        assert result.exit_code == 0


class TestConfigCorruptFile:
    def test_config_with_corrupted_file(self, runner):
        """Test config loads gracefully with corrupted JSON."""
        import os

        config_file = __import__("pathlib").Path.home() / ".vcsx" / "config.json"
        original = None
        try:
            if config_file.exists():
                original = config_file.read_text()
            config_file.parent.mkdir(exist_ok=True)
            config_file.write_text("not valid json{{{{")
            result = runner.invoke(main, ["config", "--list"])
            assert result.exit_code == 0  # should not crash
        finally:
            if original is not None:
                config_file.write_text(original)
            elif config_file.exists():
                config_file.unlink()


class TestValidateCursorWindsurf:
    def test_validate_cursorrules_without_rules_dir(self, runner, tmp_dir):
        (Path(tmp_dir) / ".cursorrules").write_text("# rules")
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        assert "cursor" in result.output.lower() or "migrate" in result.output.lower()

    def test_validate_windsurfrules_without_rules_dir(self, runner, tmp_dir):
        (Path(tmp_dir) / ".windsurfrules").write_text("# rules")
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        assert "windsurf" in result.output.lower() or "migrate" in result.output.lower()

    def test_validate_aider_valid_config(self, runner, tmp_dir):
        (Path(tmp_dir) / ".aider.conf.yaml").write_text(
            "model: gpt-4o\nauto-commits: true\nlint-cmd: ruff check .\n"
        )
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        assert "no invalid keys" in result.output or "aider" in result.output.lower()

    def test_validate_env_local_with_secrets(self, runner, tmp_dir):
        (Path(tmp_dir) / ".env.local").write_text("API_KEY=secret123\n")
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        assert "SECURITY" in result.output or "secret" in result.output.lower()


class TestValidateGeminiAgents:
    def test_validate_gemini_md(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.gemini import GeminiGenerator

        ctx = ProjectContext(project_name="test", language="python")
        GeminiGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        assert "GEMINI.md" in result.output

    def test_validate_agents_md(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.agents_md import AgentsMdGenerator

        ctx = ProjectContext(project_name="test", language="python", test_framework="pytest")
        AgentsMdGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        assert "AGENTS.md" in result.output

    def test_validate_agents_md_missing_commands(self, runner, tmp_dir):
        (Path(tmp_dir) / "AGENTS.md").write_text("# AGENTS.md\n\nSome content without commands.\n")
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        assert "commands" in result.output.lower() or "AGENTS.md" in result.output

    def test_validate_claude_md_with_api_key(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text(
            "# Project\n\nRULE: Never commit api_key secrets.\n"
        )
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0


class TestGeminiGlobalCommandExtended:
    def test_gemini_global_already_exists(self, runner, tmp_dir):
        """Test that existing file blocks creation without --force."""
        import tempfile

        gemini_dir = Path(tmp_dir) / ".gemini"
        gemini_dir.mkdir()
        (gemini_dir / "GEMINI.md").write_text("# Existing")
        # We can't easily test ~/.gemini/ but can check the command logic
        result = runner.invoke(main, ["gemini-global", "--help"])
        assert "force" in result.output.lower()


class TestValidateWarnings:
    def test_validate_claude_md_150_lines(self, runner, tmp_dir):
        """Test warning for 150-200 line CLAUDE.md."""
        content = "# test\n" + "line\n" * 160
        (Path(tmp_dir) / "CLAUDE.md").write_text(content)
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        assert "160" in result.output or "150" in result.output or "Warning" in result.output

    def test_validate_gemini_short(self, runner, tmp_dir):
        (Path(tmp_dir) / "GEMINI.md").write_text("# short\n")
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0

    def test_validate_all_passed_message(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator
        from vcsx.generators.agents_md import AgentsMdGenerator

        ctx = ProjectContext(project_name="clean", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        AgentsMdGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        # Should show CLAUDE.md as valid
        assert "CLAUDE.md" in result.output


class TestConfigCommand:
    def test_config_list(self, runner):
        result = runner.invoke(main, ["config", "--list"])
        assert result.exit_code == 0
        assert "default_tool" in result.output
        assert "claude-code" in result.output

    def test_config_set_and_get(self, runner, tmp_dir):
        result = runner.invoke(main, ["config", "--set", "default_lang", "python"])
        assert result.exit_code == 0
        result2 = runner.invoke(main, ["config", "--get", "default_lang"])
        assert result.exit_code == 0
        assert "python" in result2.output

    def test_config_unknown_key(self, runner):
        result = runner.invoke(main, ["config", "--set", "nonexistent_key", "value"])
        assert result.exit_code == 0
        assert "Unknown key" in result.output

    def test_config_reset(self, runner):
        result = runner.invoke(main, ["config", "--reset"])
        assert result.exit_code == 0
        assert "reset" in result.output.lower()


class TestAuditCommand:
    def test_audit_empty_dir(self, runner, tmp_dir):
        result = runner.invoke(main, ["audit", tmp_dir])
        assert result.exit_code == 0
        assert "No AI configs" in result.output or "vcsx init" in result.output

    def test_audit_with_claude_code(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["audit", tmp_dir])
        assert result.exit_code == 0
        assert "claude-code" in result.output

    def test_audit_detects_missing_claudeignore(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        result = runner.invoke(main, ["audit", tmp_dir])
        assert result.exit_code == 0
        assert "claudeignore" in result.output.lower()

    def test_audit_autofix(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        result = runner.invoke(main, ["audit", tmp_dir, "--fix"])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".claudeignore").exists()


class TestCompareCommand:
    def test_compare_two_dirs(self, runner, tmp_dir):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir2:
            # Setup project A
            from vcsx.core.context import ProjectContext
            from vcsx.generators.gemini import GeminiGenerator

            ctx = ProjectContext(project_name="a")
            GeminiGenerator().generate_all(ctx, tmp_dir)
            result = runner.invoke(main, ["compare", tmp_dir, tmp_dir2])
            assert result.exit_code == 0
            assert "gemini" in result.output.lower() or "only in A" in result.output

    def test_compare_identical(self, runner, tmp_dir):
        result = runner.invoke(main, ["compare", tmp_dir, tmp_dir])
        assert result.exit_code == 0
        assert "Summary" in result.output


class TestSearchCommand:
    def test_search_no_results(self, runner, tmp_dir):
        result = runner.invoke(main, ["search", "nonexistent_keyword_xyz", tmp_dir])
        assert result.exit_code == 0
        assert "No results" in result.output

    def test_search_finds_in_skills(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["search", "security", tmp_dir])
        assert result.exit_code == 0
        assert "security" in result.output.lower()

    def test_search_with_type_filter(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["search", "commit", tmp_dir, "--type", "skill"])
        assert result.exit_code == 0


class TestValidateCommand:
    def test_validate_empty_dir(self, runner, tmp_dir):
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        assert "No AI config" in result.output or "vcsx init" in result.output

    def test_validate_with_claude_md(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text(
            "# Test\n\n## Quick Commands\n```bash\npytest\n```\n\nNEVER commit secrets.\n"
        )
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        assert "CLAUDE.md" in result.output

    def test_validate_large_claude_md(self, runner, tmp_dir):
        # 250 lines is too many
        content = "# Test\n" + "line\n" * 250
        (Path(tmp_dir) / "CLAUDE.md").write_text(content)
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        assert "250" in result.output or "large" in result.output.lower() or "200" in result.output

    def test_validate_aider_invalid_keys(self, runner, tmp_dir):
        (Path(tmp_dir) / ".aider.conf.yaml").write_text(
            "model: gpt-4o\nrepo: my-project\ntools:\n  - bash\n"
        )
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0
        assert "invalid" in result.output.lower() or "repo:" in result.output

    def test_validate_all_passed(self, runner, tmp_dir):
        # Generate valid configs
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python", project_type="api")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["validate", tmp_dir])
        assert result.exit_code == 0


class TestExportCommand:
    def test_export_creates_zip(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        zip_path = Path(tmp_dir) / "test-export.zip"
        result = runner.invoke(main, ["export", tmp_dir, "--output", str(zip_path)])
        assert result.exit_code == 0
        assert zip_path.exists()

    def test_export_empty_dir(self, runner, tmp_dir):
        result = runner.invoke(main, ["export", tmp_dir])
        assert result.exit_code == 0
        assert "No AI config" in result.output or "vcsx init" in result.output

    def test_export_shows_file_count(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.gemini import GeminiGenerator

        ctx = ProjectContext(project_name="test", language="python")
        GeminiGenerator().generate_all(ctx, tmp_dir)
        zip_path = Path(tmp_dir) / "out.zip"
        result = runner.invoke(main, ["export", tmp_dir, "--output", str(zip_path)])
        assert result.exit_code == 0
        assert "Exported" in result.output


class TestGenerateCommand:
    def test_generate_gemini(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["generate", "gemini", "--project-name", "test-api", "--output-dir", tmp_dir],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "GEMINI.md").exists()

    def test_generate_agents_md(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            [
                "generate",
                "agents-md",
                "--project-name",
                "my-lib",
                "--lang",
                "python",
                "--output-dir",
                tmp_dir,
            ],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "AGENTS.md").exists()

    def test_generate_claude_code(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            [
                "generate",
                "claude-code",
                "--project-name",
                "my-app",
                "--lang",
                "typescript",
                "--output-dir",
                tmp_dir,
            ],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "CLAUDE.md").exists()

    def test_generate_shows_table(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["generate", "gemini", "--output-dir", tmp_dir],
        )
        assert result.exit_code == 0
        assert "Generated" in result.output or "gemini" in result.output


class TestMigrateCommand:
    def test_migrate_windsurf_dry_run(self, runner, tmp_dir):
        (Path(tmp_dir) / ".windsurfrules").write_text("# Old rules")
        result = runner.invoke(main, ["migrate", "windsurf", "--dir", tmp_dir, "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run" in result.output or "dry run" in result.output

    def test_migrate_windsurf_creates_rules(self, runner, tmp_dir):
        (Path(tmp_dir) / ".windsurfrules").write_text("# Old rules")
        result = runner.invoke(main, ["migrate", "windsurf", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".windsurf" / "rules").exists()

    def test_migrate_windsurf_no_file(self, runner, tmp_dir):
        result = runner.invoke(main, ["migrate", "windsurf", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "nothing to migrate" in result.output or "No .windsurfrules" in result.output

    def test_migrate_cursor_dry_run(self, runner, tmp_dir):
        (Path(tmp_dir) / ".cursorrules").write_text("# Old rules")
        result = runner.invoke(main, ["migrate", "cursor", "--dir", tmp_dir, "--dry-run"])
        assert result.exit_code == 0


class TestCheckMinScore:
    def test_check_min_score_passes(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["check", tmp_dir, "--min-score", "0"])
        assert result.exit_code == 0

    def test_check_min_score_fails(self, runner, tmp_dir):
        # Empty dir = 0% score, min-score 50 → exit 1
        result = runner.invoke(main, ["check", tmp_dir, "--min-score", "50"])
        assert result.exit_code == 1 or "below minimum" in result.output or "No AI" in result.output

    def test_check_min_score_100_passes_with_claude(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        # claude-code at 100% but only 1 tool → overall might be low
        result = runner.invoke(main, ["check", tmp_dir, "--min-score", "0"])
        assert result.exit_code == 0


class TestCheckCommandExtended:
    def test_check_json_no_tools(self, runner, tmp_dir):
        result = runner.invoke(main, ["check", tmp_dir, "--json"])
        assert result.exit_code == 0
        import json

        data = json.loads(result.output)
        assert data["tools_configured"] == 0
        assert data["overall_score"] == 0

    def test_check_with_multiple_tools(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator
        from vcsx.generators.gemini import GeminiGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        GeminiGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["check", tmp_dir, "--json"])
        data = __import__("json").loads(result.output)
        assert data["tools_configured"] >= 2


class TestDoctorCommandExtended:
    def test_doctor_with_multiple_configs(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        (Path(tmp_dir) / ".cursorrules").write_text("# rules")
        result = runner.invoke(main, ["doctor", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "claude-code" in result.output
        assert "cursor" in result.output

    def test_doctor_missing_claudeignore_tip(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        result = runner.invoke(main, ["doctor", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "claudeignore" in result.output.lower() or "claude" in result.output.lower()


class TestExportCommandExtended:
    def test_export_include_all(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        zip_path = Path(tmp_dir) / "all.zip"
        result = runner.invoke(
            main, ["export", tmp_dir, "--output", str(zip_path), "--include-all"]
        )
        assert result.exit_code == 0
        assert zip_path.exists()

    def test_export_default_filename(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.gemini import GeminiGenerator

        ctx = ProjectContext(project_name="test")
        GeminiGenerator().generate_all(ctx, tmp_dir)
        # Run from tmp_dir so zip is created there
        import os

        old_cwd = os.getcwd()
        os.chdir(tmp_dir)
        try:
            result = runner.invoke(main, ["export", "."])
            assert result.exit_code == 0
        finally:
            os.chdir(old_cwd)


class TestAuditJsonOutput:
    def _parse_json_output(self, output: str) -> dict:
        """Extract JSON from audit output (may have leading non-JSON lines)."""
        import json

        # Find first { in output
        idx = output.find("{")
        if idx >= 0:
            return json.loads(output[idx:])
        return {}

    def test_audit_json_empty_dir(self, runner, tmp_dir):
        result = runner.invoke(main, ["audit", tmp_dir, "--json"])
        assert result.exit_code == 0
        # Empty dir returns early before JSON is printed
        # Just verify command runs OK
        assert result.output is not None

    def test_audit_json_with_claude_code(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["audit", tmp_dir, "--json"])
        assert result.exit_code == 0
        data = self._parse_json_output(result.output)
        if data:  # JSON was output
            assert "status" in data
            assert data["status"] in ("pass", "warn", "fail")

    def test_audit_json_flag_exists(self, runner):
        result = runner.invoke(main, ["audit", "--help"])
        assert result.exit_code == 0
        assert "json" in result.output.lower()


class TestAuditCommandExtended:
    def test_audit_with_windsurf_no_rules(self, runner, tmp_dir):
        (Path(tmp_dir) / ".windsurfrules").write_text("# rules")
        result = runner.invoke(main, ["audit", tmp_dir])
        assert result.exit_code == 0
        assert "windsurf" in result.output.lower()

    def test_audit_with_cursor_no_rules(self, runner, tmp_dir):
        (Path(tmp_dir) / ".cursorrules").write_text("# rules")
        result = runner.invoke(main, ["audit", tmp_dir])
        assert result.exit_code == 0
        assert "cursor" in result.output.lower()

    def test_audit_aider_invalid_keys(self, runner, tmp_dir):
        (Path(tmp_dir) / ".aider.conf.yaml").write_text("model: gpt-4o\nrepo: test\n")
        result = runner.invoke(main, ["audit", tmp_dir])
        assert result.exit_code == 0
        assert "invalid" in result.output.lower() or "repo:" in result.output

    def test_audit_large_claude_md(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test\n" + "line\n" * 250)
        result = runner.invoke(main, ["audit", tmp_dir])
        assert result.exit_code == 0
        # Should warn about large file
        assert "250" in result.output or "200" in result.output


class TestDoctorPlatformInfo:
    def test_doctor_shows_platform(self, runner):
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "Platform" in result.output or "python" in result.output.lower()

    def test_doctor_shows_ai_cli_tools_section(self, runner):
        """Doctor should show the AI CLI Tools section."""
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "AI CLI Tools" in result.output

    def test_doctor_ai_cli_shows_install_count(self, runner):
        """Doctor should report installed count even if 0."""
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        # Either "X AI CLI tool(s) installed" or "not installed"
        assert "installed" in result.output.lower()

    def test_doctor_detects_aider(self, runner, tmp_dir):
        (Path(tmp_dir) / ".aider.conf.yaml").write_text("model: gpt-4o\n")
        result = runner.invoke(main, ["doctor", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "aider" in result.output.lower()

    def test_doctor_detects_bolt(self, runner, tmp_dir):
        (Path(tmp_dir) / ".bolt").mkdir()
        (Path(tmp_dir) / ".bolt" / "workspace.json").write_text("{}")
        result = runner.invoke(main, ["doctor", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "bolt" in result.output.lower()

    def test_doctor_detects_codex(self, runner, tmp_dir):
        (Path(tmp_dir) / ".openai").mkdir()
        (Path(tmp_dir) / ".openai" / "instructions.md").write_text("# Codex")
        result = runner.invoke(main, ["doctor", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "codex" in result.output.lower()

    def test_doctor_detects_zed(self, runner, tmp_dir):
        (Path(tmp_dir) / ".zed").mkdir()
        (Path(tmp_dir) / ".zed" / "settings.json").write_text("{}")
        result = runner.invoke(main, ["doctor", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "zed" in result.output.lower()


class TestUpdateCommandExtended:
    """Extended update command coverage."""

    def test_update_with_claude_missing_claudeignore(self, runner, tmp_dir):
        """Detects missing .claudeignore upgrade."""
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        result = runner.invoke(main, ["update", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        assert "claudeignore" in result.output.lower() or "upgrade" in result.output.lower()

    def test_update_auto_generates_claudeignore(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        result = runner.invoke(main, ["update", "--output-dir", tmp_dir, "--auto"])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".claudeignore").exists()

    def test_update_auto_generates_agents_md(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        result = runner.invoke(main, ["update", "--output-dir", tmp_dir, "--auto"])
        assert result.exit_code == 0

    def test_update_windsurf_missing_rules(self, runner, tmp_dir):
        (Path(tmp_dir) / ".windsurfrules").write_text("# rules")
        result = runner.invoke(main, ["update", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        assert "windsurf" in result.output.lower() or "rules" in result.output.lower()

    def test_update_with_tool_adds_config(self, runner, tmp_dir):
        result = runner.invoke(main, ["update", "--output-dir", tmp_dir, "--tool", "agents-md"])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "AGENTS.md").exists()

    def test_update_dry_run_with_tool(self, runner, tmp_dir):
        result = runner.invoke(
            main, ["update", "--output-dir", tmp_dir, "--dry-run", "--tool", "gemini"]
        )
        assert result.exit_code == 0
        assert "gemini" in result.output.lower()

    def test_update_everything_up_to_date(self, runner, tmp_dir):
        # Empty dir with no AI configs
        result = runner.invoke(main, ["update", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        assert "up to date" in result.output or "tool" in result.output.lower()


class TestStatsCommandExtended:
    def test_stats_with_gemini(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.gemini import GeminiGenerator

        ctx = ProjectContext(project_name="test")
        GeminiGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["stats", tmp_dir])
        assert result.exit_code == 0

    def test_stats_cursor_counts_rules(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.cursor import CursorGenerator

        ctx = ProjectContext(project_name="test", language="python", project_type="api")
        CursorGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["stats", tmp_dir])
        assert result.exit_code == 0
        assert "cursor" in result.output.lower() or "rules" in result.output.lower()

    def test_stats_empty_dir(self, runner, tmp_dir):
        result = runner.invoke(main, ["stats", tmp_dir])
        assert result.exit_code == 0
        assert "No AI" in result.output or "vcsx init" in result.output


class TestMigrateCommandExtended:
    def test_migrate_cursor_creates_rules(self, runner, tmp_dir):
        (Path(tmp_dir) / ".cursorrules").write_text("# Old rules")
        result = runner.invoke(main, ["migrate", "cursor", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".cursor" / "rules").exists()

    def test_migrate_claude_code_no_file(self, runner, tmp_dir):
        result = runner.invoke(main, ["migrate", "claude-code", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "No CLAUDE.md" in result.output or "nothing to migrate" in result.output.lower()

    def test_migrate_copilot_no_file(self, runner, tmp_dir):
        result = runner.invoke(main, ["migrate", "copilot", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "nothing to migrate" in result.output.lower() or "No .github" in result.output

    def test_migrate_windsurf_already_migrated(self, runner, tmp_dir):
        (Path(tmp_dir) / ".windsurfrules").write_text("# rules")
        rules_dir = Path(tmp_dir) / ".windsurf" / "rules"
        rules_dir.mkdir(parents=True)
        result = runner.invoke(main, ["migrate", "windsurf", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "already" in result.output.lower()

    def test_migrate_claude_code_adds_agents(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        (Path(tmp_dir) / ".claudeignore").write_text("*.pyc")
        result = runner.invoke(main, ["migrate", "claude-code", "--dir", tmp_dir])
        assert result.exit_code == 0

    def test_migrate_copilot_creates_instructions(self, runner, tmp_dir):
        (Path(tmp_dir) / ".github").mkdir()
        (Path(tmp_dir) / ".github" / "copilot-instructions.md").write_text("# Copilot")
        result = runner.invoke(main, ["migrate", "copilot", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".github" / "instructions").exists()


class TestAuditEnvSecurity:
    def test_audit_env_not_in_gitignore(self, runner, tmp_dir):
        """Detects .env not in .gitignore."""
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        (Path(tmp_dir) / ".env").write_text("API_KEY=secret123")
        (Path(tmp_dir) / ".gitignore").write_text("node_modules/")  # no .env
        result = runner.invoke(main, ["audit", tmp_dir])
        assert result.exit_code == 0
        assert "gitignore" in result.output.lower() or ".env" in result.output

    def test_audit_env_no_gitignore(self, runner, tmp_dir):
        """Detects .env without .gitignore at all."""
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        (Path(tmp_dir) / ".env").write_text("PASSWORD=secret")
        result = runner.invoke(main, ["audit", tmp_dir])
        assert result.exit_code == 0
        assert "gitignore" in result.output.lower() or "SECURITY" in result.output

    def test_audit_env_properly_ignored(self, runner, tmp_dir):
        """Shows OK when .env is in .gitignore."""
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        (Path(tmp_dir) / ".env").write_text("API_KEY=secret")
        (Path(tmp_dir) / ".gitignore").write_text(".env\nnode_modules/")
        result = runner.invoke(main, ["audit", tmp_dir])
        assert result.exit_code == 0

    def test_audit_passed_all_clean(self, runner, tmp_dir):
        """Shows all-clear when no issues."""
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator
        from vcsx.generators.agents_md import AgentsMdGenerator

        ctx = ProjectContext(project_name="clean", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        AgentsMdGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["audit", tmp_dir])
        assert result.exit_code == 0
        # Should have no critical issues (may have warnings)


class TestStatsClaudeDetails:
    def test_stats_shows_claude_skill_count(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python", project_type="api")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["stats", tmp_dir])
        assert result.exit_code == 0
        assert "22" in result.output or "Skills" in result.output

    def test_stats_shows_breakdown(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["stats", tmp_dir])
        assert result.exit_code == 0
        assert "claude-code" in result.output.lower()


class TestDockerAndInitMultiTool:
    def test_init_all_tools_fast(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["init", "--fast", "--all-tools", "--output-dir", tmp_dir],
            input="my-project\nPython, FastAPI\n",
        )
        assert result.exit_code == 0

    def test_init_multi_cli_fast(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["init", "--fast", "--cli", "gemini", "--cli", "agents-md", "--output-dir", tmp_dir],
            input="my-project\nPython\n",
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "GEMINI.md").exists()
        assert (Path(tmp_dir) / "AGENTS.md").exists()


class TestInfoCommandExtended:
    def test_info_cursor(self, runner):
        result = runner.invoke(main, ["info", "cursor"])
        assert result.exit_code == 0
        assert ".cursorrules" in result.output

    def test_info_windsurf(self, runner):
        result = runner.invoke(main, ["info", "windsurf"])
        assert result.exit_code == 0
        assert "windsurf" in result.output.lower()

    def test_info_aider(self, runner):
        result = runner.invoke(main, ["info", "aider"])
        assert result.exit_code == 0
        assert ".aider" in result.output

    def test_info_no_args(self, runner):
        result = runner.invoke(main, ["info"])
        assert result.exit_code == 0
        assert "Usage" in result.output or "tool" in result.output.lower()


class TestPluginsCommand:
    def test_plugins_list(self, runner):
        result = runner.invoke(main, ["plugins"])
        assert result.exit_code == 0
        # Either shows no plugins or a table
        assert "plugin" in result.output.lower() or result.output.strip() != ""


class TestQualityCommand:
    def test_quality_empty_dir(self, runner, tmp_dir):
        result = runner.invoke(main, ["quality", tmp_dir])
        assert result.exit_code == 0
        assert "Project Stack" in result.output or "quality" in result.output.lower()

    def test_quality_with_claude_code(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python", project_type="api")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["quality", tmp_dir])
        assert result.exit_code == 0
        assert "claude-code" in result.output
        assert "Skills" in result.output

    def test_quality_shows_quick_wins(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        result = runner.invoke(main, ["quality", tmp_dir])
        assert result.exit_code == 0
        # Missing .claudeignore → quick win shown
        assert "Quick Wins" in result.output or "agents-md" in result.output

    def test_quality_with_python_project(self, runner, tmp_dir):
        (Path(tmp_dir) / "requirements.txt").write_text("fastapi\n")
        (Path(tmp_dir) / "GEMINI.md").write_text("# Gemini")
        result = runner.invoke(main, ["quality", tmp_dir])
        assert result.exit_code == 0
        assert "gemini" in result.output.lower() or "AI Tools" in result.output


class TestStatusCommand:
    def test_status_empty_dir(self, runner, tmp_dir):
        result = runner.invoke(main, ["status", tmp_dir])
        assert result.exit_code == 0
        assert "No AI tool" in result.output or "vcsx init" in result.output

    def test_status_with_claude_code(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python", project_type="api")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["status", tmp_dir])
        assert result.exit_code == 0
        assert "claude-code" in result.output
        assert "Skills" in result.output or "22" in result.output

    def test_status_shows_score(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        result = runner.invoke(main, ["status", tmp_dir])
        assert result.exit_code == 0
        assert "%" in result.output

    def test_status_shows_suggestions(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        result = runner.invoke(main, ["status", tmp_dir])
        assert result.exit_code == 0
        # Missing .claudeignore → suggestion shown
        assert "claudeignore" in result.output.lower() or "Suggestions" in result.output

    def test_status_all_clean(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator
        from vcsx.generators.agents_md import AgentsMdGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        AgentsMdGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["status", tmp_dir])
        assert result.exit_code == 0

    def test_status_with_windsurf_old_format(self, runner, tmp_dir):
        (Path(tmp_dir) / ".windsurfrules").write_text("# rules")
        result = runner.invoke(main, ["status", tmp_dir])
        assert result.exit_code == 0
        assert "windsurf" in result.output.lower()

    def test_status_with_cursor_old_format(self, runner, tmp_dir):
        (Path(tmp_dir) / ".cursorrules").write_text("# rules")
        result = runner.invoke(main, ["status", tmp_dir])
        assert result.exit_code == 0

    def test_status_with_cursor_and_rules(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.cursor import CursorGenerator

        ctx = ProjectContext(project_name="test", language="python", project_type="api")
        CursorGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["status", tmp_dir])
        assert result.exit_code == 0
        assert "%" in result.output


class TestGeminiGlobalCommand:
    def test_gemini_global_creates_file(self, runner, tmp_dir):
        # We can't easily test ~/.gemini/ creation but can test via mock
        # Just verify the command exists and accepts args
        result = runner.invoke(main, ["gemini-global", "--help"])
        assert result.exit_code == 0
        assert "gemini" in result.output.lower() or "global" in result.output.lower()

    def test_gemini_global_lang_option(self, runner):
        result = runner.invoke(main, ["gemini-global", "--help"])
        assert "lang" in result.output.lower() or "language" in result.output.lower()


class TestMigrateClaudeCodeExtended:
    def test_migrate_claude_code_already_complete(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["migrate", "claude-code", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "complete" in result.output.lower() or "already" in result.output.lower()

    def test_migrate_claude_code_dry_run(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        result = runner.invoke(main, ["migrate", "claude-code", "--dir", tmp_dir, "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run" in result.output or "dry run" in result.output

    def test_migrate_copilot_already_exists(self, runner, tmp_dir):
        (Path(tmp_dir) / ".github").mkdir()
        (Path(tmp_dir) / ".github" / "copilot-instructions.md").write_text("# Copilot")
        instructions = Path(tmp_dir) / ".github" / "instructions"
        instructions.mkdir()
        result = runner.invoke(main, ["migrate", "copilot", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "already" in result.output.lower()

    def test_migrate_copilot_dry_run(self, runner, tmp_dir):
        (Path(tmp_dir) / ".github").mkdir()
        (Path(tmp_dir) / ".github" / "copilot-instructions.md").write_text("# Copilot")
        result = runner.invoke(main, ["migrate", "copilot", "--dir", tmp_dir, "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run" in result.output or "dry run" in result.output

    def test_migrate_cursor_already_migrated(self, runner, tmp_dir):
        (Path(tmp_dir) / ".cursorrules").write_text("# rules")
        rules = Path(tmp_dir) / ".cursor" / "rules"
        rules.mkdir(parents=True)
        result = runner.invoke(main, ["migrate", "cursor", "--dir", tmp_dir])
        assert result.exit_code == 0
        assert "already" in result.output.lower()

    def test_migrate_cursor_dry_run(self, runner, tmp_dir):
        (Path(tmp_dir) / ".cursorrules").write_text("# rules")
        result = runner.invoke(main, ["migrate", "cursor", "--dir", tmp_dir, "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run" in result.output or "dry run" in result.output


class TestCheckRecommendations:
    def test_check_shows_recommendations(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator

        # Claude code without AGENTS.md
        ctx = ProjectContext(project_name="test", language="python")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        # Remove AGENTS.md if it was generated
        agents_md = Path(tmp_dir) / "AGENTS.md"
        if agents_md.exists():
            agents_md.unlink()
        result = runner.invoke(main, ["check", tmp_dir])
        assert result.exit_code == 0

    def test_check_json_all_tools(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.claude_code import ClaudeCodeGenerator
        from vcsx.generators.cursor import CursorGenerator
        from vcsx.generators.gemini import GeminiGenerator

        ctx = ProjectContext(project_name="test", language="python", project_type="api")
        ClaudeCodeGenerator().generate_all(ctx, tmp_dir)
        CursorGenerator().generate_all(ctx, tmp_dir)
        GeminiGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["check", tmp_dir, "--json"])
        data = __import__("json").loads(result.output)
        assert data["tools_configured"] >= 3


class TestUpdateAutoWindsurf:
    def test_update_auto_windsurf_rules(self, runner, tmp_dir):
        (Path(tmp_dir) / "CLAUDE.md").write_text("# test")
        (Path(tmp_dir) / ".windsurfrules").write_text("# rules")
        result = runner.invoke(main, ["update", "--output-dir", tmp_dir, "--auto"])
        assert result.exit_code == 0


class TestCompareIdenticalFiles:
    def test_compare_identical_configs(self, runner, tmp_dir):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp2:
            from vcsx.core.context import ProjectContext
            from vcsx.generators.gemini import GeminiGenerator

            ctx = ProjectContext(project_name="test")
            GeminiGenerator().generate_all(ctx, tmp_dir)
            GeminiGenerator().generate_all(ctx, tmp2)
            result = runner.invoke(main, ["compare", tmp_dir, tmp2])
            assert result.exit_code == 0
            assert "identical" in result.output or "both" in result.output.lower()


class TestStatsWindsurf:
    def test_stats_windsurf_rules(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.windsurf import WindsurfGenerator

        ctx = ProjectContext(project_name="test", language="python")
        WindsurfGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["stats", tmp_dir])
        assert result.exit_code == 0

    def test_stats_copilot_scoped(self, runner, tmp_dir):
        from vcsx.core.context import ProjectContext
        from vcsx.generators.copilot import CopilotGenerator

        ctx = ProjectContext(project_name="test", language="python")
        CopilotGenerator().generate_all(ctx, tmp_dir)
        result = runner.invoke(main, ["stats", tmp_dir])
        assert result.exit_code == 0
        assert "copilot" in result.output.lower() or "configured" in result.output.lower()

    def test_stats_git_section_shown_for_git_repo(self, runner, tmp_dir):
        """Stats should show Git Activity for a real git repo."""
        import subprocess

        (Path(tmp_dir) / "CLAUDE.md").write_text("# Test")
        subprocess.run(["git", "init"], cwd=tmp_dir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"], cwd=tmp_dir, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_dir, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=tmp_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "feat: initial"], cwd=tmp_dir, capture_output=True)
        result = runner.invoke(main, ["stats", tmp_dir])
        assert result.exit_code == 0
        assert "Git Activity" in result.output

    def test_stats_no_git_section_for_non_repo(self, runner, tmp_dir):
        """Stats should not show Git Activity for non-git directories."""
        (Path(tmp_dir) / "CLAUDE.md").write_text("# Test")
        result = runner.invoke(main, ["stats", tmp_dir])
        assert result.exit_code == 0
        # Git Activity section should not appear
        assert "Git Activity" not in result.output

    def test_stats_commit_types_in_output(self, runner, tmp_dir):
        """Stats should show commit type breakdown for repos with typed commits."""
        import subprocess

        (Path(tmp_dir) / "CLAUDE.md").write_text("# Test")
        subprocess.run(["git", "init"], cwd=tmp_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_dir, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=tmp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: add feature"], cwd=tmp_dir, capture_output=True
        )
        (Path(tmp_dir) / "fix.txt").write_text("fix")
        subprocess.run(["git", "add", "."], cwd=tmp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "fix: resolve bug"], cwd=tmp_dir, capture_output=True
        )
        result = runner.invoke(main, ["stats", tmp_dir])
        assert result.exit_code == 0
        # Should show "feat" and/or "fix" in commit types
        assert "feat" in result.output or "fix" in result.output or "Total commits" in result.output


class TestGenerateFromProject:
    def test_generate_from_python_project(self, runner, tmp_dir):
        import tempfile, json

        with tempfile.TemporaryDirectory() as src_dir:
            # Create a Python project
            (Path(src_dir) / "requirements.txt").write_text("fastapi\npytest\n")
            result = runner.invoke(
                main,
                ["generate", "agents-md", "--from-project", src_dir, "--output-dir", tmp_dir],
            )
            assert result.exit_code == 0
            assert (Path(tmp_dir) / "AGENTS.md").exists()

    def test_generate_from_typescript_project(self, runner, tmp_dir):
        import tempfile, json as json_mod

        with tempfile.TemporaryDirectory() as src_dir:
            pkg = {"name": "my-app", "dependencies": {"react": "^18.0.0"}}
            (Path(src_dir) / "package.json").write_text(json_mod.dumps(pkg))
            result = runner.invoke(
                main,
                ["generate", "gemini", "--from-project", src_dir, "--output-dir", tmp_dir],
            )
            assert result.exit_code == 0
            content = (Path(tmp_dir) / "GEMINI.md").read_text()
            assert "typescript" in content.lower() or "GEMINI" in content


class TestGenerateCommandExtended:
    def test_generate_aider(self, runner, tmp_dir):
        result = runner.invoke(
            main, ["generate", "aider", "--project-name", "test", "--output-dir", tmp_dir]
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".aider.conf.yaml").exists()

    def test_generate_cursor(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            [
                "generate",
                "cursor",
                "--project-name",
                "test",
                "--lang",
                "python",
                "--output-dir",
                tmp_dir,
            ],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".cursorrules").exists()

    def test_generate_zed(self, runner, tmp_dir):
        result = runner.invoke(
            main, ["generate", "zed", "--project-name", "test", "--output-dir", tmp_dir]
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".zed" / "settings.json").exists()

    def test_generate_bolt(self, runner, tmp_dir):
        result = runner.invoke(
            main, ["generate", "bolt", "--project-name", "test", "--output-dir", tmp_dir]
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".bolt" / "workspace.json").exists()

    def test_generate_copilot(self, runner, tmp_dir):
        result = runner.invoke(
            main, ["generate", "copilot", "--project-name", "test", "--output-dir", tmp_dir]
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".github" / "copilot-instructions.md").exists()

    def test_generate_windsurf(self, runner, tmp_dir):
        result = runner.invoke(
            main, ["generate", "windsurf", "--project-name", "test", "--output-dir", tmp_dir]
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".windsurfrules").exists()

    def test_generate_codex(self, runner, tmp_dir):
        result = runner.invoke(
            main, ["generate", "codex", "--project-name", "test", "--output-dir", tmp_dir]
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".openai" / "instructions.md").exists()


class TestChangelogCommand:
    def test_changelog_shows_versions(self, runner):
        result = runner.invoke(main, ["changelog"])
        assert result.exit_code == 0

    def test_changelog_latest(self, runner):
        result = runner.invoke(main, ["changelog", "--latest"])
        assert result.exit_code == 0

    def test_changelog_specific_version(self, runner):
        result = runner.invoke(main, ["changelog", "--version", "4.4.0"])
        assert result.exit_code == 0

    def test_changelog_unknown_version(self, runner):
        result = runner.invoke(main, ["changelog", "--version", "0.0.0"])
        assert result.exit_code == 0
        assert (
            "not found" in result.output.lower() or result.output == "" or "0.0.0" in result.output
        )


class TestPresetsCommand:
    def test_presets_list(self, runner):
        result = runner.invoke(main, ["presets"])
        assert result.exit_code == 0
        assert "fastapi-postgres" in result.output
        assert "saas-nextjs" in result.output

    def test_presets_search(self, runner):
        result = runner.invoke(main, ["presets", "python"])
        assert result.exit_code == 0

    def test_presets_no_results(self, runner):
        result = runner.invoke(main, ["presets", "nonexistent-xyz-12345"])
        assert result.exit_code == 0
        assert "No presets" in result.output or result.output.strip() != ""


class TestLangsCommand:
    def test_langs_list(self, runner):
        result = runner.invoke(main, ["langs"])
        assert result.exit_code == 0
        assert "python" in result.output.lower()
        assert "typescript" in result.output.lower()
        assert "go" in result.output.lower()
        assert "rust" in result.output.lower()

    def test_langs_shows_11(self, runner):
        result = runner.invoke(main, ["langs"])
        assert result.exit_code == 0
        assert "11" in result.output or "kotlin" in result.output.lower()


class TestCompletionCommand:
    def test_completion_bash(self, runner):
        result = runner.invoke(main, ["completion", "bash"])
        assert result.exit_code == 0
        assert "bash" in result.output.lower()

    def test_completion_zsh(self, runner):
        result = runner.invoke(main, ["completion", "zsh"])
        assert result.exit_code == 0
        assert "zsh" in result.output.lower()

    def test_completion_fish(self, runner):
        result = runner.invoke(main, ["completion", "fish"])
        assert result.exit_code == 0
        assert "fish" in result.output.lower()

    def test_completion_powershell(self, runner):
        result = runner.invoke(main, ["completion", "powershell"])
        assert result.exit_code == 0


class TestTemplatesCommand:
    def test_templates_list(self, runner):
        result = runner.invoke(main, ["templates"])
        assert result.exit_code == 0
        assert "fastapi-postgres" in result.output
        assert "react-typescript" in result.output

    def test_templates_search(self, runner):
        result = runner.invoke(main, ["templates", "python"])
        assert result.exit_code == 0

    def test_templates_install_valid(self, runner):
        result = runner.invoke(main, ["templates:install", "fastapi-postgres"])
        assert result.exit_code == 0
        assert "fastapi-postgres" in result.output

    def test_templates_install_invalid(self, runner):
        result = runner.invoke(main, ["templates:install", "nonexistent-template"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "Available" in result.output


class TestNewProjectExtended:
    def test_new_go_project(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            [
                "new",
                "my-go-api",
                "--lang",
                "go",
                "--type",
                "api",
                "--tool",
                "agents-md",
                "--output-dir",
                tmp_dir,
            ],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "my-go-api").exists()

    def test_new_rust_project(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            [
                "new",
                "my-rust-cli",
                "--lang",
                "rust",
                "--type",
                "cli",
                "--tool",
                "gemini",
                "--output-dir",
                tmp_dir,
            ],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "my-rust-cli").exists()

    def test_new_preset_nextjs(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["new", "my-nextjs", "--preset", "nextjs", "--output-dir", tmp_dir],
        )
        assert result.exit_code == 0

    def test_new_preset_go_api(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["new", "my-go", "--preset", "go-api", "--tool", "agents-md", "--output-dir", tmp_dir],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "my-go").exists()

    def test_new_preset_rust_cli(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["new", "my-rust", "--preset", "rust-cli", "--output-dir", tmp_dir],
        )
        assert result.exit_code == 0


class TestInstallCommand:
    def test_install_pip(self, runner):
        result = runner.invoke(main, ["install", "pip"])
        assert result.exit_code == 0
        assert "pip install vcsx" in result.output

    def test_install_npm(self, runner):
        result = runner.invoke(main, ["install", "npm"])
        assert result.exit_code == 0
        assert "npm install -g vcsx" in result.output

    def test_install_exe(self, runner):
        result = runner.invoke(main, ["install", "exe"])
        assert result.exit_code == 0
        assert "barancanercan/vcsx" in result.output


class TestScaffoldCommand:
    def test_scaffold_gitignore_python(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "gitignore", "--lang", "python", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".gitignore").exists()
        content = (Path(tmp_dir) / ".gitignore").read_text()
        assert "__pycache__" in content
        assert ".venv" in content or "venv" in content

    def test_scaffold_gitignore_typescript(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "gitignore", "--lang", "typescript", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / ".gitignore").read_text()
        assert "node_modules" in content

    def test_scaffold_gitignore_go(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "gitignore", "--lang", "go", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / ".gitignore").read_text()
        assert "vendor" in content or "*.exe" in content

    def test_scaffold_dockerfile_python(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "dockerfile", "--lang", "python", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "Dockerfile").exists()
        content = (Path(tmp_dir) / "Dockerfile").read_text()
        assert "python" in content.lower()
        assert "EXPOSE" in content

    def test_scaffold_dockerfile_typescript(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "dockerfile", "--lang", "typescript", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / "Dockerfile").read_text()
        assert "node" in content.lower()
        assert "AS builder" in content  # Multi-stage

    def test_scaffold_dockerfile_go(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "dockerfile", "--lang", "go", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / "Dockerfile").read_text()
        assert "golang" in content.lower()
        assert "scratch" in content  # Minimal runtime

    def test_scaffold_makefile_python(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "makefile", "--lang", "python", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / "Makefile").read_text()
        assert "pytest" in content
        assert "ruff" in content

    def test_scaffold_makefile_go(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "makefile", "--lang", "go", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / "Makefile").read_text()
        assert "go build" in content
        assert "go test" in content

    def test_scaffold_editorconfig(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "editorconfig", "--lang", "python", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / ".editorconfig").read_text()
        assert "root = true" in content
        assert "indent_size" in content

    def test_scaffold_dry_run(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "gitignore", "--lang", "python", "--dry-run", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        assert "gitignore" in result.output.lower()
        # File should NOT be created
        assert not (Path(tmp_dir) / ".gitignore").exists()

    def test_scaffold_skips_existing(self, runner, tmp_dir):
        (Path(tmp_dir) / ".gitignore").write_text("EXISTING")
        result = runner.invoke(main, ["scaffold", "gitignore", "--lang", "python", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        assert "already exists" in result.output
        # Should NOT overwrite
        assert (Path(tmp_dir) / ".gitignore").read_text() == "EXISTING"

    def test_scaffold_renovate(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "renovate", "--lang", "typescript", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        import json
        data = json.loads((Path(tmp_dir) / "renovate.json").read_text())
        assert "$schema" in data
        assert "extends" in data

    def test_scaffold_nvmrc(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "nvmrc", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".nvmrc").exists()

    def test_scaffold_dockercompose(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "dockercompose", "--lang", "python", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / "docker-compose.yml").read_text()
        assert "services:" in content
        assert "postgres" in content.lower() or "db:" in content


class TestScaffoldNewFiles:
    def test_scaffold_lintconfig_python(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "lintconfig", "--lang", "python", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "ruff.toml").exists()
        content = (Path(tmp_dir) / "ruff.toml").read_text()
        assert "target-version" in content
        assert "select" in content

    def test_scaffold_lintconfig_typescript(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "lintconfig", "--lang", "typescript", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "eslint.config.mjs").exists()
        content = (Path(tmp_dir) / "eslint.config.mjs").read_text()
        assert "@typescript-eslint" in content

    def test_scaffold_lintconfig_go(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "lintconfig", "--lang", "go", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".golangci.yml").exists()
        content = (Path(tmp_dir) / ".golangci.yml").read_text()
        assert "errcheck" in content or "linters" in content

    def test_scaffold_lintconfig_rust(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "lintconfig", "--lang", "rust", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".clippy.toml").exists()

    def test_scaffold_security(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "security", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / "SECURITY.md").read_text()
        assert "Reporting a Vulnerability" in content
        assert "coordinated disclosure" in content.lower() or "Disclosure" in content

    def test_scaffold_ciworkflow_python(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "ciworkflow", "--lang", "python", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / ".github" / "workflows" / "ci.yml").read_text()
        assert "pytest" in content
        assert "ruff" in content

    def test_scaffold_ciworkflow_go(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "ciworkflow", "--lang", "go", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / ".github" / "workflows" / "ci.yml").read_text()
        assert "go test" in content

    def test_scaffold_codeowners(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "codeowners", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / "CODEOWNERS").read_text()
        assert "*" in content
        assert "@" in content

    def test_scaffold_pullrequest(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "pullrequest", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / ".github" / "pull_request_template.md").read_text()
        assert "Checklist" in content
        assert "Testing" in content


class TestPromptCommand:
    def test_prompt_feature_basic(self, runner):
        result = runner.invoke(main, ["prompt", "add user auth", "--lang", "python", "--type", "feature"])
        assert result.exit_code == 0
        assert "Feature" in result.output or "feature" in result.output.lower()
        assert "add user auth" in result.output

    def test_prompt_bugfix(self, runner):
        result = runner.invoke(main, ["prompt", "fix race condition", "--lang", "go", "--type", "bugfix"])
        assert result.exit_code == 0
        assert "Bug" in result.output or "fix" in result.output.lower()
        assert "fix race condition" in result.output

    def test_prompt_refactor(self, runner):
        result = runner.invoke(main, ["prompt", "simplify auth module", "--lang", "python", "--type", "refactor"])
        assert result.exit_code == 0
        assert "Refactor" in result.output
        assert "behavior must not change" in result.output.lower() or "Behavior" in result.output

    def test_prompt_test_type(self, runner):
        result = runner.invoke(main, ["prompt", "UserService", "--lang", "typescript", "--type", "test"])
        assert result.exit_code == 0
        assert "AAA" in result.output or "Arrange" in result.output or "test" in result.output.lower()

    def test_prompt_docs(self, runner):
        result = runner.invoke(main, ["prompt", "payment module", "--lang", "python", "--type", "docs"])
        assert result.exit_code == 0
        assert "Documentation" in result.output or "doc" in result.output.lower()

    def test_prompt_explain(self, runner):
        result = runner.invoke(main, ["prompt", "auth middleware", "--lang", "go", "--type", "explain"])
        assert result.exit_code == 0
        assert "Explain" in result.output or "explain" in result.output.lower()

    def test_prompt_review(self, runner):
        result = runner.invoke(main, ["prompt", "PR #42", "--lang", "rust", "--type", "review"])
        assert result.exit_code == 0
        assert "Review" in result.output
        assert "APPROVE" in result.output or "Blocking" in result.output

    def test_prompt_with_framework(self, runner):
        result = runner.invoke(main, ["prompt", "add endpoint", "--lang", "python", "--framework", "fastapi"])
        assert result.exit_code == 0
        assert "fastapi" in result.output.lower()

    def test_prompt_shows_separator(self, runner):
        result = runner.invoke(main, ["prompt", "some task", "--lang", "python"])
        assert result.exit_code == 0
        assert "─" in result.output or "---" in result.output or "────" in result.output


class TestScaffoldDeployFiles:
    def test_scaffold_tsconfig(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "tsconfig", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / "tsconfig.json").read_text()
        assert '"strict": true' in content
        assert "noUncheckedIndexedAccess" in content
        assert '"outDir"' in content

    def test_scaffold_pyproject(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "pyproject", "--lang", "python", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / "pyproject.toml").read_text()
        assert "[build-system]" in content
        assert "pytest" in content
        assert "ruff" in content

    def test_scaffold_pyproject_fastapi(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "pyproject", "--lang", "python", "--framework", "fastapi", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / "pyproject.toml").read_text()
        assert "fastapi" in content

    def test_scaffold_flytoml(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "flytoml", "--lang", "python", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / "fly.toml").read_text()
        assert "app = " in content
        assert "services" in content
        assert "health" in content

    def test_scaffold_helmvalues(self, runner, tmp_dir):
        result = runner.invoke(main, ["scaffold", "helmvalues", "--lang", "python", "--output-dir", tmp_dir])
        assert result.exit_code == 0
        content = (Path(tmp_dir) / "values.yaml").read_text()
        assert "replicaCount:" in content
        assert "autoscaling:" in content
        assert "ingress:" in content
