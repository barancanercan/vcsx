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
)
from vcsx.implementation import run_implementation
from vcsx.planner import confirm_plan, generate_plan
from vcsx.plugins import discover_plugins, get_registry
from vcsx.templates import get_template_registry, list_official_templates, search_templates

console = Console(force_terminal=False)


def _load_config() -> dict:
    """Load user config from ~/.vcsx/config.json with defaults."""
    import json

    defaults = {
        "default_tool": "claude-code",
        "default_lang": "typescript",
        "default_type": "web",
        "lang": "tr",
        "auto_push": False,
    }
    config_file = Path.home() / ".vcsx" / "config.json"
    if config_file.exists():
        try:
            return {**defaults, **json.loads(config_file.read_text())}
        except Exception:
            pass
    return defaults


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
@click.option(
    "--fast",
    "-f",
    is_flag=True,
    default=False,
    help="Fast mode: skip full discovery, just ask project name and stack",
)
@click.option(
    "--scan",
    "-s",
    is_flag=True,
    default=False,
    help="Scan mode: auto-detect tech stack from existing project files",
)
def init(cli, all_tools, lang, output_dir, fast, scan):
    """Start interactive setup wizard.

    \b
    Examples:
        vcsx init                          # Full interactive wizard
        vcsx init --fast                   # Fast mode (minimal questions)
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

    # Scan mode: auto-detect from project files
    if scan:
        from vcsx.core.context import ProjectContext
        from vcsx.core.inference import infer_formatter, infer_linter, infer_test_framework
        from vcsx.core.scanner import format_scan_summary, scan_project

        scan_dir = output_dir if output_dir != "." else "."
        detected = scan_project(scan_dir)

        console.print(
            f"\n[bold cyan]Scan Mode[/] — Auto-detecting from: {Path(scan_dir).resolve()}"
        )
        console.print(f"[green]✓ Detected:[/] {format_scan_summary(detected)}\n")

        context = ProjectContext(
            project_name=detected.get("project_name", "my-project"),
            description=detected.get("description", ""),
            language=detected.get("language", "typescript"),
            framework=detected.get("framework", ""),
            tech_stack=detected.get("tech_stack", ""),
            project_type=detected.get("project_type", "web"),
            test_framework=detected.get("test_framework", ""),
            lang="en",
        )
        # Fill in inferred values if not detected
        if not context.test_framework:
            context.test_framework = infer_test_framework(context.language)
        if not context.formatter:
            context.formatter = infer_formatter(context.language)
        if not context.linter:
            context.linter = infer_linter(context.language)

    # Fast mode: skip full discovery
    elif fast:
        from rich.prompt import Prompt

        from vcsx.core.context import ProjectContext
        from vcsx.core.inference import (
            infer_formatter,
            infer_language,
            infer_linter,
            infer_test_framework,
        )

        user_cfg = _load_config()
        console.print("\n[bold cyan]Fast Mode[/] — minimal questions\n")
        project_name = Prompt.ask("Project name", default="my-project")
        default_stack = user_cfg.get("default_lang", "typescript")
        tech_stack = Prompt.ask(
            "Tech stack (e.g. Python, FastAPI / TypeScript, React)",
            default=default_stack,
        )
        inferred_lang = infer_language(tech_stack)

        context = ProjectContext(
            project_name=project_name,
            tech_stack=tech_stack,
            language=inferred_lang,
            test_framework=infer_test_framework(inferred_lang),
            formatter=infer_formatter(inferred_lang),
            linter=infer_linter(inferred_lang),
            lang="en",
        )
        console.print(f"\n[green]✓[/] Language detected: [cyan]{inferred_lang}[/]")
    else:
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

    if not fast and not scan:
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
@click.option(
    "--auto",
    is_flag=True,
    default=False,
    help="Auto-apply all detected upgrades without prompting",
)
def update(output_dir, dry_run, tool, auto):
    """Update an existing project — add missing AI config files.

    Detects which config files exist and which are missing, then
    generates the missing ones without overwriting existing files.

    Examples:
        vcsx update               # Auto-detect and add missing configs
        vcsx update --dry-run     # Preview what would be added
        vcsx update --tool gemini # Add Gemini CLI config only
        vcsx update --auto        # Auto-apply all detected upgrades
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

    # --auto: apply all detected upgrades automatically
    if auto and missing_files and not tools_to_add:
        console.print("\n[cyan]Auto-applying upgrades...[/]")
        from vcsx.core.context import ProjectContext

        ctx = ProjectContext(project_name=target.name, lang="en")
        if ".claudeignore" in missing_files and (target / "CLAUDE.md").exists():
            from vcsx.generators.claude_code import ClaudeCodeGenerator

            ClaudeCodeGenerator().generate_scaffold(ctx, str(target))
            console.print("[green]✓ .claudeignore generated[/]")
        if "AGENTS.md" in missing_files:
            from vcsx.generators.agents_md import AgentsMdGenerator

            AgentsMdGenerator().generate_config(ctx, str(target))
            console.print("[green]✓ AGENTS.md generated[/]")
        if ".windsurf/rules/ (new format)" in missing_files:
            from vcsx.generators.windsurf import WindsurfGenerator

            WindsurfGenerator()._generate_windsurf_rules(ctx, str(target))
            console.print("[green]✓ .windsurf/rules/ generated[/]")
        console.print("\n[green]Done![/]")
        return

    if not tools_to_add:
        console.print("\nRun with [cyan]--tool <name>[/] to add a specific tool, e.g.:")
        console.print("  vcsx update --tool gemini")
        console.print("  vcsx update --tool agents-md")
        console.print("  vcsx update --auto        # apply all detected upgrades")
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
    console.print("\nUse [cyan]vcsx info <tool>[/] for details on any tool.")
    console.print("Use [cyan]vcsx init -c <tool> -c <tool>[/] to set up multiple tools at once.")


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

    console.print(
        Panel(
            f"[bold]{tool}[/bold]\n\n{desc}\n\n"
            f"[dim]Category:[/dim] {category}\n\n"
            f"[dim]Generated files:[/dim]\n" + "\n".join(f"  • {f}" for f in files),
            title="Tool Info",
            border_style="cyan",
        )
    )


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
            console.print(
                f"\n[dim]Not configured:[/] {', '.join(missing_tools[:4])}{'...' if len(missing_tools) > 4 else ''}"
            )
            console.print(
                "\nTo add a tool: [cyan]vcsx update --tool <name>[/]\n"
                "To add all:    [cyan]vcsx update --tool "
                + " --tool ".join(["gemini", "agents-md"])
                + "[/]"
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

    table = Table(
        title=f"AI Config Quality — {len(configured_tools)}/{len(checks)} tools configured"
    )
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
    type=click.Choice(
        [
            "python",
            "typescript",
            "javascript",
            "go",
            "rust",
            "kotlin",
            "swift",
            "dart",
            "csharp",
            "php",
            "ruby",
        ]
    ),
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
    "--preset",
    "-p",
    default=None,
    help="Use a template preset (e.g. fastapi-postgres, react-typescript, go-api)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=".",
    help="Parent directory where project folder will be created",
)
def new_project(project_name, project_type, lang, tool, preset, output_dir):
    """Scaffold a new project with AI tool configs — no wizard needed.

    Examples:
        vcsx new my-api --type api --lang python
        vcsx new my-app --type web --lang typescript --tool cursor
        vcsx new my-lib --type library --lang python --tool claude-code --tool gemini
    """
    from vcsx.core.context import ProjectContext
    from vcsx.core.inference import infer_formatter, infer_linter, infer_test_framework

    # Apply preset if given
    if preset:
        from vcsx.templates import get_template_registry

        registry = get_template_registry()
        tmpl = registry.get(preset)
        if tmpl:
            meta = tmpl.metadata
            lang = meta.tech_stack.get("language", lang)
            project_type = meta.tech_stack.get("type", project_type)
            console.print(f"[cyan]Using preset:[/] {preset} — {meta.description}")
        else:
            available = [t.metadata.name for t in get_template_registry().list_all()]
            console.print(
                f"[yellow]Unknown preset '{preset}'.[/] Available: {', '.join(available)}"
            )

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
    console.print("  git init && git add . && git commit -m 'chore: initial vcsx setup'")
    if lang == "python":
        console.print("  python -m venv .venv && source .venv/bin/activate")
        console.print("  pip install -e '.[dev]'  # if pyproject.toml exists")
    elif lang in ("typescript", "javascript"):
        console.print("  npm install")


