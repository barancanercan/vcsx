"""Implementation phase — Orchestrates file generation across CLI tools."""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from vcsx.core.context import ProjectContext
from vcsx.generators.base import BaseGenerator


def run_implementation(
    ctx: ProjectContext,
    output_dir: str,
    generators: list[BaseGenerator],
    console: Console,
) -> None:
    """Run the implementation phase for all specified generators."""

    for gen in generators:
        console.print(f"\n[bold cyan]🔧 Generating {gen.name} setup...[/bold cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Config
            task = progress.add_task(f"[cyan]Generating {gen.name} config...", total=None)
            config = gen.generate_config(ctx, output_dir)
            lines = len(config.splitlines()) if isinstance(config, str) else 0
            progress.update(task, description=f"[green]✅ Config ({lines} lines)")

            # Skills
            task = progress.add_task("[cyan]Generating skills...", total=None)
            skills = gen.generate_skills(ctx, output_dir)
            progress.update(
                task,
                description=f"[green]✅ Skills: {', '.join(skills) if skills else 'N/A'}",
            )

            # Hooks
            task = progress.add_task("[cyan]Generating hooks...", total=None)
            gen.generate_hooks(ctx, output_dir)
            progress.update(task, description="[green]✅ Hooks configured")

            # Agents
            task = progress.add_task("[cyan]Generating agents...", total=None)
            agents = gen.generate_agents(ctx, output_dir)
            progress.update(
                task,
                description=f"[green]✅ Agents: {', '.join(agents) if agents else 'N/A'}",
            )

            # Scaffold
            task = progress.add_task("[cyan]Generating scaffold...", total=None)
            scaffold = gen.generate_scaffold(ctx, output_dir)
            progress.update(task, description=f"[green]✅ Scaffold: {', '.join(scaffold)}")

    # Summary
    console.print("\n[bold]📊 Setup Summary[/bold]")
    for gen in generators:
        console.print(f"  • {gen.name}: {', '.join(gen.output_files)}")

    console.print("\n[bold]📖 How to Use:[/bold]")
    console.print("  1. Config files (CLAUDE.md, .cursorrules) load automatically")
    console.print("  2. Skills auto-trigger when relevant, or use /skill-name")
    console.print("  3. Hooks run deterministically on events (no manual invocation)")
    console.print("  4. Agents are used by explicitly asking the AI to delegate")
