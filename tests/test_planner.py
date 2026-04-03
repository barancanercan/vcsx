"""Tests for planner.py — generate_plan, confirm_plan, _generate_tree, _determine_skills."""

from unittest import mock
from io import StringIO

import pytest
from rich.console import Console

from vcsx.core.context import ProjectContext
from vcsx.planner import generate_plan, confirm_plan, _generate_tree, _determine_skills


def make_ctx(**kwargs) -> ProjectContext:
    """Create a minimal ProjectContext for testing."""
    defaults = {
        "project_name": "test-app",
        "purpose": "Test purpose",
        "problem": "Test problem",
        "project_type": "cli",
        "tech_stack": "Python",
        "language": "python",
        "framework": "click",
        "hosting": "vercel",
        "auth_needed": False,
        "auth_method": "",
        "test_level": "unit",
        "test_framework": "pytest",
        "ci_cd": True,
        "formatter": "black",
        "linter": "ruff",
        "mvp_features": "feature1, feature2, feature3",
        "target_users": "developers",
        "user_stories": "As a user, I can do X\nAs a user, I can do Y",
        "success_criteria": "100 users\n200ms response",
    }
    defaults.update(kwargs)
    return ProjectContext(**defaults)


def make_console() -> Console:
    """Create a Rich console writing to a string buffer."""
    return Console(file=StringIO(), width=120)


class TestGeneratePlan:
    def test_returns_string(self):
        ctx = make_ctx()
        console = make_console()
        result = generate_plan(ctx, console, ["claude-code"])
        assert isinstance(result, str)

    def test_contains_project_name(self):
        ctx = make_ctx(project_name="my-awesome-app")
        console = make_console()
        result = generate_plan(ctx, console, ["claude-code"])
        assert "my-awesome-app" in result

    def test_contains_purpose(self):
        ctx = make_ctx(purpose="Build a great tool")
        console = make_console()
        result = generate_plan(ctx, console, ["claude-code"])
        assert "Build a great tool" in result

    def test_claude_code_tool(self):
        ctx = make_ctx()
        console = make_console()
        result = generate_plan(ctx, console, ["claude-code"])
        assert "CLAUDE.md" in result or "Claude" in result

    def test_cursor_tool(self):
        ctx = make_ctx()
        console = make_console()
        result = generate_plan(ctx, console, ["cursor"])
        assert "cursorrules" in result.lower() or "Cursor" in result

    def test_windsurf_tool(self):
        ctx = make_ctx()
        console = make_console()
        result = generate_plan(ctx, console, ["windsurf"])
        assert "windsurf" in result.lower()

    def test_zed_tool(self):
        ctx = make_ctx()
        console = make_console()
        result = generate_plan(ctx, console, ["zed"])
        assert "zed" in result.lower()

    def test_aider_tool(self):
        ctx = make_ctx()
        console = make_console()
        result = generate_plan(ctx, console, ["aider"])
        assert "aider" in result.lower()

    def test_bolt_tool(self):
        ctx = make_ctx()
        console = make_console()
        result = generate_plan(ctx, console, ["bolt"])
        assert "bolt" in result.lower()

    def test_codex_tool(self):
        ctx = make_ctx()
        console = make_console()
        result = generate_plan(ctx, console, ["codex"])
        assert "Codex" in result or "codex" in result

    def test_copilot_tool(self):
        ctx = make_ctx()
        console = make_console()
        result = generate_plan(ctx, console, ["copilot"])
        assert "copilot" in result.lower() or "Copilot" in result

    def test_multiple_tools(self):
        ctx = make_ctx()
        console = make_console()
        result = generate_plan(ctx, console, ["claude-code", "cursor"])
        assert isinstance(result, str)
        assert len(result) > 100

    def test_no_mvp_features_fallback(self):
        ctx = make_ctx(mvp_features="")
        console = make_console()
        result = generate_plan(ctx, console, ["claude-code"])
        assert "Proje iskeleti" in result or "iskeleti" in result

    def test_auth_enabled(self):
        ctx = make_ctx(auth_needed=True, auth_method="JWT")
        console = make_console()
        result = generate_plan(ctx, console, ["claude-code"])
        assert "Evet" in result or "JWT" in result

    def test_auth_disabled(self):
        ctx = make_ctx(auth_needed=False)
        console = make_console()
        result = generate_plan(ctx, console, ["claude-code"])
        assert "Hayır" in result

    def test_with_user_stories(self):
        ctx = make_ctx(user_stories="As a user, I can login\nAs a user, I can logout")
        console = make_console()
        result = generate_plan(ctx, console, ["claude-code"])
        assert "login" in result or "User Stories" in result or "user" in result.lower()

    def test_with_success_criteria(self):
        ctx = make_ctx(success_criteria="100 users\n200ms response")
        console = make_console()
        result = generate_plan(ctx, console, [])
        assert "100 users" in result or "200ms" in result

    def test_empty_tools(self):
        ctx = make_ctx()
        console = make_console()
        result = generate_plan(ctx, console, [])
        assert isinstance(result, str)