@main.command("export")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output ZIP file path (default: <project-name>-ai-configs.zip)",
)
@click.option(
    "--include-all",
    is_flag=True,
    default=False,
    help="Include all files including .gitignore, README, etc.",
)
def export_configs(path, output, include_all):
    """Export all AI config files to a ZIP archive.

    Useful for sharing configs across projects or backing up setups.

    Examples:
        vcsx export                           # Export current project configs
        vcsx export ~/my-project              # Export specific project
        vcsx export --output my-configs.zip   # Custom output name
        vcsx export --include-all             # Include all project files
    """
    import zipfile

    target = Path(path).resolve()
    project_name = target.name

    # Determine output path
    if output:
        zip_path = Path(output)
    else:
        zip_path = Path(f"{project_name}-ai-configs.zip")

    # AI config patterns to include
    ai_patterns = [
        "CLAUDE.md",
        ".claudeignore",
        "GEMINI.md",
        "AGENTS.md",
        ".aider.conf.yaml",
        ".aider.context.md",
        ".cursorrules",
        ".windsurfrules",
        ".claude/**",
        ".cursor/**",
        ".windsurf/**",
        ".zed/**",
        ".bolt/**",
        ".openai/**",
        ".github/copilot-instructions.md",
        ".github/instructions/**",
    ]

    collected = []

    def should_include(rel_path: str) -> bool:
        if include_all:
            return True
        p = rel_path.replace("\\", "/")
        for pattern in ai_patterns:
            if pattern.endswith("/**"):
                prefix = pattern[:-3]
                if p.startswith(prefix):
                    return True
            elif p == pattern or p.startswith(pattern.rstrip("*")):
                return True
        return False

    # Walk directory
    for file_path in sorted(target.rglob("*")):
        if file_path.is_file():
            # Skip .git and common build dirs
            parts = file_path.relative_to(target).parts
            if any(
                p in (".git", "node_modules", "__pycache__", ".venv", "dist", "build")
                for p in parts
            ):
                continue
            rel = str(file_path.relative_to(target))
            if should_include(rel):
                collected.append((file_path, rel))

    if not collected:
        console.print("[yellow]No AI config files found to export.[/]")
        console.print("Run [cyan]vcsx init[/] to set up AI configs first.")
        return

    # Write ZIP
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path, rel in collected:
            zf.write(file_path, rel)

    total_size = zip_path.stat().st_size
    size_kb = total_size / 1024

    console.print(f"\n[bold]vcsx export[/] — {target}")
    console.print(f"\n[green]✓ Exported {len(collected)} files → {zip_path}[/]")
    console.print(f"  Size: {size_kb:.1f} KB")
    console.print("\n[dim]Files included:[/]")
    for _, rel in collected[:20]:
        console.print(f"  • {rel}")
    if len(collected) > 20:
        console.print(f"  ... and {len(collected) - 20} more")

    console.print("\n[dim]To use in another project:[/]")
    console.print(f"  unzip {zip_path} -d /path/to/project")


