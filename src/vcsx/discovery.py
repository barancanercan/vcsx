"""Discovery phase — Interactive questionnaire engine with smart defaults."""

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.text import Text

from vcsx.core.context import ProjectContext
from vcsx.core.inference import (
    infer_formatter,
    infer_framework,
    infer_language,
    infer_linter,
    infer_test_framework,
)
from vcsx.utils.prompts import (
    AI_TOOLS,
    get_prompts,
    detect_platform,
    detect_ai_tool,
    get_intelligent_defaults,
    get_prompt_question,
    get_prompt_hint,
    get_prompt_placeholder,
    get_prompt_value,
)
from vcsx.generators.registry import ALL_TOOLS


def run_discovery(console: Console, lang: str = "tr") -> ProjectContext:
    """Run the discovery questionnaire with rich metadata."""
    prompts = get_prompts(lang)
    ctx = ProjectContext(lang=lang)

    console.print(prompts["welcome"])

    # PHASE 0: AI Tool & Platform (Quick)
    console.print("\n" + "=" * 60)
    console.print("PHASE 0: AI Tool & Platform")
    console.print("=" * 60)

    detected_tool = detect_ai_tool()
    default_tool = detected_tool if detected_tool else "claude-code"

    console.print(f"\n[dim]Available tools:[/] {', '.join(ALL_TOOLS)}")
    console.print("[dim]Tip: Use 'all' to configure every tool at once[/]")

    ai_tool_input = Prompt.ask(
        get_prompt_question(prompts, "ai_tool"),
        default=default_tool,
    )

    # Support "all" shortcut or comma-separated list
    if ai_tool_input.strip().lower() == "all":
        ctx.ai_tool = "all"
        ctx.ai_tools_list = list(ALL_TOOLS)
        console.print(f"[green]All {len(ALL_TOOLS)} tools will be configured.[/]")
    elif "," in ai_tool_input:
        tools = [t.strip() for t in ai_tool_input.split(",") if t.strip() in ALL_TOOLS]
        if tools:
            ctx.ai_tool = tools[0]
            ctx.ai_tools_list = tools
            console.print(f"[green]Configuring: {', '.join(tools)}[/]")
        else:
            ctx.ai_tool = default_tool
            ctx.ai_tools_list = [ctx.ai_tool]
    elif ai_tool_input in ALL_TOOLS:
        ctx.ai_tool = ai_tool_input
        ctx.ai_tools_list = [ctx.ai_tool]
    else:
        ctx.ai_tool = default_tool
        ctx.ai_tools_list = [ctx.ai_tool]

    detected_platform = detect_platform()
    ctx.platform = Prompt.ask(
        get_prompt_question(prompts, "platform"),
        default=detected_platform,
        choices=["windows-powershell", "macos", "linux", "wsl"],
    )

    # PHASE 1: Project Foundation (EN ÖNEMLİ - DETAYLI)
    console.print("\n" + "=" * 60)
    console.print("PHASE 1: Project Foundation (En Önemli)")
    console.print("=" * 60)
    console.print(Text(prompts["purpose"]["description"], style="dim"))

    ctx.purpose = Prompt.ask(
        get_prompt_question(prompts, "purpose"),
        default="",
        default_string=get_prompt_placeholder(prompts, "purpose"),
    )

    console.print(Text(prompts["problem"]["description"], style="dim"))
    ctx.problem = Prompt.ask(
        get_prompt_question(prompts, "problem"),
        default="",
        default_string=get_prompt_placeholder(prompts, "problem"),
    )

    ctx.project_name = Prompt.ask(
        get_prompt_question(prompts, "project_name"),
        default="my-project",
        default_string=get_prompt_placeholder(prompts, "project_name"),
    )
    ctx.description = Prompt.ask(
        get_prompt_question(prompts, "description"),
        default="",
        default_string=get_prompt_placeholder(prompts, "description"),
    )

    ctx.tech_stack = Prompt.ask(
        get_prompt_question(prompts, "tech_stack"),
        default="",
        default_string=get_prompt_placeholder(prompts, "tech_stack"),
    )
    ctx.language = infer_language(ctx.tech_stack)
    ctx.framework = infer_framework(ctx.tech_stack)

    project_type_prompt = prompts.get("project_type", {})
    project_type_options = project_type_prompt.get("options", {})
    project_type_choices = list(project_type_options.keys())
    ctx.project_type = Prompt.ask(
        get_prompt_question(prompts, "project_type"),
        default="web",
        choices=project_type_choices,
    )

    # PHASE 2: User Stories (DETAYLI)
    console.print("\n" + "=" * 60)
    console.print("PHASE 2: User Stories & Success Criteria")
    console.print("=" * 60)
    console.print(Text(prompts["user_stories"]["description"], style="dim"))
    ctx.user_stories = Prompt.ask(
        get_prompt_question(prompts, "user_stories"),
        default="",
        default_string=get_prompt_placeholder(prompts, "user_stories"),
    )

    console.print(Text(prompts["success_criteria"]["description"], style="dim"))
    ctx.success_criteria = Prompt.ask(
        get_prompt_question(prompts, "success_criteria"),
        default="",
        default_string=get_prompt_placeholder(prompts, "success_criteria"),
    )

    ctx.mvp_features = Prompt.ask(
        get_prompt_question(prompts, "mvp_features"),
        default="",
        default_string=get_prompt_placeholder(prompts, "mvp_features"),
    )
    ctx.target_users = Prompt.ask(
        get_prompt_question(prompts, "target_users"),
        default="",
        default_string=get_prompt_placeholder(prompts, "target_users"),
    )

    # PHASE 3: Technical Details (Smart Branching)
    console.print("\n" + "=" * 60)
    console.print("PHASE 3: Technical Details")
    console.print("=" * 60)

    ctx.hosting = Prompt.ask(
        get_prompt_question(prompts, "hosting"),
        default="",
        default_string=get_prompt_placeholder(prompts, "hosting"),
    )

    auth_needed_prompt = prompts.get("auth_needed", {})
    ctx.auth_needed = Confirm.ask(
        get_prompt_question(prompts, "auth_needed"),
        default=False,
    )
    if ctx.auth_needed:
        ctx.auth_method = Prompt.ask(
            get_prompt_question(prompts, "auth_method"),
            default="",
            default_string=get_prompt_placeholder(prompts, "auth_method"),
        )

    ctx.external_services = Prompt.ask(
        get_prompt_question(prompts, "external_services"),
        default="",
        default_string=get_prompt_placeholder(prompts, "external_services"),
    )

    ctx.monorepo = Confirm.ask(
        get_prompt_question(prompts, "monorepo"),
        default=False,
    )

    # PHASE 4: Development Standards
    console.print("\n" + "=" * 60)
    console.print("PHASE 4: Development Standards")
    console.print("=" * 60)

    test_level_prompt = prompts.get("test_level", {})
    test_level_options = test_level_prompt.get("options", {})
    test_level_choices = list(test_level_options.keys())
    ctx.test_level = Prompt.ask(
        get_prompt_question(prompts, "test_level"),
        default="unit",
        choices=test_level_choices,
    )
    if ctx.test_level != "none":
        ctx.test_framework = Prompt.ask(
            get_prompt_question(prompts, "test_framework"),
            default=infer_test_framework(ctx.language),
        )

    ctx.ci_cd = Confirm.ask(
        get_prompt_question(prompts, "ci_cd"),
        default=False,
    )

    ctx.code_style = Prompt.ask(
        get_prompt_question(prompts, "code_style"),
        default="",
        default_string=get_prompt_placeholder(prompts, "code_style"),
    )
    ctx.formatter = Prompt.ask(
        get_prompt_question(prompts, "formatter"),
        default=infer_formatter(ctx.language),
    )
    ctx.linter = Prompt.ask(
        get_prompt_question(prompts, "linter"),
        default=infer_linter(ctx.language),
    )

    # PHASE 5: Claude Code Specific (if selected)
    if ctx.ai_tool == "claude-code":
        console.print("\n" + "=" * 60)
        console.print("PHASE 5: Claude Code Configuration")
        console.print("=" * 60)

        intelligent = get_intelligent_defaults(ctx.language, ctx.project_type)

        ctx.recurring_tasks = Prompt.ask(
            get_prompt_question(prompts, "recurring_tasks"),
            default="",
            default_string=intelligent.get(
                "recurring_tasks", get_prompt_placeholder(prompts, "recurring_tasks")
            ),
        )
        ctx.forbidden_actions = Prompt.ask(
            get_prompt_question(prompts, "forbidden_actions"),
            default="rm -rf, git push --force",
            default_string=intelligent.get(
                "forbidden_actions", get_prompt_placeholder(prompts, "forbidden_actions")
            ),
        )
        ctx.automations = Prompt.ask(
            get_prompt_question(prompts, "automations"),
            default="auto-format on save, run tests before commit",
            default_string=intelligent.get(
                "automations", get_prompt_placeholder(prompts, "automations")
            ),
        )

    console.print(f"\n✓ Discovery complete! Project: {ctx.project_name}")
    console.print(
        f"  Purpose: {ctx.purpose[:60]}..."
        if len(ctx.purpose) > 60
        else f"  Purpose: {ctx.purpose}"
    )
    return ctx
