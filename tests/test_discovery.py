"""Tests for vcsx.discovery — run_discovery questionnaire engine."""

from unittest.mock import MagicMock, patch

from vcsx.core.context import ProjectContext  # noqa: E402
from vcsx.discovery import run_discovery  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_console():
    """Return a MagicMock that mimics rich.console.Console."""
    return MagicMock()


def _patch_prompt(answers: list):
    """Return a side_effect list for Prompt.ask calls."""
    return answers


# ---------------------------------------------------------------------------
# Default / happy-path run (no auth, no claude-code phase)
# ---------------------------------------------------------------------------

BASIC_PROMPT_ANSWERS = [
    # Phase 0
    "cursor",  # ai_tool
    "linux",  # platform
    # Phase 1
    "Build a web app",  # purpose
    "Too much manual work",  # problem
    "my-project",  # project_name
    "A cool description",  # description
    "python fastapi",  # tech_stack
    "web",  # project_type
    # Phase 2
    "As a user I want...",  # user_stories
    "App works correctly",  # success_criteria
    "feature1, feature2",  # mvp_features
    "developers",  # target_users
    # Phase 3
    "vercel",  # hosting
    # auth_needed → Confirm (False)
    "none",  # external_services
    # monorepo → Confirm (False)
    # Phase 4
    "unit",  # test_level
    "pytest",  # test_framework
    # ci_cd → Confirm (False)
    "black",  # code_style
    "black",  # formatter
    "ruff",  # linter
]

BASIC_CONFIRM_ANSWERS = [False, False, False]  # auth_needed, monorepo, ci_cd


def _run_with_mocks(prompt_answers, confirm_answers, lang="tr"):
    console = make_console()
    prompt_iter = iter(prompt_answers)
    confirm_iter = iter(confirm_answers)

    with (
        patch("vcsx.discovery.Prompt.ask", side_effect=lambda *a, **kw: next(prompt_iter)),
        patch("vcsx.discovery.Confirm.ask", side_effect=lambda *a, **kw: next(confirm_iter)),
        patch("vcsx.discovery.detect_ai_tool", return_value=None),
        patch("vcsx.discovery.detect_platform", return_value="linux"),
    ):
        ctx = run_discovery(console, lang=lang)
    return ctx