@main.command("stats")
@click.argument("path", default=".", type=click.Path(exists=True))
def stats(path):
    """Show statistics about AI config files in a project.

    Counts skills, hooks, agents, rules, and config files.

    Examples:
        vcsx stats                  # Current directory
        vcsx stats ~/my-project     # Specific project
    """
    target = Path(path).resolve()
    console.print(f"\n[bold]vcsx stats[/] — {target}\n")

    stats_data = {
        "tools_configured": 0,
        "skills": 0,
        "hooks": 0,
        "agents": 0,
        "rules": 0,
        "total_config_files": 0,
        "total_config_lines": 0,
    }

    tool_counts = {}

    # Claude Code
    claude_md = target / "CLAUDE.md"
    if claude_md.exists():
        stats_data["tools_configured"] += 1
        stats_data["total_config_files"] += 1
        stats_data["total_config_lines"] += len(claude_md.read_text().splitlines())
        tool_counts["claude-code"] = {"skills": 0, "hooks": 0, "agents": 0}

        skills_dir = target / ".claude" / "skills"
        if skills_dir.exists():
            skill_count = sum(1 for _ in skills_dir.glob("*/SKILL.md"))
            stats_data["skills"] += skill_count
            tool_counts["claude-code"]["skills"] = skill_count

        hooks_dir = target / ".claude" / "hooks"
        if hooks_dir.exists():
            hook_count = sum(1 for _ in hooks_dir.glob("*.sh"))
            stats_data["hooks"] += hook_count
            tool_counts["claude-code"]["hooks"] = hook_count

        agents_dir = target / ".claude" / "agents"
        if agents_dir.exists():
            agent_count = sum(1 for _ in agents_dir.glob("*.md"))
            stats_data["agents"] += agent_count
            tool_counts["claude-code"]["agents"] = agent_count

    # Cursor
    if (target / ".cursorrules").exists():
        stats_data["tools_configured"] += 1
        stats_data["total_config_files"] += 1
        rules_dir = target / ".cursor" / "rules"
        if rules_dir.exists():
            rule_count = sum(1 for _ in rules_dir.glob("*.mdc"))
            stats_data["rules"] += rule_count
            tool_counts["cursor"] = {"rules": rule_count}

    # Windsurf
    if (target / ".windsurfrules").exists():
        stats_data["tools_configured"] += 1
        stats_data["total_config_files"] += 1
        rules_dir = target / ".windsurf" / "rules"
        if rules_dir.exists():
            rule_count = sum(1 for _ in rules_dir.glob("*.md"))
            stats_data["rules"] += rule_count
            tool_counts["windsurf"] = {"rules": rule_count}

    # Other tools
    simple_checks = {
        "GEMINI.md": "gemini",
        "AGENTS.md": "agents-md",
        ".aider.conf.yaml": "aider",
        ".bolt/workspace.json": "bolt",
        ".openai/instructions.md": "codex",
        ".github/copilot-instructions.md": "copilot",
        ".zed/settings.json": "zed",
    }
    for f, tool in simple_checks.items():
        if (target / f).exists():
            stats_data["tools_configured"] += 1
            stats_data["total_config_files"] += 1

    # Copilot scoped instructions
    instructions_dir = target / ".github" / "instructions"
    if instructions_dir.exists():
        instr_count = sum(1 for _ in instructions_dir.glob("*.instructions.md"))
        if instr_count:
            tool_counts["copilot"] = {"scoped_instructions": instr_count}

    if stats_data["tools_configured"] == 0:
        console.print("[yellow]No AI tool configs found.[/]")
        console.print("Run [cyan]vcsx init[/] to get started.")
        return

    # Summary table
    table = Table(title="AI Config Statistics", border_style="cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Count", style="bold cyan", justify="right")

    table.add_row("Tools configured", str(stats_data["tools_configured"]))
    table.add_row("Skills (Claude Code)", str(stats_data["skills"]))
    table.add_row("Hooks (Claude Code)", str(stats_data["hooks"]))
    table.add_row("Agents (Claude Code)", str(stats_data["agents"]))
    table.add_row("Scoped rules (Cursor/Windsurf)", str(stats_data["rules"]))
    table.add_row("Config files total", str(stats_data["total_config_files"]))
    if stats_data["total_config_lines"]:
        table.add_row("Config lines (CLAUDE.md)", str(stats_data["total_config_lines"]))

    console.print(table)

    # Per-tool breakdown
    if tool_counts:
        console.print("\n[bold]Per-tool breakdown:[/]")
        for tool, counts in tool_counts.items():
            parts = ", ".join(f"{v} {k}" for k, v in counts.items() if v)
            if parts:
                console.print(f"  [cyan]{tool}:[/] {parts}")


@main.command("config")
@click.option("--set", "set_key", nargs=2, metavar="KEY VALUE", help="Set a config value")
@click.option("--get", "get_key", metavar="KEY", help="Get a config value")
@click.option("--list", "list_all", is_flag=True, help="List all config values")
@click.option("--reset", is_flag=True, help="Reset config to defaults")
def config_cmd(set_key, get_key, list_all, reset):
    """Manage vcsx user configuration (~/.vcsx/config.json).

    \b
    Available config keys:
      default_tool     Default AI tool (default: claude-code)
      default_lang     Default language (default: typescript)
      default_type     Default project type (default: web)
      lang             UI language: tr or en (default: tr)
      auto_push        Auto git-push after generate (default: false)

    \b
    Examples:
        vcsx config --set default_tool cursor
        vcsx config --set default_lang python
        vcsx config --set lang en
        vcsx config --get default_tool
        vcsx config --list
        vcsx config --reset
    """
    import json

    config_dir = Path.home() / ".vcsx"
    config_file = config_dir / "config.json"
    config_dir.mkdir(exist_ok=True)

    defaults = {
        "default_tool": "claude-code",
        "default_lang": "typescript",
        "default_type": "web",
        "lang": "tr",
        "auto_push": False,
    }

    # Load existing config
    if config_file.exists():
        try:
            cfg = json.loads(config_file.read_text())
        except Exception:
            cfg = {}
    else:
        cfg = {}

    if reset:
        config_file.write_text(json.dumps(defaults, indent=2))
        console.print("[green]✓ Config reset to defaults.[/]")
        return

    if set_key:
        key, value = set_key
        if key not in defaults:
            console.print(f"[red]Unknown key:[/] {key}")
            console.print(f"Available keys: {', '.join(defaults.keys())}")
            return
        # Type coerce
        if key == "auto_push":
            value = value.lower() in ("true", "1", "yes")
        cfg[key] = value
        config_file.write_text(json.dumps(cfg, indent=2))
        console.print(f"[green]✓ Set[/] {key} = {value}")
        return

    if get_key:
        merged = {**defaults, **cfg}
        if get_key not in merged:
            console.print(f"[red]Unknown key:[/] {get_key}")
            return
        console.print(f"{get_key} = {merged[get_key]}")
        return

    # Default: list all
    merged = {**defaults, **cfg}
    table = Table(title=f"vcsx config ({config_file})")
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    table.add_column("Source", style="dim")

    for key, default_val in defaults.items():
        current = merged[key]
        source = "user" if key in cfg else "default"
        table.add_row(key, str(current), source)

    console.print(table)


