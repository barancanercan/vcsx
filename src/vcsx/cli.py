"""CLI entry point for vcsx."""

import platform
import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from vcsx import __version__
from vcsx.discovery import run_discovery
from vcsx.generators.registry import (
    ALL_TOOLS,
    TOOL_CATEGORIES,
    TOOL_DESCRIPTIONS,
    get_generator,
    get_tools_by_category,
)
from vcsx.implementation import run_implementation
from vcsx.planner import confirm_plan, generate_plan
from vcsx.plugins import discover_plugins, get_registry
from vcsx.templates import get_template_registry, list_official_templates, search_templates

console = Console(force_terminal=False)

BANNER = """
  ==================
       [SETUP]
      vcsx
     v{version:>6}
  ==================
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
    default=None,
    type=click.Choice(ALL_TOOLS),
    help="CLI tools to generate setup for (optional - will ask in discovery)",
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
    console.print(BANNER.format(version=__version__))
    console.print(
        Panel(
            "Vibe Coding Setup Expert",
            subtitle="AI Coding Environment Generator",
        )
    )

    console.print("\nPHASE 1: DISCOVERY")
    context = run_discovery(console, lang=lang)

    # Use discovered AI tool, or CLI flag if provided
    selected_tools = list(cli) if cli else [context.ai_tool]

    console.print("\nPHASE 2: PLAN")
    generate_plan(context, console, selected_tools)
    if not confirm_plan(console):
        console.print("Setup cancelled. Run 'vcsx init' to try again.")
        return

    console.print("\nPHASE 3: IMPLEMENTATION")
    generators = [get_generator(t) for t in selected_tools]
    run_implementation(context, output_dir, generators, console)

    console.print("\nSetup complete!")
    console.print(f"Files generated in: {output_dir}")


@main.command("update")
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=".",
    help="Directory to update (default: current directory)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be added/updated without writing files",
)
@click.option(
    "--tool",
    "-t",
    multiple=True,
    type=click.Choice(ALL_TOOLS),
    help="Specific tool configs to add (default: auto-detect from existing files)",
)
def update(output_dir, dry_run, tool):
    """Update an existing project — add missing AI config files.

    Detects which config files exist and which are missing, then
    generates the missing ones without overwriting existing files.

    Examples:
        vcsx update               # Auto-detect and add missing configs
        vcsx update --dry-run     # Preview what would be added
        vcsx update --tool gemini # Add Gemini CLI config only
    """
    target = Path(output_dir).resolve()
    console.print(f"\n[bold cyan]vcsx update[/] — Scanning: {target}\n")

    # Detection map: file/dir → tool name
    detection_map = {
        "CLAUDE.md": "claude-code",
        ".claude/": "claude-code",
        ".cursorrules": "cursor",
        ".cursor/rules/": "cursor",
        ".windsurfrules": "windsurf",
        ".windsurf/": "windsurf",
        ".github/copilot-instructions.md": "copilot",
        "AGENTS.md": "agents-md",
        "GEMINI.md": "gemini",
        ".aider.conf.yaml": "aider",
        ".bolt/": "bolt",
        ".openai/": "codex",
    }

    # Detect what's already present
    present = []
    for path_str, tool_name in detection_map.items():
        p = target / path_str
        if p.exists():
            present.append(tool_name)

    # Detect what's missing (keys: claudeignore, agents.md, etc.)
    missing_files = []
    if (target / "CLAUDE.md").exists() and not (target / ".claudeignore").exists():
        missing_files.append(".claudeignore")
    if (target / "CLAUDE.md").exists() and not (target / "AGENTS.md").exists():
        missing_files.append("AGENTS.md")
    if (target / ".windsurfrules").exists() and not (target / ".windsurf" / "rules").exists():
        missing_files.append(".windsurf/rules/ (new format)")

    # Determine which tools to add
    tools_to_add = list(tool) if tool else []

    # Summary table
    table = Table(title="Config Status")
    table.add_column("File / Config", style="cyan")
    table.add_column("Status", style="bold")

    for path_str, tool_name in detection_map.items():
        p = target / path_str
        status = "[green]✓ Present[/]" if p.exists() else "[yellow]✗ Missing[/]"
        table.add_row(path_str, status)

    for mf in missing_files:
        table.add_row(mf, "[yellow]✗ Missing (upgrade available)[/]")

    console.print(table)

    if missing_files:
        console.print(f"\n[yellow]Upgrade opportunities:[/] {', '.join(missing_files)}")

    if not tools_to_add and not missing_files:
        console.print("\n[green]✓ Everything looks up to date![/]")
        return

    if dry_run:
        console.print("\n[dim]Dry run — no files written.[/]")
        if tools_to_add:
            console.print(f"Would add configs for: {', '.join(tools_to_add)}")
        if missing_files:
            console.print(f"Would generate: {', '.join(missing_files)}")
        return

    if not tools_to_add:
        console.print("\nRun with [cyan]--tool <name>[/] to add a specific tool, e.g.:")
        console.print("  vcsx update --tool gemini")
        console.print("  vcsx update --tool agents-md")
        return

    # Run generators for requested tools
    from vcsx.core.context import ProjectContext
    ctx = ProjectContext(project_name=target.name, lang="en")

    for t in tools_to_add:
        gen = get_generator(t)
        console.print(f"\n[cyan]Adding {t}...[/]")
        try:
            result = gen.generate_all(ctx, str(target))
            console.print(f"[green]✓ {t} config added[/]")
        except Exception as e:
            console.print(f"[red]✗ Failed to add {t}: {e}[/]")

    console.print("\n[green]Done![/]")


@main.command("list")
def list_tools():
    """List available CLI tools."""
    table = Table(title="Available AI Tools")
    table.add_column("Tool", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Description", style="dim")

    for tool in ALL_TOOLS:
        category = "unknown"
        for cat, tools in TOOL_CATEGORIES.items():
            if tool in tools:
                category = cat
                break
        desc = TOOL_DESCRIPTIONS.get(tool, "")
        table.add_row(tool, category, desc)

    console.print(table)


@main.command("info")
@click.argument("tool", required=False)
def info_tool(tool):
    """Show detailed info about a tool."""
    if not tool:
        console.print("Usage: vcsx info <tool>")
        console.print("Run 'vcsx list' for available tools")
        return

    if tool not in ALL_TOOLS:
        console.print(f"Unknown tool: {tool}")
        console.print(f"Available: {', '.join(ALL_TOOLS)}")
        return

    desc = TOOL_DESCRIPTIONS.get(tool, "")
    category = "unknown"
    for cat, tools in TOOL_CATEGORIES.items():
        if tool in tools:
            category = cat
            break

    console.print(Panel(f"{tool}\n\n{desc}", title="Tool Info", border_style="cyan"))
    console.print(f"Category: {category}")


@main.command("install")
@click.argument("method", type=click.Choice(["pip", "brew", "exe", "npx", "npm"]))
def install_vcsx(method):
    """Show installation instructions for different methods."""
    instructions = {
        "pip": {
            "title": "PyPI (Python Package Index)",
            "commands": [
                "pip install vcsx",
                "vcsx init",
            ],
        },
        "brew": {
            "title": "Homebrew (macOS/Linux)",
            "commands": [
                "brew tap vcsx/tap",
                "brew install vcsx",
                "vcsx init",
            ],
        },
        "exe": {
            "title": "Standalone Executable",
            "commands": [
                "# Download from GitHub Releases",
                "curl -L https://github.com/vibe-coding-setup-expert/vcsx/releases/latest/download/vcsx.exe -o vcsx.exe",
                "./vcsx.exe init",
            ],
        },
        "npx": {
            "title": "npx (npm)",
            "commands": [
                "npx vcsx init",
                "# Or install globally: npm install -g vcsx",
            ],
        },
        "npm": {
            "title": "npm (Global)",
            "commands": [
                "npm install -g vcsx",
                "vcsx init",
            ],
        },
    }

    inst = instructions.get(method)
    if inst:
        console.print(Panel(f"{inst['title']}", border_style="cyan"))
        for cmd in inst["commands"]:
            console.print(f"  $ {cmd}")


@main.command("doctor")
def doctor():
    """Check vcsx installation and dependencies."""
    console.print("Running diagnostics...\n")

    table = Table(show_header=False)
    table.add_column("Check")
    table.add_column("Status")

    version = __version__
    table.add_row("Version", f"OK {version}")

    python_path = shutil.which("python") or shutil.which("python3")
    if python_path:
        table.add_row("Python", "OK Found")
    else:
        table.add_row("Python", "Not found")

    vcsx_path = shutil.which("vcsx")
    if vcsx_path:
        table.add_row("vcsx in PATH", f"OK {vcsx_path}")
    else:
        table.add_row("vcsx in PATH", "Not in PATH (use python -m vcsx)")

    plugins = discover_plugins()
    table.add_row("Plugins", f"OK {len(plugins)} loaded")

    tools_count = len(ALL_TOOLS)
    table.add_row("AI Tools", f"OK {tools_count} available")

    registry = get_registry()
    enabled = len(registry.list_enabled())
    table.add_row("Generators", f"OK {enabled} enabled")

    console.print(table)


@main.command("plugins")
def list_plugins():
    """List available plugins."""
    plugins = discover_plugins()

    if not plugins:
        console.print("No plugins installed")
        return

    table = Table(title="Installed Plugins")
    table.add_column("Name")
    table.add_column("Version")

    for plugin in plugins:
        table.add_row(plugin.name, plugin.version)

    console.print(table)


@main.command("templates")
@click.argument("query", required=False)
def list_templates(query):
    """List or search available templates."""
    if query:
        results = search_templates(query)
    else:
        results = list_official_templates()

    if not results:
        console.print("No templates found")
        return

    table = Table(title=f"{'Search Results' if query else 'Official Templates'}")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Tech Stack")

    for template in results:
        tech_stack = ", ".join(f"{k}={v}" for k, v in template.tech_stack.items())
        table.add_row(template.name, template.description, tech_stack)

    console.print(table)


@main.command("templates:install")
@click.argument("template_name")
def install_template(template_name):
    """Install a template."""
    from vcsx.templates import get_template_registry

    registry = get_template_registry()
    template = registry.get(template_name)

    if not template:
        console.print(f"Template not found: {template_name}")
        available = [t.metadata.name for t in registry.list_all()]
        console.print(f"Available: {', '.join(available)}")
        return

    console.print(f"Template '{template_name}' installed")
    console.print(f"Files: {', '.join(template.list_files())}")
