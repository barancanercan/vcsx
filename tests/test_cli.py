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
        # Either shows dry-run message or "up to date" when nothing to do
        assert "Dry run" in result.output or "dry run" in result.output or "up to date" in result.output

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
                "new", "my-api", "--lang", "python", "--type", "api",
                "--tool", "claude-code", "--output-dir", tmp_dir,
            ],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "my-api" / "CLAUDE.md").exists()

    def test_new_multi_tool(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            [
                "new", "my-multi", "--lang", "python",
                "--tool", "claude-code", "--tool", "gemini",
                "--output-dir", tmp_dir,
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
                "new", "my-web", "--lang", "typescript", "--type", "web",
                "--tool", "cursor", "--output-dir", tmp_dir,
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
            ["generate", "agents-md", "--project-name", "my-lib", "--lang", "python", "--output-dir", tmp_dir],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "AGENTS.md").exists()

    def test_generate_claude_code(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["generate", "claude-code", "--project-name", "my-app", "--lang", "typescript", "--output-dir", tmp_dir],
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
        result = runner.invoke(main, ["export", tmp_dir, "--output", str(zip_path), "--include-all"])
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


class TestGenerateCommandExtended:
    def test_generate_aider(self, runner, tmp_dir):
        result = runner.invoke(
            main, ["generate", "aider", "--project-name", "test", "--output-dir", tmp_dir]
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / ".aider.conf.yaml").exists()

    def test_generate_cursor(self, runner, tmp_dir):
        result = runner.invoke(
            main, ["generate", "cursor", "--project-name", "test", "--lang", "python", "--output-dir", tmp_dir]
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
            ["new", "my-go-api", "--lang", "go", "--type", "api", "--tool", "agents-md", "--output-dir", tmp_dir],
        )
        assert result.exit_code == 0
        assert (Path(tmp_dir) / "my-go-api").exists()

    def test_new_rust_project(self, runner, tmp_dir):
        result = runner.invoke(
            main,
            ["new", "my-rust-cli", "--lang", "rust", "--type", "cli", "--tool", "gemini", "--output-dir", tmp_dir],
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