@main.command("audit")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--fix", "auto_fix", is_flag=True, help="Auto-fix issues where possible")
def audit_project(path, auto_fix):
    """Run a comprehensive audit of all AI configs in a project.

    Combines check + validate + stats into one actionable report.
    With --fix, auto-applies safe fixes.

    Examples:
        vcsx audit                  # Audit current project
        vcsx audit ~/my-project     # Audit specific project
        vcsx audit --fix            # Audit and auto-fix safe issues
    """
    target = Path(path).resolve()
    console.print(f"\n[bold]vcsx audit[/] — {target}\n")

    issues = []
    warnings = []
    fixes_applied = []

    # 1. Check which tools are configured
    tool_files = {
        "claude-code": "CLAUDE.md",
        "cursor": ".cursorrules",
        "windsurf": ".windsurfrules",
        "gemini": "GEMINI.md",
        "agents-md": "AGENTS.md",
        "aider": ".aider.conf.yaml",
        "copilot": ".github/copilot-instructions.md",
        "zed": ".zed/settings.json",
        "bolt": ".bolt/workspace.json",
        "codex": ".openai/instructions.md",
    }
    configured = [t for t, f in tool_files.items() if (target / f).exists()]

    if not configured:
        console.print("[yellow]No AI configs found. Run vcsx init to get started.[/]")
        return

    console.print(f"[bold]Configured tools ({len(configured)}):[/] {', '.join(configured)}\n")

    # 2. Claude Code specific checks
    if "claude-code" in configured:
        claude_md = target / "CLAUDE.md"
        lines = len(claude_md.read_text().splitlines())
        if lines > 200:
            issues.append(f"CLAUDE.md: {lines} lines (max 200) — too large, AI context bloat")
        elif lines > 150:
            warnings.append(f"CLAUDE.md: {lines} lines — consider trimming to < 150")
        else:
            console.print(f"  [green]✓[/] CLAUDE.md: {lines} lines (OK)")

        if not (target / ".claudeignore").exists():
            issues.append("Missing .claudeignore — context window not optimized")
            if auto_fix:
                from vcsx.core.context import ProjectContext
                from vcsx.generators.claude_code import ClaudeCodeGenerator

                ctx = ProjectContext(project_name=target.name)
                ClaudeCodeGenerator().generate_scaffold(ctx, str(target))
                fixes_applied.append("Generated .claudeignore")
        else:
            console.print("  [green]✓[/] .claudeignore present")

        skills_count = (
            sum(1 for _ in (target / ".claude" / "skills").glob("*/SKILL.md"))
            if (target / ".claude" / "skills").exists()
            else 0
        )
        hooks_count = (
            sum(1 for _ in (target / ".claude" / "hooks").glob("*.sh"))
            if (target / ".claude" / "hooks").exists()
            else 0
        )
        agents_count = (
            sum(1 for _ in (target / ".claude" / "agents").glob("*.md"))
            if (target / ".claude" / "agents").exists()
            else 0
        )

        console.print(
            f"  [green]✓[/] Skills: {skills_count} | Hooks: {hooks_count} | Agents: {agents_count}"
        )
        if skills_count < 5:
            warnings.append(
                f"Only {skills_count} skills — run vcsx generate claude-code to add more"
            )

    # 3. Security: check for .env in repo
    gitignore = target / ".gitignore"
    env_file = target / ".env"
    if env_file.exists():
        if gitignore.exists() and ".env" not in gitignore.read_text():
            issues.append("SECURITY: .env exists but not in .gitignore!")
        elif not gitignore.exists():
            issues.append("SECURITY: .env exists but no .gitignore found!")
        else:
            console.print("  [green]✓[/] .env in .gitignore")

    # 4. Aider config validation
    if "aider" in configured:
        aider_conf = (target / ".aider.conf.yaml").read_text()
        invalid = [k for k in ["repo:", "tools:", "command:", "only:"] if k in aider_conf]
        if invalid:
            issues.append(f".aider.conf.yaml has invalid keys: {', '.join(invalid)}")

    # 5. Windsurf format check
    if "windsurf" in configured:
        if not (target / ".windsurf" / "rules").exists():
            warnings.append("Windsurf: only legacy .windsurfrules — run: vcsx migrate windsurf")

    # 6. Cursor format check
    if "cursor" in configured:
        if not (target / ".cursor" / "rules").exists():
            warnings.append("Cursor: only legacy .cursorrules — run: vcsx migrate cursor")

    # 7. Universal standard
    if "agents-md" not in configured:
        warnings.append("No AGENTS.md (universal standard) — run: vcsx update --tool agents-md")

    # Print results
    console.print()
    if issues:
        console.print("[bold red]Issues:[/]")
        for i in issues:
            console.print(f"  ✗ {i}")

    if warnings:
        console.print("\n[bold yellow]Warnings:[/]")
        for w in warnings:
            console.print(f"  ⚠ {w}")

    if fixes_applied:
        console.print("\n[bold green]Auto-fixed:[/]")
        for f in fixes_applied:
            console.print(f"  ✓ {f}")

    total = len(issues) + len(warnings)
    console.print()
    if total == 0:
        console.print("[bold green]✓ Audit passed — all checks clean![/]")
    elif issues:
        console.print(f"[bold red]{len(issues)} issue(s), {len(warnings)} warning(s)[/]")
        console.print("Run [cyan]vcsx audit --fix[/] to auto-fix safe issues.")
    else:
        console.print(f"[yellow]{len(warnings)} warning(s)[/] — no critical issues.")


