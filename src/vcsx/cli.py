"""CLI entry point for vcsx."""

import click
from rich.console import Console
from rich.panel import Panel

from vcsx import __version__
from vcsx.discovery import run_discovery
from vcsx.generators.registry import ALL_TOOLS, get_generator
from vcsx.implementation import run_implementation
from vcsx.planner import confirm_plan, generate_plan

console = Console()

BANNER = """
  ╔══════════════════╗
  ║       ⚙️         ║
  ║      vcsx        ║
  ║     v{version:<6} ║
  ╚══════════════════╝
"""


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version=__version__, prog_name="vcsx")
def main(ctx):
    """Vibe Coding Setup Expert — Automates AI coding environment setup.

    Run without commands to start the interactive setup wizard.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(init)


@main.command()
@click.option(
    "--cli",
    "-c",
    multiple=True,
    default=["claude-code"],
    type=click.Choice(ALL_TOOLS),
    help="CLI tools to generate setup for",
)
@click.option(
    "--lang",
    "-l",
    type=click.Choice(["tr", "en"]),
    default="tr",
    help="Language for prompts",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=".",
    help="Target directory for setup",
)
def init(cli, lang, output_dir):
    """Start interactive setup wizard."""
    tools = list(cli) if cli else ["claude-code"]

    console.print(f"[bold cyan]{BANNER.format(version=__version__)}[/bold cyan]")
    console.print(
        Panel.fit(
            "[bold]Vibe Coding Setup Expert[/bold]",
            subtitle=f"CLI tools: {', '.join(tools)}",
        )
    )

    # Phase 1: Discovery
    console.print("\n[bold yellow]🔍 PHASE 1: DISCOVERY[/bold yellow]")
    context = run_discovery(console, lang=lang)

    # Phase 2: Plan
    console.print("\n[bold yellow]📋 PHASE 2: PLAN[/bold yellow]")
    generate_plan(context, console, tools)
    if not confirm_plan(console):
        console.print("[red]Setup cancelled. Run 'vcsx init' to try again.[/red]")
        return

    # Phase 3: Implementation
    console.print("\n[bold yellow]🛠️ PHASE 3: IMPLEMENTATION[/bold yellow]")
    generators = [get_generator(t) for t in tools]
    run_implementation(context, output_dir, generators, console)

    console.print("\n[bold green]✅ Setup complete![/bold green]")
    console.print(f"Files generated in: [cyan]{output_dir}[/cyan]")


@main.command("list")
def list_tools():
    """List available CLI tools."""
    console.print("[bold]Available CLI tools:[/bold]")
    for tool in ALL_TOOLS:
        console.print(f"  • {tool}")


if __name__ == "__main__":
    main()