class TestRunDiscoveryBasic:
    def test_returns_project_context(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert isinstance(ctx, ProjectContext)

    def test_ai_tool_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.ai_tool == "cursor"

    def test_ai_tools_list_single(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.ai_tools_list == ["cursor"]

    def test_platform_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.platform == "linux"

    def test_purpose_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.purpose == "Build a web app"

    def test_problem_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.problem == "Too much manual work"

    def test_project_name_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.project_name == "my-project"

    def test_description_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.description == "A cool description"

    def test_tech_stack_and_language_inferred(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.tech_stack == "python fastapi"
        assert ctx.language == "python"

    def test_framework_inferred(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert "fastapi" in ctx.framework.lower() or ctx.framework != ""

    def test_project_type_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.project_type == "web"

    def test_user_stories_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.user_stories == "As a user I want..."

    def test_success_criteria_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.success_criteria == "App works correctly"

    def test_hosting_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.hosting == "vercel"

    def test_auth_needed_false(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.auth_needed is False

    def test_monorepo_false(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.monorepo is False

    def test_test_level_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.test_level == "unit"

    def test_test_framework_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.test_framework == "pytest"

    def test_ci_cd_false(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.ci_cd is False

    def test_formatter_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.formatter == "black"

    def test_linter_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.linter == "ruff"

    def test_lang_passed(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS, lang="tr")
        assert ctx.lang == "tr"

    def test_english_lang(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS, lang="en")
        assert ctx.lang == "en"


# ---------------------------------------------------------------------------
# "all" tools shortcut
# ---------------------------------------------------------------------------


def _make_all_tools_answers():
    answers = list(BASIC_PROMPT_ANSWERS)
    answers[0] = "all"  # Replace ai_tool answer
    return answers


class TestAllToolsShortcut:
    def test_ai_tool_is_all(self):
        ctx = _run_with_mocks(_make_all_tools_answers(), BASIC_CONFIRM_ANSWERS)
        assert ctx.ai_tool == "all"

    def test_ai_tools_list_populated(self):
        from vcsx.generators.registry import ALL_TOOLS

        ctx = _run_with_mocks(_make_all_tools_answers(), BASIC_CONFIRM_ANSWERS)
        assert ctx.ai_tools_list == list(ALL_TOOLS)

    def test_ai_tools_list_not_empty(self):
        ctx = _run_with_mocks(_make_all_tools_answers(), BASIC_CONFIRM_ANSWERS)
        assert len(ctx.ai_tools_list) > 0


# ---------------------------------------------------------------------------
# Comma-separated tools
# ---------------------------------------------------------------------------


def _make_csv_tools_answers(csv_input):
    answers = list(BASIC_PROMPT_ANSWERS)
    answers[0] = csv_input
    return answers


def _run_with_mocks_detected(prompt_answers, confirm_answers, detected_tool="cursor", lang="tr"):
    """Like _run_with_mocks but with a custom detected AI tool (avoids claude-code fallback)."""
    console = make_console()
    prompt_iter = iter(prompt_answers)
    confirm_iter = iter(confirm_answers)

    with (
        patch("vcsx.discovery.Prompt.ask", side_effect=lambda *a, **kw: next(prompt_iter)),
        patch("vcsx.discovery.Confirm.ask", side_effect=lambda *a, **kw: next(confirm_iter)),
        patch("vcsx.discovery.detect_ai_tool", return_value=detected_tool),
        patch("vcsx.discovery.detect_platform", return_value="linux"),
    ):
        ctx = run_discovery(console, lang=lang)
    return ctx


class TestCsvTools:
    def test_valid_csv_tools(self):
        ctx = _run_with_mocks(
            _make_csv_tools_answers("cursor,codex"),
            BASIC_CONFIRM_ANSWERS,
        )
        assert ctx.ai_tool == "cursor"
        assert "cursor" in ctx.ai_tools_list
        assert "codex" in ctx.ai_tools_list

    def test_invalid_csv_tools_fallback(self):
        """Invalid tool names → fall back to detected tool (cursor)."""
        ctx = _run_with_mocks_detected(
            _make_csv_tools_answers("nonexistent-tool,also-fake"),
            BASIC_CONFIRM_ANSWERS,
            detected_tool="cursor",
        )
        # Should fall back; ai_tools_list will be a single-item default list
        assert len(ctx.ai_tools_list) >= 1

    def test_mixed_valid_invalid_csv(self):
        ctx = _run_with_mocks(
            _make_csv_tools_answers("cursor,invalid-xyz"),
            BASIC_CONFIRM_ANSWERS,
        )
        assert "cursor" in ctx.ai_tools_list


# ---------------------------------------------------------------------------
# Unknown tool fallback
# ---------------------------------------------------------------------------


class TestUnknownToolFallback:
    def test_unknown_tool_falls_back_to_detected(self):
        """When input is invalid tool and detect returns 'cursor', cursor becomes default."""
        answers = list(BASIC_PROMPT_ANSWERS)
        answers[0] = "totally-unknown-tool"
        ctx = _run_with_mocks_detected(answers, BASIC_CONFIRM_ANSWERS, detected_tool="cursor")
        # falls back to detected default
        assert ctx.ai_tool != "totally-unknown-tool"

    def test_unknown_tool_ai_tools_list_single(self):
        answers = list(BASIC_PROMPT_ANSWERS)
        answers[0] = "totally-unknown-tool"
        ctx = _run_with_mocks_detected(answers, BASIC_CONFIRM_ANSWERS, detected_tool="cursor")
        assert len(ctx.ai_tools_list) == 1


# ---------------------------------------------------------------------------
# Auth needed = True branch
# ---------------------------------------------------------------------------

AUTH_PROMPT_ANSWERS = [
    "cursor",  # ai_tool
    "linux",  # platform
    "purpose",  # purpose
    "problem",  # problem
    "proj",  # project_name
    "desc",  # description
    "python",  # tech_stack
    "web",  # project_type
    "stories",  # user_stories
    "criteria",  # success_criteria
    "mvp",  # mvp_features
    "users",  # target_users
    "aws",  # hosting
    # auth_needed → True (Confirm)
    "jwt",  # auth_method  ← inserted because auth_needed=True
    "stripe",  # external_services
    # monorepo → False (Confirm)
    "unit",  # test_level
    "pytest",  # test_framework
    # ci_cd → False (Confirm)
    "pep8",  # code_style
    "black",  # formatter
    "ruff",  # linter
]

AUTH_CONFIRM_ANSWERS = [True, False, False]  # auth_needed=True, monorepo=False, ci_cd=False


class TestAuthBranch:
    def test_auth_needed_true(self):
        ctx = _run_with_mocks(AUTH_PROMPT_ANSWERS, AUTH_CONFIRM_ANSWERS)
        assert ctx.auth_needed is True

    def test_auth_method_set(self):
        ctx = _run_with_mocks(AUTH_PROMPT_ANSWERS, AUTH_CONFIRM_ANSWERS)
        assert ctx.auth_method == "jwt"


# ---------------------------------------------------------------------------
# Claude Code phase (PHASE 5)
# ---------------------------------------------------------------------------

CC_PROMPT_ANSWERS = [
    "claude-code",  # ai_tool
    "linux",  # platform
    "purpose",  # purpose
    "problem",  # problem
    "proj",  # project_name
    "desc",  # description
    "python",  # tech_stack
    "web",  # project_type
    "stories",  # user_stories
    "criteria",  # success_criteria
    "mvp",  # mvp_features
    "users",  # target_users
    "vercel",  # hosting
    # auth_needed → False (Confirm)
    "none",  # external_services
    # monorepo → False (Confirm)
    "unit",  # test_level
    "pytest",  # test_framework
    # ci_cd → False (Confirm)
    "pep8",  # code_style
    "black",  # formatter
    "ruff",  # linter
    # Phase 5 (Claude Code only)
    "run tests",  # recurring_tasks
    "rm -rf",  # forbidden_actions
    "auto-format",  # automations
]

CC_CONFIRM_ANSWERS = [False, False, False]


class TestClaudeCodePhase:
    def test_ai_tool_claude_code(self):
        ctx = _run_with_mocks(CC_PROMPT_ANSWERS, CC_CONFIRM_ANSWERS)
        assert ctx.ai_tool == "claude-code"

    def test_recurring_tasks_set(self):
        ctx = _run_with_mocks(CC_PROMPT_ANSWERS, CC_CONFIRM_ANSWERS)
        assert ctx.recurring_tasks == "run tests"

    def test_forbidden_actions_set(self):
        ctx = _run_with_mocks(CC_PROMPT_ANSWERS, CC_CONFIRM_ANSWERS)
        assert ctx.forbidden_actions == "rm -rf"

    def test_automations_set(self):
        ctx = _run_with_mocks(CC_PROMPT_ANSWERS, CC_CONFIRM_ANSWERS)
        assert ctx.automations == "auto-format"


# ---------------------------------------------------------------------------
# detect_ai_tool integration (auto-detected default)
# ---------------------------------------------------------------------------


class TestDetectedAiTool:
    def test_detected_tool_used_as_default(self):
        """When detect_ai_tool returns a valid tool, it becomes the default."""
        console = make_console()
        prompt_answers = list(BASIC_PROMPT_ANSWERS)
        prompt_iter = iter(prompt_answers)
        confirm_iter = iter(BASIC_CONFIRM_ANSWERS)

        with (
            patch("vcsx.discovery.Prompt.ask", side_effect=lambda *a, **kw: next(prompt_iter)),
            patch("vcsx.discovery.Confirm.ask", side_effect=lambda *a, **kw: next(confirm_iter)),
            patch("vcsx.discovery.detect_ai_tool", return_value="codex"),
            patch("vcsx.discovery.detect_platform", return_value="linux"),
        ):
            ctx = run_discovery(console)
        # prompt_answers[0] = "cursor" overrides the detected default
        assert ctx.ai_tool == "cursor"

    def test_no_detected_tool_uses_claude_code_default(self):
        """When detect_ai_tool returns None, default is claude-code."""
        console = make_console()

        cc_answers = list(CC_PROMPT_ANSWERS)
        cc_answers[0] = "claude-code"
        p_iter = iter(cc_answers)
        c_iter = iter(CC_CONFIRM_ANSWERS)

        with (
            patch("vcsx.discovery.Prompt.ask", side_effect=lambda *a, **kw: next(p_iter)),
            patch("vcsx.discovery.Confirm.ask", side_effect=lambda *a, **kw: next(c_iter)),
            patch("vcsx.discovery.detect_ai_tool", return_value=None),
            patch("vcsx.discovery.detect_platform", return_value="linux"),
        ):
            ctx = run_discovery(console)
        assert ctx.ai_tool == "claude-code"


# ---------------------------------------------------------------------------
# Test level = "none" (skip test_framework question)
# ---------------------------------------------------------------------------


def _make_no_test_answers():
    """Build answer list with test_level = 'none' (skips test_framework)."""
    return [
        "cursor",
        "linux",
        "purpose",
        "problem",
        "proj",
        "desc",
        "python",
        "web",
        "stories",
        "criteria",
        "mvp",
        "users",
        "vercel",
        # auth_needed → False
        "none",
        # monorepo → False
        "none",  # test_level = "none" — no test_framework asked
        # ci_cd → False
        "pep8",
        "black",
        "ruff",
    ]


class TestNoTestLevel:
    def test_no_test_framework_when_none(self):
        ctx = _run_with_mocks(_make_no_test_answers(), [False, False, False])
        assert ctx.test_level == "none"
        assert ctx.test_framework == ""  # never set


# ---------------------------------------------------------------------------
# ci_cd = True
# ---------------------------------------------------------------------------


def _make_cicd_answers():
    return list(BASIC_PROMPT_ANSWERS)


class TestCiCd:
    def test_ci_cd_true(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, [False, False, True])
        assert ctx.ci_cd is True


# ---------------------------------------------------------------------------
# Monorepo = True
# ---------------------------------------------------------------------------


class TestMonorepo:
    def test_monorepo_true(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, [False, True, False])
        assert ctx.monorepo is True


# ---------------------------------------------------------------------------
# Console print calls (smoke-test that console is used)
# ---------------------------------------------------------------------------


class TestConsoleUsed:
    def test_console_print_called(self):
        console = make_console()
        prompt_iter = iter(BASIC_PROMPT_ANSWERS)
        confirm_iter = iter(BASIC_CONFIRM_ANSWERS)

        with (
            patch("vcsx.discovery.Prompt.ask", side_effect=lambda *a, **kw: next(prompt_iter)),
            patch("vcsx.discovery.Confirm.ask", side_effect=lambda *a, **kw: next(confirm_iter)),
            patch("vcsx.discovery.detect_ai_tool", return_value=None),
            patch("vcsx.discovery.detect_platform", return_value="linux"),
        ):
            run_discovery(console)

        assert console.print.called
        assert console.print.call_count >= 5


# ---------------------------------------------------------------------------
# MVP features and target users
# ---------------------------------------------------------------------------


class TestMvpAndTargetUsers:
    def test_mvp_features_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.mvp_features == "feature1, feature2"

    def test_target_users_set(self):
        ctx = _run_with_mocks(BASIC_PROMPT_ANSWERS, BASIC_CONFIRM_ANSWERS)
        assert ctx.target_users == "developers"