@main.command("compare")
@click.argument("path_a", type=click.Path(exists=True))
@click.argument("path_b", type=click.Path(exists=True))
def compare_projects(path_a, path_b):
    """Compare AI config files between two projects.

    Shows which tools are configured in each, what's missing,
    and highlights config differences.

    Examples:
        vcsx compare ~/project-a ~/project-b
        vcsx compare . ../other-project
    """
    target_a = Path(path_a).resolve()
    target_b = Path(path_b).resolve()

    console.print("\n[bold]vcsx compare[/]")
    console.print(f"  A: {target_a}")
    console.print(f"  B: {target_b}\n")

    # Config files to compare
    config_files = {
        "claude-code": ["CLAUDE.md", ".claudeignore", ".claude/settings.json"],
        "cursor": [".cursorrules"],
        "windsurf": [".windsurfrules"],
        "copilot": [".github/copilot-instructions.md"],
        "gemini": ["GEMINI.md"],
        "agents-md": ["AGENTS.md"],
        "aider": [".aider.conf.yaml"],
        "bolt": [".bolt/workspace.json"],
        "codex": [".openai/instructions.md"],
        "zed": [".zed/settings.json"],
    }

    table = Table(title="Config Comparison", border_style="cyan")
    table.add_column("Tool", style="cyan")
    table.add_column(f"A: {target_a.name}", style="bold")
    table.add_column(f"B: {target_b.name}", style="bold")
    table.add_column("Status")

    only_in_a = []
    only_in_b = []
    in_both = []

    for tool, files in config_files.items():
        has_a = any((target_a / f).exists() for f in files)
        has_b = any((target_b / f).exists() for f in files)

        if has_a and has_b:
            in_both.append(tool)
            # Check if content differs for primary file
            for f in files:
                fa = target_a / f
                fb = target_b / f
                if fa.exists() and fb.exists():
                    try:
                        same = fa.read_text() == fb.read_text()
                        diff_note = "[green]identical[/]" if same else "[yellow]differs[/]"
                    except Exception:
                        diff_note = "[dim]binary[/]"
                    break
            else:
                diff_note = "[green]present[/]"
            table.add_row(tool, "[green]✓[/]", "[green]✓[/]", diff_note)
        elif has_a:
            only_in_a.append(tool)
            table.add_row(tool, "[green]✓[/]", "[dim]✗ missing[/]", "[yellow]only in A[/]")
        elif has_b:
            only_in_b.append(tool)
            table.add_row(tool, "[dim]✗ missing[/]", "[green]✓[/]", "[yellow]only in B[/]")
        else:
            table.add_row(tool, "[dim]—[/]", "[dim]—[/]", "[dim]neither[/]")

    console.print(table)

    # Summary
    console.print("\n[bold]Summary:[/]")
    console.print(f"  Both configured: [green]{len(in_both)}[/] tools")
    if only_in_a:
        console.print(f"  Only in A: [yellow]{', '.join(only_in_a)}[/]")
        console.print(f"    → Run in B: [cyan]vcsx update --tool {' --tool '.join(only_in_a)}[/]")
    if only_in_b:
        console.print(f"  Only in B: [yellow]{', '.join(only_in_b)}[/]")
        console.print(f"    → Run in A: [cyan]vcsx update --tool {' --tool '.join(only_in_b)}[/]")

    # Skill count comparison
    skills_a = (
        sum(1 for _ in (target_a / ".claude" / "skills").glob("*/SKILL.md"))
        if (target_a / ".claude" / "skills").exists()
        else 0
    )
    skills_b = (
        sum(1 for _ in (target_b / ".claude" / "skills").glob("*/SKILL.md"))
        if (target_b / ".claude" / "skills").exists()
        else 0
    )
    if skills_a or skills_b:
        console.print(f"\n  Claude Code skills: A=[cyan]{skills_a}[/] B=[cyan]{skills_b}[/]")


@main.command("search")
@click.argument("query")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--type", "-t", type=click.Choice(["skill", "hook", "agent", "all"]), default="all")
def search_configs(query, path, type):
    """Search inside AI config files for a keyword.

    Searches skills, hooks, agents and other config files for the given query.

    Examples:
        vcsx search deploy              # Find anything about deploy
        vcsx search pytest --type skill # Find pytest in skills only
        vcsx search "jwt" ~/my-project  # Search in specific project
    """
    import re

    target = Path(path).resolve()
    query_lower = query.lower()
    results = []

    search_paths = {
        "skill": [".claude/skills"],
        "hook": [".claude/hooks"],
        "agent": [".claude/agents"],
        "all": [
            ".claude/skills",
            ".claude/hooks",
            ".claude/agents",
            ".cursor/rules",
            ".windsurf/rules",
            ".github/instructions",
        ],
    }

    dirs_to_search = search_paths.get(type, search_paths["all"])

    for dir_rel in dirs_to_search:
        search_dir = target / dir_rel
        if not search_dir.exists():
            continue
        for file_path in sorted(search_dir.rglob("*")):
            if file_path.is_file() and file_path.suffix in (
                ".md",
                ".sh",
                ".yaml",
                ".json",
                ".toml",
                ".mdc",
            ):
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    if query_lower in content.lower():
                        # Find matching lines
                        matching_lines = [
                            (i + 1, line.strip())
                            for i, line in enumerate(content.splitlines())
                            if query_lower in line.lower()
                        ]
                        results.append(
                            {
                                "file": str(file_path.relative_to(target)),
                                "matches": matching_lines[:3],  # max 3 lines per file
                            }
                        )
                except Exception:
                    pass

    if not results:
        console.print(f"\n[yellow]No results for '[bold]{query}[/bold]' in {target}[/]")
        return

    console.print(f"\n[bold]Search:[/] '{query}' — {len(results)} file(s)\n")

    for r in results:
        console.print(f"  [cyan]{r['file']}[/]")
        for lineno, line in r["matches"]:
            # Highlight the query in the line
            highlighted = re.sub(
                re.escape(query), f"[bold yellow]{query}[/bold yellow]", line, flags=re.IGNORECASE
            )
            console.print(f"    [dim]{lineno}:[/] {highlighted}")
        console.print()


@main.command("changelog")
@click.option("--version", "-v", default=None, help="Show changelog for specific version")
@click.option("--latest", "-l", is_flag=True, default=False, help="Show only the latest version")
def show_changelog(version, latest):
    """Show the changelog for vcsx.

    Examples:
        vcsx changelog           # Full changelog
        vcsx changelog --latest  # Latest version only
        vcsx changelog -v 4.0.0  # Specific version
    """
    import re

    # Find CHANGELOG.md relative to the installed package
    import vcsx

    package_dir = Path(vcsx.__file__).parent.parent.parent
    changelog_path = package_dir / "CHANGELOG.md"

    if not changelog_path.exists():
        # Try common locations
        for candidate in [
            Path("CHANGELOG.md"),
            Path(__file__).parent.parent.parent / "CHANGELOG.md",
        ]:
            if candidate.exists():
                changelog_path = candidate
                break

    if not changelog_path.exists():
        console.print("[yellow]CHANGELOG.md not found.[/]")
        console.print("See: https://github.com/barancanercan/vcsx/releases")
        return

    content = changelog_path.read_text(encoding="utf-8")
    sections = re.split(r"\n## \[", content)

    if latest:
        # Show only first section
        for section in sections[1:]:
            if section.strip():
                console.print(f"## [{section[:200]}")
                return
        return

    if version:
        for section in sections[1:]:
            if section.startswith(version):
                console.print(f"## [{section}")
                return
        console.print(f"[yellow]Version {version} not found in changelog.[/]")
        return

    # Show full changelog (last 3 versions)
    shown = 0
    for section in sections[1:]:
        if shown >= 3:
            break
        if section.strip() and not section.startswith("Unreleased"):
            console.print(f"\n## [{section[:500]}")
            shown += 1


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


