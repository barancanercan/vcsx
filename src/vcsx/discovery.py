"""Discovery phase — Interactive questionnaire engine with smart parsing."""

from rich.console import Console
from rich.prompt import Confirm, Prompt

from vcsx.core.context import ProjectContext
from vcsx.core.inference import (
    infer_formatter,
    infer_framework,
    infer_language,
    infer_linter,
    infer_test_framework,
)
from vcsx.utils.prompts import get_prompts


def run_discovery(console: Console, lang: str = "tr") -> ProjectContext:
    """Run the discovery questionnaire."""
    prompts = get_prompts(lang)
    ctx = ProjectContext(lang=lang)

    console.print(prompts["welcome"])

    # Round 1: Project basics
    console.print("\n[bold cyan]━━━ Round 1/3: Project Basics ━━━[/bold cyan]")
    ctx.project_name = Prompt.ask(prompts["project_name"], default="my-project")
    ctx.description = Prompt.ask(prompts["description"], default="")
    ctx.project_type = Prompt.ask(
        prompts["project_type"],
        choices=["web", "api", "cli", "mobile", "desktop", "library", "other"],
        default="web",
    )
    ctx.tech_stack = Prompt.ask(prompts["tech_stack"], default="")
    ctx.language = infer_language(ctx.tech_stack)
    ctx.framework = infer_framework(ctx.tech_stack)
    ctx.mvp_features = Prompt.ask(prompts["mvp_features"], default="")
    ctx.target_users = Prompt.ask(prompts["target_users"], default="")

    # Round 2: Technical preferences
    console.print("\n[bold cyan]━━━ Round 2/3: Technical Preferences ━━━[/bold cyan]")
    ctx.hosting = Prompt.ask(prompts["hosting"], default="")
    ctx.auth_needed = Confirm.ask(prompts["auth_needed"], default=False)
    if ctx.auth_needed:
        ctx.auth_method = Prompt.ask(prompts["auth_method"], default="")
    ctx.external_services = Prompt.ask(prompts["external_services"], default="")
    ctx.monorepo = Confirm.ask(prompts["monorepo"], default=False)

    # Round 3: Development standards
    console.print("\n[bold cyan]━━━ Round 3/3: Development Standards ━━━[/bold cyan]")
    ctx.test_level = Prompt.ask(
        prompts["test_level"],
        choices=["none", "unit", "integration", "full"],
        default="unit",
    )
    if ctx.test_level != "none":
        ctx.test_framework = Prompt.ask(
            prompts["test_framework"],
            default=infer_test_framework(ctx.language),
        )
    ctx.ci_cd = Confirm.ask(prompts["ci_cd"], default=False)
    ctx.code_style = Prompt.ask(prompts["code_style"], default="")
    ctx.formatter = Prompt.ask(prompts["formatter"], default=infer_formatter(ctx.language))
    ctx.linter = Prompt.ask(prompts["linter"], default=infer_linter(ctx.language))

    # Claude Code preferences
    console.print("\n[bold cyan]━━━ Claude Code Preferences ━━━[/bold cyan]")
    ctx.recurring_tasks = Prompt.ask(prompts["recurring_tasks"], default="")
    ctx.forbidden_actions = Prompt.ask(
        prompts["forbidden_actions"],
        default="rm -rf, git push --force, dropping tables, deleting production data",
    )
    ctx.automations = Prompt.ask(
        prompts["automations"],
        default="auto-format on save, run tests before commit",
    )

    console.print(f"\n[bold green]✅ Discovery complete! Project: {ctx.project_name}[/bold green]")
    return ctx
