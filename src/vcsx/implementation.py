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
        console.print(f"\nGenerating {gen.name} setup...")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Config
            task = progress.add_task(f"Generating {gen.name} config...", total=None)
            config = gen.generate_config(ctx, output_dir)
            lines = len(config.splitlines()) if isinstance(config, str) else 0
            progress.update(task, description=f"Config ({lines} lines)")

            # Skills
            task = progress.add_task("Generating skills...", total=None)
            skills = gen.generate_skills(ctx, output_dir)
            progress.update(
                task,
                description=f"Skills: {', '.join(skills) if skills else 'N/A'}",
            )

            # Hooks
            task = progress.add_task("Generating hooks...", total=None)
            gen.generate_hooks(ctx, output_dir)
            progress.update(task, description="Hooks configured")

            # Agents
            task = progress.add_task("Generating agents...", total=None)
            agents = gen.generate_agents(ctx, output_dir)
            progress.update(
                task,
                description=f"Agents: {', '.join(agents) if agents else 'N/A'}",
            )

            # Scaffold
            task = progress.add_task("Generating scaffold...", total=None)
            scaffold = gen.generate_scaffold(ctx, output_dir)
            progress.update(task, description=f"Scaffold: {', '.join(scaffold)}")

    # Summary
    console.print("\nSetup Summary")
    for gen in generators:
        console.print(f"  * {gen.name}: {', '.join(gen.output_files)}")

    console.print("\nHow to Use:")
    console.print("  1. Config files (CLAUDE.md, .cursorrules) load automatically")
    console.print("  2. Skills auto-trigger when relevant, or use /skill-name")
    console.print("  3. Hooks run deterministically on events (no manual invocation)")
    console.print("  4. Agents are used by explicitly asking the AI to delegate")