@main.command("status")
@click.argument("path", default=".", type=click.Path(exists=True))
def project_status(path):
    """Show a one-page AI setup status for a project.

    Combines doctor + check + stats into a single clean overview.

    Examples:
        vcsx status             # Current directory
        vcsx status ~/my-proj   # Specific project
    """
    target = Path(path).resolve()
    console.print(f"\n[bold]vcsx status[/] — {target.name}\n")

    # Tool detection
    tool_files = {
        "claude-code": "CLAUDE.md",
        "cursor": ".cursorrules",
        "windsurf": ".windsurfrules",
        "gemini": "GEMINI.md",
        "agents-md": "AGENTS.md",
        "aider": ".aider.conf.yaml",
        "copilot": ".github/copilot-instructions.md",
        "zed": ".zed/settings.json",
        "bolt": ".bolt/workspace.json",
        "codex": ".openai/instructions.md",
    }
    configured = [t for t, f in tool_files.items() if (target / f).exists()]

    # Score calculation (reuse check logic)
    total_score = 0
    tool_scores = {}
    check_data = {
        "claude-code": {
            "files": ["CLAUDE.md", ".claudeignore", ".claude/settings.json"],
            "quality": [".claude/agents", ".claude/skills"],
        },
        "cursor": {"files": [".cursorrules"], "quality": [".cursor/rules"]},
        "windsurf": {"files": [".windsurfrules"], "quality": [".windsurf/rules"]},
        "gemini": {"files": ["GEMINI.md"], "quality": []},
        "agents-md": {"files": ["AGENTS.md"], "quality": []},
    }
    for tool, cfg in check_data.items():
        present = sum(1 for f in cfg["files"] if (target / f).exists())
        quality = sum(1 for f in cfg["quality"] if (target / f).exists())
        score = present * 2 + quality
        max_score = len(cfg["files"]) * 2 + len(cfg["quality"])
        if present > 0 and max_score > 0:
            tool_scores[tool] = int(score / max_score * 100)
            total_score += tool_scores[tool]

    overall = int(total_score / len(tool_scores)) if tool_scores else 0

    # Skill/hook/agent counts
    skills = (
        sum(1 for _ in (target / ".claude" / "skills").glob("*/SKILL.md"))
        if (target / ".claude" / "skills").exists()
        else 0
    )
    hooks = (
        sum(1 for _ in (target / ".claude" / "hooks").glob("*.sh"))
        if (target / ".claude" / "hooks").exists()
        else 0
    )
    agents = (
        sum(1 for _ in (target / ".claude" / "agents").glob("*.md"))
        if (target / ".claude" / "agents").exists()
        else 0
    )
    rules = (
        sum(1 for _ in (target / ".cursor" / "rules").glob("*.mdc"))
        if (target / ".cursor" / "rules").exists()
        else 0
    )
    rules += (
        sum(1 for _ in (target / ".windsurf" / "rules").glob("*.md"))
        if (target / ".windsurf" / "rules").exists()
        else 0
    )

    # Print overview
    score_color = "green" if overall >= 80 else "yellow" if overall >= 50 else "red"
    console.print(
        f"[bold]Quality Score:[/] [{score_color}]{overall}%[/]  |  Tools: {len(configured)}/{len(tool_files)}"
    )
    console.print()

    if configured:
        console.print(f"[bold]Configured:[/] {', '.join(f'[cyan]{t}[/]' for t in configured)}")
    else:
        console.print("[yellow]No AI tool configs found. Run vcsx init to get started.[/]")
        return

    # Stats
    if skills or hooks or agents or rules:
        console.print()
        console.print("[bold]Contents:[/]")
        if skills:
            console.print(f"  Skills (Claude Code): {skills}")
        if hooks:
            console.print(f"  Hooks (Claude Code): {hooks}")
        if agents:
            console.print(f"  Agents (Claude Code): {agents}")
        if rules:
            console.print(f"  Scoped rules (Cursor/Windsurf): {rules}")

    # Issues
    issues = []
    if "claude-code" in configured and not (target / ".claudeignore").exists():
        issues.append("Missing .claudeignore → run: vcsx update --auto")
    if configured and "agents-md" not in configured:
        issues.append("No AGENTS.md → run: vcsx update --tool agents-md")
    if (target / ".windsurfrules").exists() and not (target / ".windsurf" / "rules").exists():
        issues.append("Windsurf: old format → run: vcsx migrate windsurf")
    if (target / ".cursorrules").exists() and not (target / ".cursor" / "rules").exists():
        issues.append("Cursor: old format → run: vcsx migrate cursor")

    if issues:
        console.print()
        console.print("[bold yellow]Suggestions:[/]")
        for i in issues:
            console.print(f"  • {i}")
    else:
        console.print()
        console.print("[bold green]✓ Everything looks good![/]")

    console.print()
    console.print("[dim]Run vcsx audit for full analysis  |  vcsx check --json for CI[/]")


