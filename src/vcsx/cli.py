"""CLI entry point for vcsx."""

import platform
import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

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
    help="CLI tools to generate setup for (can be used multiple times for multi-tool)",
)
@click.option(
    "--all-tools",
    "-a",
    is_flag=True,
    default=False,
    help="Generate configs for ALL supported AI tools at once",
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
def init(cli, all_tools, lang, output_dir):
    """Start interactive setup wizard.

    Examples:
        vcsx init                          # Single tool (interactive)
        vcsx init -c claude-code -c cursor # Two specific tools
        vcsx init --all-tools              # All 10 tools at once
    """
    console.print(BANNER.format(version=__version__))
    console.print(
        Panel(
            "Vibe Coding Setup Expert",
            subtitle="AI Coding Environment Generator",
        )
    )

    console.print("\nPHASE 1: DISCOVERY")
    context = run_discovery(console, lang=lang)

    # Determine which tools to use (CLI flags override discovery)
    if all_tools:
        selected_tools = list(ALL_TOOLS)
        console.print(f"\n[cyan]All tools selected:[/] {', '.join(selected_tools)}")
    elif cli:
        selected_tools = list(cli)
        console.print(f"\n[cyan]Tools selected:[/] {', '.join(selected_tools)}")
    elif context.ai_tools_list:
        # Use multi-tool selection from discovery
        selected_tools = context.ai_tools_list
        if len(selected_tools) > 1:
            console.print(f"\n[cyan]Tools selected in discovery:[/] {', '.join(selected_tools)}")
    else:
        selected_tools = [context.ai_tool]

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
    console.print(f"Tools configured: {', '.join(selected_tools)}")


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
        ".zed/": "zed",
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
            gen.generate_all(ctx, str(target))
            console.print(f"[green]✓ {t} config added[/]")
        except Exception as e:
            console.print(f"[red]✗ Failed to add {t}: {e}[/]")

    console.print("\n[green]Done![/]")


@main.command("list")
def list_tools():
    """List available CLI tools."""
    table = Table(title="Available AI Tools (10 total)")
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
    console.print(f"\nUse [cyan]vcsx info <tool>[/] for details on any tool.")
    console.print(f"Use [cyan]vcsx init -c <tool> -c <tool>[/] to set up multiple tools at once.")


@main.command("info")
@click.argument("tool", required=False)
def info_tool(tool):
    """Show detailed info about a tool, including generated files."""
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

    gen = get_generator(tool)
    files = gen.output_files

    console.print(Panel(
        f"[bold]{tool}[/bold]\n\n{desc}\n\n"
        f"[dim]Category:[/dim] {category}\n\n"
        f"[dim]Generated files:[/dim]\n" + "\n".join(f"  • {f}" for f in files),
        title="Tool Info",
        border_style="cyan"
    ))


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
                "curl -L https://github.com/barancanercan/vcsx/releases/latest/download/vcsx.exe -o vcsx.exe",
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
@click.option(
    "--dir",
    "-d",
    type=click.Path(),
    default=".",
    help="Project directory to inspect (default: current directory)",
)
def doctor(dir):
    """Check vcsx installation and detect AI tools in a project."""
    target = Path(dir).resolve()
    console.print("Running diagnostics...\n")

    # --- Installation Checks ---
    install_table = Table(title="Installation", show_header=False)
    install_table.add_column("Check")
    install_table.add_column("Status")

    install_table.add_row("vcsx version", f"[green]OK[/] {__version__}")

    python_path = shutil.which("python") or shutil.which("python3")
    if python_path:
        install_table.add_row("Python", f"[green]OK[/] {python_path}")
    else:
        install_table.add_row("Python", "[red]Not found[/]")

    vcsx_path = shutil.which("vcsx")
    if vcsx_path:
        install_table.add_row("vcsx in PATH", f"[green]OK[/] {vcsx_path}")
    else:
        install_table.add_row("vcsx in PATH", "[yellow]Not in PATH[/] (use: python -m vcsx)")

    plugins = discover_plugins()
    install_table.add_row("Plugins", f"[green]OK[/] {len(plugins)} loaded")

    tools_count = len(ALL_TOOLS)
    install_table.add_row("AI Tools", f"[green]OK[/] {tools_count} available")

    registry = get_registry()
    enabled = len(registry.list_enabled())
    install_table.add_row("Generators", f"[green]OK[/] {enabled} enabled")

    console.print(install_table)

    # --- Project AI Tool Detection ---
    if target.exists():
        console.print(f"\n[bold]AI Tool Detection[/] — {target}\n")

        detection_map = {
            "CLAUDE.md": ("claude-code", ".claude/"),
            ".cursorrules": ("cursor", ".cursor/rules/"),
            ".windsurfrules": ("windsurf", ".windsurf/rules/"),
            ".github/copilot-instructions.md": ("copilot", ".github/instructions/"),
            "GEMINI.md": ("gemini", None),
            "AGENTS.md": ("agents-md", None),
            ".aider.conf.yaml": ("aider", None),
            ".bolt/workspace.json": ("bolt", None),
            ".openai/instructions.md": ("codex", None),
            ".zed/settings.json": ("zed", None),
        }

        detect_table = Table(title="Project Config Status")
        detect_table.add_column("Tool", style="cyan")
        detect_table.add_column("Config File", style="dim")
        detect_table.add_column("Status", style="bold")
        detect_table.add_column("Quality", style="dim")

        configured = []
        missing_tools = []

        for config_file, (tool_name, extra_dir) in detection_map.items():
            config_path = target / config_file
            if config_path.exists():
                configured.append(tool_name)
                # Quality check: does extra dir also exist?
                quality = "[green]Complete[/]"
                if extra_dir:
                    extra_path = target / extra_dir
                    if not extra_path.exists():
                        quality = "[yellow]Basic only[/] (run vcsx update)"
                detect_table.add_row(tool_name, config_file, "[green]✓ Found[/]", quality)
            else:
                missing_tools.append(tool_name)
                detect_table.add_row(tool_name, config_file, "[dim]✗ Not set up[/]", "—")

        console.print(detect_table)

        if configured:
            console.print(f"\n[green]✓ Configured:[/] {', '.join(configured)}")
        if missing_tools:
            console.print(f"\n[dim]Not configured:[/] {', '.join(missing_tools[:4])}{'...' if len(missing_tools) > 4 else ''}")
            console.print(
                "\nTo add a tool: [cyan]vcsx update --tool <name>[/]\n"
                "To add all:    [cyan]vcsx update --tool " + " --tool ".join(["gemini", "agents-md"]) + "[/]"
            )

        # Check .claudeignore
        if (target / "CLAUDE.md").exists() and not (target / ".claudeignore").exists():
            console.print(
                "\n[yellow]Tip:[/] Claude Code detected but no .claudeignore found.\n"
                "Run: [cyan]vcsx update --tool claude-code[/] to generate it."
            )

    # Platform info
    console.print(f"\n[dim]Platform:[/] {platform.system()} {platform.machine()}")
    console.print(f"[dim]Python:[/] {platform.python_version()}")


@main.command("check")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
def check_project(path, output_json):
    """Analyze a project's AI config quality and give a score.

    Checks for: config files present, quality indicators, best practices.

    Examples:
        vcsx check                    # Check current directory
        vcsx check ~/my-project       # Check specific project
        vcsx check ~/my-project --json  # JSON output for CI
    """
    import json as json_mod
    from vcsx.generators.registry import get_generator

    target = Path(path).resolve()

    checks = {
        "claude-code": {
            "files": ["CLAUDE.md", ".claude/settings.json", ".claude/skills"],
            "quality": [".claudeignore", ".claude/agents"],
        },
        "cursor": {
            "files": [".cursorrules"],
            "quality": [".cursor/rules"],
        },
        "windsurf": {
            "files": [".windsurfrules"],
            "quality": [".windsurf/rules"],
        },
        "copilot": {
            "files": [".github/copilot-instructions.md"],
            "quality": [".github/instructions"],
        },
        "gemini": {
            "files": ["GEMINI.md"],
            "quality": [],
        },
        "agents-md": {
            "files": ["AGENTS.md"],
            "quality": [],
        },
        "aider": {
            "files": [".aider.conf.yaml"],
            "quality": [".aider.context.md"],
        },
        "bolt": {
            "files": [".bolt/workspace.json"],
            "quality": [".bolt/prompts.md"],
        },
        "codex": {
            "files": [".openai/instructions.md"],
            "quality": [],
        },
        "zed": {
            "files": [".zed/settings.json"],
            "quality": [".zed/context.md", ".zed/hooks.toml"],
        },
    }

    results = {}
    total_score = 0
    max_score = 0

    for tool, cfg in checks.items():
        present_files = []
        missing_files = []
        quality_files = []

        for f in cfg["files"]:
            p = target / f
            if p.exists():
                present_files.append(f)
            else:
                missing_files.append(f)

        for f in cfg.get("quality", []):
            p = target / f
            if p.exists():
                quality_files.append(f)

        has_basic = len(present_files) > 0
        score = len(present_files) * 2 + len(quality_files)
        max_tool_score = len(cfg["files"]) * 2 + len(cfg.get("quality", []))

        results[tool] = {
            "configured": has_basic,
            "present": present_files,
            "missing": missing_files,
            "quality": quality_files,
            "score": score,
            "max_score": max_tool_score,
        }

        if has_basic:
            total_score += score
            max_score += max_tool_score

    configured_tools = [t for t, r in results.items() if r["configured"]]
    overall_pct = int((total_score / max_score * 100) if max_score > 0 else 0)

    if output_json:
        output = {
            "path": str(target),
            "tools_configured": len(configured_tools),
            "total_tools": len(checks),
            "overall_score": overall_pct,
            "tools": results,
        }
        console.print(json_mod.dumps(output, indent=2))
        return

    # Rich output
    console.print(f"\n[bold]vcsx check[/] — {target}\n")

    if not configured_tools:
        console.print("[yellow]No AI tool configs found.[/]")
        console.print("Run [cyan]vcsx init[/] to get started.")
        return

    table = Table(title=f"AI Config Quality — {len(configured_tools)}/{len(checks)} tools configured")
    table.add_column("Tool", style="cyan")
    table.add_column("Status")
    table.add_column("Core Files")
    table.add_column("Quality Extras")
    table.add_column("Score")

    for tool, r in results.items():
        if not r["configured"]:
            continue
        status = "[green]✓[/]"
        core = f"{len(r['present'])}/{len(r['present']) + len(r['missing'])}"
        quality = f"+{len(r['quality'])} extras" if r["quality"] else "—"
        pct = int(r["score"] / r["max_score"] * 100) if r["max_score"] > 0 else 0
        score_color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"
        table.add_row(tool, status, core, quality, f"[{score_color}]{pct}%[/]")

    console.print(table)

    # Overall score
    score_color = "green" if overall_pct >= 80 else "yellow" if overall_pct >= 50 else "red"
    console.print(f"\n[bold]Overall config quality:[/] [{score_color}]{overall_pct}%[/]")

    # Recommendations
    suggestions = []
    if "claude-code" in configured_tools:
        if not (target / ".claudeignore").exists():
            suggestions.append("Add .claudeignore: vcsx update --tool claude-code")
        if not (target / ".claude" / "agents").exists():
            suggestions.append("Add Claude agents: vcsx update --tool claude-code")
    if "CLAUDE.md" not in str(configured_tools) and "agents-md" not in configured_tools:
        suggestions.append("Add AGENTS.md (universal standard): vcsx update --tool agents-md")

    if suggestions:
        console.print("\n[bold]Recommendations:[/]")
        for s in suggestions:
            console.print(f"  • {s}")


@main.command("new")
@click.argument("project_name")
@click.option(
    "--type",
    "-t",
    "project_type",
    type=click.Choice(["web", "api", "cli", "library", "data-pipeline", "ml-model"]),
    default="web",
    help="Project type",
)
@click.option(
    "--lang",
    "-l",
    type=click.Choice(["python", "typescript", "javascript", "go", "rust"]),
    default="typescript",
    help="Primary language",
)
@click.option(
    "--tool",
    "-c",
    multiple=True,
    type=click.Choice(ALL_TOOLS),
    default=("claude-code",),
    help="AI tools to configure (default: claude-code)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=".",
    help="Parent directory where project folder will be created",
)
def new_project(project_name, project_type, lang, tool, output_dir):
    """Scaffold a new project with AI tool configs — no wizard needed.

    Examples:
        vcsx new my-api --type api --lang python
        vcsx new my-app --type web --lang typescript --tool cursor
        vcsx new my-lib --type library --lang python --tool claude-code --tool gemini
    """
    from vcsx.core.context import ProjectContext
    from vcsx.core.inference import infer_formatter, infer_linter, infer_test_framework

    project_dir = (Path(output_dir) / project_name).resolve()

    if project_dir.exists():
        console.print(f"[red]Error:[/] Directory already exists: {project_dir}")
        console.print("Use a different name or remove the directory first.")
        return

    project_dir.mkdir(parents=True)
    console.print(f"\n[bold]Creating {project_name}[/] ({project_type}, {lang})")
    console.print(f"Location: {project_dir}\n")

    ctx = ProjectContext(
        project_name=project_name,
        project_type=project_type,
        language=lang,
        tech_stack=lang,
        test_framework=infer_test_framework(lang),
        formatter=infer_formatter(lang),
        linter=infer_linter(lang),
        lang="en",
    )

    tools = list(tool)
    generators = [get_generator(t) for t in tools]

    with console.status(f"Scaffolding {project_name}..."):
        for gen in generators:
            gen.generate_all(ctx, str(project_dir))

    # Show summary
    table = Table(title=f"{project_name} — Created", border_style="green")
    table.add_column("Tool", style="cyan")
    table.add_column("Files Generated")

    for gen in generators:
        table.add_row(gen.name, ", ".join(gen.output_files[:3]))

    console.print(table)
    console.print(f"\n[green]✓ Done![/] Project ready at: {project_dir}")
    console.print("\nNext steps:")
    console.print(f"  cd {project_name}")
    console.print(f"  git init && git add . && git commit -m 'chore: initial vcsx setup'")
    if lang == "python":
        console.print(f"  python -m venv .venv && source .venv/bin/activate")
        console.print(f"  pip install -e '.[dev]'  # if pyproject.toml exists")
    elif lang in ("typescript", "javascript"):
        console.print(f"  npm install")


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


@main.command("migrate")
@click.argument("tool", type=click.Choice(["windsurf", "cursor", "claude-code", "copilot"]))
@click.option(
    "--dir",
    "-d",
    "target_dir",
    type=click.Path(exists=True),
    default=".",
    help="Project directory to migrate (default: current)",
)
@click.option("--dry-run", is_flag=True, help="Preview changes without writing files")
def migrate(tool, target_dir, dry_run):
    """Migrate an existing AI tool config to the latest format.

    \b
    windsurf   — .windsurfrules → .windsurf/rules/*.md (v2 format)
    cursor     — .cursorrules → .cursor/rules/*.mdc (modern format)
    claude-code — CLAUDE.md → add missing .claudeignore + agents/
    copilot    — copilot-instructions.md → add scoped instructions/

    Examples:
        vcsx migrate windsurf
        vcsx migrate cursor --dry-run
        vcsx migrate claude-code --dir ~/my-project
    """
    from vcsx.core.context import ProjectContext

    target = Path(target_dir).resolve()
    ctx = ProjectContext(project_name=target.name, lang="en")

    console.print(f"\n[bold]vcsx migrate {tool}[/] — {target}\n")

    if tool == "windsurf":
        old_file = target / ".windsurfrules"
        new_dir = target / ".windsurf" / "rules"

        if not old_file.exists():
            console.print("[yellow]No .windsurfrules found — nothing to migrate.[/]")
            return

        if new_dir.exists():
            console.print("[green]✓ .windsurf/rules/ already exists.[/] Already on new format.")
            return

        console.print(f"Will create: {new_dir}/")
        console.print("  • core-conventions.md (alwaysApply: true)")
        console.print("  • testing.md (globs: tests/**)")
        console.print("  • security.md (alwaysApply: false)")

        if dry_run:
            console.print("\n[dim]Dry run — no files written.[/]")
            return

        from vcsx.generators.windsurf import WindsurfGenerator
        WindsurfGenerator()._generate_windsurf_rules(ctx, str(target))
        console.print(f"\n[green]✓ Migrated![/] .windsurf/rules/ created.")
        console.print("[dim]Old .windsurfrules retained for backward compatibility.[/]")

    elif tool == "cursor":
        old_file = target / ".cursorrules"
        new_dir = target / ".cursor" / "rules"

        if not old_file.exists():
            console.print("[yellow]No .cursorrules found — nothing to migrate.[/]")
            return

        if new_dir.exists():
            console.print("[green]✓ .cursor/rules/ already exists.[/] Already on new format.")
            return

        console.print(f"Will create: {new_dir}/")
        console.print("  • build-test.mdc")
        console.print("  • commit-message.mdc")
        console.print("  • pr-review.mdc")
        console.print("  • test-patterns.mdc")

        if dry_run:
            console.print("\n[dim]Dry run — no files written.[/]")
            return

        from vcsx.generators.cursor import CursorGenerator
        CursorGenerator().generate_skills(ctx, str(target))
        console.print(f"\n[green]✓ Migrated![/] .cursor/rules/ created.")
        console.print("[dim]Old .cursorrules retained for backward compatibility.[/]")

    elif tool == "claude-code":
        claude_md = target / "CLAUDE.md"

        if not claude_md.exists():
            console.print("[yellow]No CLAUDE.md found — run 'vcsx init' first.[/]")
            return

        missing = []
        if not (target / ".claudeignore").exists():
            missing.append(".claudeignore")
        if not (target / ".claude" / "agents").exists():
            missing.append(".claude/agents/")

        if not missing:
            console.print("[green]✓ Claude Code config is already complete.[/]")
            return

        console.print(f"Will create: {', '.join(missing)}")

        if dry_run:
            console.print("\n[dim]Dry run — no files written.[/]")
            return

        from vcsx.generators.claude_code import ClaudeCodeGenerator
        gen = ClaudeCodeGenerator()
        if ".claudeignore" in missing:
            gen.generate_scaffold(ctx, str(target))
        if ".claude/agents/" in missing:
            gen.generate_agents(ctx, str(target))
        console.print(f"\n[green]✓ Claude Code config upgraded![/]")

    elif tool == "copilot":
        main_file = target / ".github" / "copilot-instructions.md"
        instructions_dir = target / ".github" / "instructions"

        if not main_file.exists():
            console.print("[yellow]No .github/copilot-instructions.md found — nothing to migrate.[/]")
            return

        if instructions_dir.exists():
            console.print("[green]✓ Scoped instructions already exist.[/]")
            return

        console.print(f"Will create: .github/instructions/")
        console.print("  • code-style.instructions.md")
        console.print("  • testing.instructions.md")
        console.print("  • security.instructions.md")

        if dry_run:
            console.print("\n[dim]Dry run — no files written.[/]")
            return

        from vcsx.generators.copilot import CopilotGenerator
        CopilotGenerator()._generate_scoped_instructions(ctx, str(target))
        console.print(f"\n[green]✓ Copilot scoped instructions created![/]")


@main.command("completion")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish", "powershell"]))
def completion(shell):
    """Print shell completion script.

    To enable completion, add to your shell profile:

    \b
    # bash (~/.bashrc)
    eval "$(vcsx completion bash)"

    # zsh (~/.zshrc)
    eval "$(vcsx completion zsh)"

    # fish (~/.config/fish/completions/vcsx.fish)
    vcsx completion fish | source
    """
    import os

    env_var = "_VCSX_COMPLETE"
    scripts = {
        "bash": f'eval "$({env_var}=bash_source vcsx)"',
        "zsh": f'eval "$({env_var}=zsh_source vcsx)"',
        "fish": f"eval (env {env_var}=fish_source vcsx)",
        "powershell": f"Invoke-Expression (& vcsx --{env_var}=powershell_source)",
    }

    setup_instructions = {
        "bash": "# Add to ~/.bashrc:\neval \"$(vcsx completion bash)\"",
        "zsh": "# Add to ~/.zshrc:\neval \"$(vcsx completion zsh)\"",
        "fish": "# Add to ~/.config/fish/completions/vcsx.fish:\nvcsx completion fish | source",
        "powershell": "# Add to $PROFILE:\nInvoke-Expression (& vcsx completion powershell)",
    }

    console.print(f"# vcsx shell completion for {shell}")
    console.print(setup_instructions[shell])
    console.print(f"\n# Auto-generated (requires click-completion or Click 8.x):")
    console.print(scripts[shell])


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
