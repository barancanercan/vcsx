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