@main.command("gemini-global")
@click.option(
    "--lang",
    "-l",
    type=click.Choice(["python", "typescript", "javascript", "go", "rust"]),
    default="python",
    help="Primary language for global config",
)
@click.option("--force", is_flag=True, help="Overwrite existing global config")
def gemini_global(lang, force):
    """Create ~/.gemini/GEMINI.md — global Gemini CLI config.

    This file is loaded by Gemini CLI for ALL projects.
    Use it to set your preferred conventions, style, and tools.

    Examples:
        vcsx gemini-global --lang python
        vcsx gemini-global --lang typescript --force
    """
    from vcsx.core.context import ProjectContext
    from vcsx.core.inference import infer_formatter, infer_linter, infer_test_framework
    from vcsx.generators.gemini import GeminiGenerator

    gemini_dir = Path.home() / ".gemini"
    gemini_dir.mkdir(exist_ok=True)
    target = gemini_dir / "GEMINI.md"

    if target.exists() and not force:
        console.print("[yellow]~/.gemini/GEMINI.md already exists.[/]")
        console.print("Use [cyan]--force[/] to overwrite.")
        return

    ctx = ProjectContext(
        project_name="Global",
        language=lang,
        tech_stack=lang,
        description="Global Gemini CLI configuration — applies to all projects",
        project_type="general",
        test_framework=infer_test_framework(lang),
        formatter=infer_formatter(lang),
        linter=infer_linter(lang),
        lang="en",
    )

    gen = GeminiGenerator()
    gen.generate_config(ctx, str(gemini_dir))

    # Rename GEMINI.md (generated in gemini_dir)
    # Actually the generator writes to output_dir/GEMINI.md
    # which is already ~/.gemini/GEMINI.md ✓

    console.print(f"\n[green]✓ Created:[/] {target}")
    console.print(f"[dim]Language:[/] {lang}")
    console.print("\nGemini CLI will now load this config for all projects.")
    console.print("Override per-project with a local GEMINI.md in your project root.")


@main.command("generate")
@click.argument("tool", type=click.Choice(ALL_TOOLS))
@click.argument("file_type", required=False)
@click.option(
    "--project-name",
    "-n",
    default="my-project",
    help="Project name for the generated file",
)
@click.option(
    "--lang",
    "-l",
    type=click.Choice(["python", "typescript", "javascript", "go", "rust"]),
    default="python",
    help="Primary language",
)
@click.option(
    "--type",
    "-t",
    "project_type",
    type=click.Choice(["web", "api", "cli", "library", "data-pipeline", "ml-model"]),
    default="api",
    help="Project type",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=".",
    help="Output directory",
)
@click.option(
    "--from-project",
    "-p",
    type=click.Path(exists=True),
    default=None,
    help="Auto-detect context from an existing project directory",
)
def generate_file(tool, file_type, project_name, lang, project_type, output_dir, from_project):
    """Generate a single AI config file without the full wizard.

    Useful for quickly adding a specific config to an existing project
    or previewing what vcsx would generate.

    \b
    Examples:
        vcsx generate claude-code           # Generate full Claude Code setup
        vcsx generate gemini -n my-api      # GEMINI.md for my-api
        vcsx generate agents-md --lang go   # AGENTS.md for a Go project
        vcsx generate cursor --type web     # Cursor rules for a web project
    """
    from vcsx.core.context import ProjectContext
    from vcsx.core.inference import infer_formatter, infer_linter, infer_test_framework

    # Auto-detect from existing project if --from-project given
    if from_project:
        from vcsx.core.scanner import scan_project

        detected = scan_project(from_project)
        lang = detected.get("language", lang) or lang
        project_type = detected.get("project_type", project_type) or project_type
        project_name = detected.get("project_name", project_name) or project_name
        console.print(f"[cyan]Auto-detected from {from_project}:[/] {lang} / {project_type}")

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

    target = Path(output_dir).resolve()
    gen = get_generator(tool)

    console.print(f"\n[bold]vcsx generate {tool}[/] → {target}\n")

    with console.status(f"Generating {tool} config..."):
        gen.generate_all(ctx, str(target))

    # Show what was created
    table = Table(title=f"{tool} — Generated", border_style="green")
    table.add_column("File")
    table.add_column("Status")

    for f in gen.output_files:
        # Check if a file matching this pattern was created
        f_path = target / f.split("*")[0].rstrip("/")
        status = "[green]✓ Created[/]" if f_path.exists() else "[dim]Skipped[/]"
        table.add_row(f, status)

    console.print(table)
    console.print(f"\n[green]Done![/] Config files written to: {target}")