class TestConfirmPlan:
    def test_returns_true_when_confirmed(self):
        console = make_console()
        with mock.patch("vcsx.planner.Confirm.ask", return_value=True):
            result = confirm_plan(console)
        assert result is True

    def test_returns_false_when_declined(self):
        console = make_console()
        with mock.patch("vcsx.planner.Confirm.ask", return_value=False):
            result = confirm_plan(console)
        assert result is False


class TestGenerateTree:
    def test_cli_type(self):
        ctx = make_ctx(project_type="cli")
        result = _generate_tree(ctx)
        assert "src/" in result
        assert "tests/" in result

    def test_api_type(self):
        ctx = make_ctx(project_type="api")
        result = _generate_tree(ctx)
        assert "src/" in result

    def test_web_type(self):
        ctx = make_ctx(project_type="web")
        result = _generate_tree(ctx)
        assert "src/" in result

    def test_library_type(self):
        ctx = make_ctx(project_type="library")
        result = _generate_tree(ctx)
        assert "docs/" in result

    def test_data_pipeline_type(self):
        ctx = make_ctx(project_type="data-pipeline")
        result = _generate_tree(ctx)
        assert "scrapers/" in result or "data/" in result

    def test_ml_model_type(self):
        ctx = make_ctx(project_type="ml-model")
        result = _generate_tree(ctx)
        assert "notebooks/" in result or "models/" in result

    def test_contains_gitignore(self):
        ctx = make_ctx()
        result = _generate_tree(ctx)
        assert ".gitignore" in result

    def test_contains_readme(self):
        ctx = make_ctx()
        result = _generate_tree(ctx)
        assert "README.md" in result

    def test_contains_project_name(self):
        ctx = make_ctx(project_name="cool-tool")
        result = _generate_tree(ctx)
        assert "cool-tool/" in result


class TestDetermineSkills:
    def test_returns_list(self):
        ctx = make_ctx()
        result = _determine_skills(ctx)
        assert isinstance(result, list)

    def test_base_skills_present(self):
        ctx = make_ctx()
        result = _determine_skills(ctx)
        names = [s["name"] for s in result]
        assert "commit-message" in names
        assert "pr-review" in names
        assert "deploy" in names

    def test_auth_skill_added_when_needed(self):
        ctx = make_ctx(auth_needed=True, auth_method="JWT")
        result = _determine_skills(ctx)
        names = [s["name"] for s in result]
        assert "auth-conventions" in names

    def test_no_auth_skill_when_not_needed(self):
        ctx = make_ctx(auth_needed=False)
        result = _determine_skills(ctx)
        names = [s["name"] for s in result]
        assert "auth-conventions" not in names

    def test_api_skill_for_api_type(self):
        ctx = make_ctx(project_type="api")
        result = _determine_skills(ctx)
        names = [s["name"] for s in result]
        assert "api-conventions" in names

    def test_test_skill_added_when_tests(self):
        ctx = make_ctx(test_level="unit")
        result = _determine_skills(ctx)
        names = [s["name"] for s in result]
        assert "test-patterns" in names

    def test_no_test_skill_when_no_tests(self):
        ctx = make_ctx(test_level="none")
        result = _determine_skills(ctx)
        names = [s["name"] for s in result]
        assert "test-patterns" not in names

    def test_each_skill_has_name_and_description(self):
        ctx = make_ctx()
        result = _determine_skills(ctx)
        for skill in result:
            assert "name" in skill
            assert "description" in skill
            assert len(skill["name"]) > 0