@main.command("validate")
@click.argument("path", default=".", type=click.Path(exists=True))
def validate_config(path):
    """Validate AI config files for best practices and common mistakes.

    Checks CLAUDE.md, GEMINI.md, AGENTS.md, .cursorrules etc. for:
    - File size (too large → context bloat)
    - Missing required sections
    - Common anti-patterns

    Examples:
        vcsx validate               # Validate current directory
        vcsx validate ~/my-project  # Validate specific project
    """
    target = Path(path).resolve()
    console.print(f"\n[bold]vcsx validate[/] — {target}\n")

    issues = []
    warnings = []
    info = []

    # === CLAUDE.md checks ===
    claude_md = target / "CLAUDE.md"
    if claude_md.exists():
        content = claude_md.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        line_count = len(lines)

        if line_count > 200:
            issues.append(
                f"CLAUDE.md is {line_count} lines (max recommended: 200). "
                "Large context files slow down AI responses and reduce quality."
            )
        elif line_count > 150:
            warnings.append(f"CLAUDE.md is {line_count} lines — consider trimming to < 150.")

        if "## Quick Commands" not in content and "## Commands" not in content:
            warnings.append(
                "CLAUDE.md: Missing 'Quick Commands' section. Add build/test/lint commands."
            )

        if "NEVER" not in content.upper() and "DO NOT" not in content.upper():
            info.append(
                "CLAUDE.md: No explicit prohibitions found. Consider adding forbidden actions."
            )

        if (
            "api_key" in content.lower()
            or "secret" in content.lower()
            and "never" not in content.lower()
        ):
            warnings.append(
                "CLAUDE.md: Contains 'api_key' or 'secret' — ensure it's a rule, not a leaked credential."
            )

        info.append(f"CLAUDE.md: {line_count} lines ✓")

    # === GEMINI.md checks ===
    gemini_md = target / "GEMINI.md"
    if gemini_md.exists():
        content = gemini_md.read_text(encoding="utf-8", errors="replace")
        lines = len(content.splitlines())
        if lines < 10:
            warnings.append(
                f"GEMINI.md is very short ({lines} lines). Gemini CLI benefits from rich context."
            )
        info.append(f"GEMINI.md: {lines} lines ✓")

    # === AGENTS.md checks ===
    agents_md = target / "AGENTS.md"
    if agents_md.exists():
        content = agents_md.read_text(encoding="utf-8", errors="replace")
        if "## Build & Test Commands" not in content and "```bash" not in content:
            warnings.append(
                "AGENTS.md: Missing commands block. Add build/test commands for AI agents."
            )
        if "## Forbidden" not in content and "## What NOT" not in content:
            info.append("AGENTS.md: Consider adding a 'Forbidden Actions' section.")
        info.append(f"AGENTS.md: {len(content.splitlines())} lines ✓")

    # === .aider.conf.yaml checks ===
    aider_conf = target / ".aider.conf.yaml"
    if aider_conf.exists():
        content = aider_conf.read_text(encoding="utf-8", errors="replace")
        # Check for common invalid keys
        invalid_keys = ["repo:", "tools:", "command:", "only:", "max-context-characters:"]
        found_invalid = [k for k in invalid_keys if k in content]
        if found_invalid:
            issues.append(
                f".aider.conf.yaml contains invalid keys: {', '.join(found_invalid)}. "
                "These are not valid Aider CLI flags. Run 'vcsx migrate aider' to fix."
            )
        else:
            info.append(".aider.conf.yaml: no invalid keys ✓")

    # === .cursorrules checks ===
    cursorrules = target / ".cursorrules"
    if cursorrules.exists():
        content = cursorrules.read_text(encoding="utf-8", errors="replace")
        cursor_rules_dir = target / ".cursor" / "rules"
        if not cursor_rules_dir.exists():
            info.append(
                ".cursorrules found but no .cursor/rules/ directory. "
                "Run 'vcsx migrate cursor' to add modern scoped rules."
            )

    # === .windsurfrules checks ===
    windsurfrules = target / ".windsurfrules"
    if windsurfrules.exists():
        windsurf_rules = target / ".windsurf" / "rules"
        if not windsurf_rules.exists():
            info.append(
                ".windsurfrules found but no .windsurf/rules/ directory. "
                "Run 'vcsx migrate windsurf' to add new format."
            )

    # === .env check ===
    for env_file in [".env", ".env.local"]:
        env_path = target / env_file
        if env_path.exists():
            try:
                content = env_path.read_text(encoding="utf-8", errors="replace")
                if any(kw in content.upper() for kw in ["API_KEY", "SECRET", "TOKEN", "PASSWORD"]):
                    issues.append(
                        f"SECURITY: {env_file} contains secrets. "
                        "Ensure it's in .gitignore and .claudeignore."
                    )
                    # Check .gitignore
                    gitignore = target / ".gitignore"
                    if gitignore.exists():
                        gi_content = gitignore.read_text()
                        if ".env" not in gi_content:
                            issues.append(".gitignore: .env not listed! Add it immediately.")
            except Exception:
                pass

    # === Summary ===
    if not issues and not warnings and not info:
        console.print("[dim]No AI config files found to validate.[/]")
        console.print("Run [cyan]vcsx init[/] to set up AI configs.")
        return

    if issues:
        console.print("[bold red]Issues (fix required):[/]")
        for issue in issues:
            console.print(f"  ✗ {issue}")
        console.print()

    if warnings:
        console.print("[bold yellow]Warnings:[/]")
        for w in warnings:
            console.print(f"  ⚠ {w}")
        console.print()

    if info:
        console.print("[bold green]Passed:[/]")
        for i in info:
            console.print(f"  ✓ {i}")
        console.print()

    total = len(issues) + len(warnings)
    if total == 0:
        console.print("[bold green]All checks passed![/]")
    elif issues:
        console.print(f"[bold red]{len(issues)} issue(s) found — fix required.[/]")
    else:
        console.print(f"[yellow]{len(warnings)} warning(s) found.[/] Consider addressing them.")


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
        console.print("\n[green]✓ Migrated![/] .windsurf/rules/ created.")
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
        console.print("\n[green]✓ Migrated![/] .cursor/rules/ created.")
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
        console.print("\n[green]✓ Claude Code config upgraded![/]")

    elif tool == "copilot":
        main_file = target / ".github" / "copilot-instructions.md"
        instructions_dir = target / ".github" / "instructions"

        if not main_file.exists():
            console.print(
                "[yellow]No .github/copilot-instructions.md found — nothing to migrate.[/]"
            )
            return

        if instructions_dir.exists():
            console.print("[green]✓ Scoped instructions already exist.[/]")
            return

        console.print("Will create: .github/instructions/")
        console.print("  • code-style.instructions.md")
        console.print("  • testing.instructions.md")
        console.print("  • security.instructions.md")

        if dry_run:
            console.print("\n[dim]Dry run — no files written.[/]")
            return

        from vcsx.generators.copilot import CopilotGenerator

        CopilotGenerator()._generate_scoped_instructions(ctx, str(target))
        console.print("\n[green]✓ Copilot scoped instructions created![/]")


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

    env_var = "_VCSX_COMPLETE"
    scripts = {
        "bash": f'eval "$({env_var}=bash_source vcsx)"',
        "zsh": f'eval "$({env_var}=zsh_source vcsx)"',
        "fish": f"eval (env {env_var}=fish_source vcsx)",
        "powershell": f"Invoke-Expression (& vcsx --{env_var}=powershell_source)",
    }

    setup_instructions = {
        "bash": '# Add to ~/.bashrc:\neval "$(vcsx completion bash)"',
        "zsh": '# Add to ~/.zshrc:\neval "$(vcsx completion zsh)"',
        "fish": "# Add to ~/.config/fish/completions/vcsx.fish:\nvcsx completion fish | source",
        "powershell": "# Add to $PROFILE:\nInvoke-Expression (& vcsx completion powershell)",
    }

    console.print(f"# vcsx shell completion for {shell}")
    console.print(setup_instructions[shell])
    console.print("\n# Auto-generated (requires click-completion or Click 8.x):")
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

    registry = get_template_registry()
    template = registry.get(template_name)

    if not template:
        console.print(f"Template not found: {template_name}")
        available = [t.metadata.name for t in registry.list_all()]
        console.print(f"Available: {', '.join(available)}")
        return

    console.print(f"Template '{template_name}' installed")
    console.print(f"Files: {', '.join(template.list_files())}")
