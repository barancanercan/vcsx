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

    # --- Tech-stack-based suggestions when project has no AI configs yet ---
    tech_suggestions: list[str] = []
    if not present and not tools_to_add:
        from vcsx.core.scanner import scan_project

        stack = scan_project(str(target))
        lang = (stack.get("language") or "").lower()
        framework = (stack.get("framework") or "").lower()
        project_type = (stack.get("project_type") or "web").lower()

        # Suggest claude-code as primary (universal, most powerful)
        tech_suggestions.append("claude-code")

        # Suggest cursor for frontend-heavy or TypeScript projects
        if lang in ("typescript", "javascript") or project_type in ("web", "frontend"):
            tech_suggestions.append("cursor")

        # Suggest agents-md as universal standard
        tech_suggestions.append("agents-md")

        # Suggest windsurf for mobile projects (Flutter/Dart, Swift)
        if lang in ("dart", "swift", "kotlin") or project_type == "mobile":
            tech_suggestions.append("windsurf")

        # Suggest aider for Python/Go/Rust API projects (terminal-friendly)
        if lang in ("python", "go", "rust") and project_type in ("api", "cli", "library"):
            tech_suggestions.append("aider")

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for s in tech_suggestions:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        tech_suggestions = unique

        if tech_suggestions and stack.get("language"):
            console.print(
                f"[cyan]Tech stack detected:[/] {lang}"
                + (f" / {framework}" if framework else "")
                + f" / {project_type}"
            )
            console.print(
                f"[yellow]💡 Suggested tools:[/] {', '.join(tech_suggestions)}\n"
                f"   Run [cyan]vcsx update --auto[/] to apply all, or "
                f"[cyan]vcsx update --tool <name>[/] for specific ones.\n"
            )

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

    if not tools_to_add and not missing_files and not tech_suggestions:
        console.print("\n[green]✓ Everything looks up to date![/]")
        return

    if not tools_to_add and not missing_files and tech_suggestions:
        # No existing configs and no explicit tool — use suggestions
        if not auto:
            console.print(
                "\n[dim]No AI configs found. Use [cyan]--auto[/] to apply suggestions"
                " or [cyan]--tool <name>[/] for a specific tool.[/]"
            )
            return
        # --auto with fresh project: apply all suggestions
        tools_to_add = tech_suggestions

    if dry_run:
        console.print("\n[dim]Dry run — no files written.[/]")
        if tools_to_add:
            console.print(f"Would add configs for: {', '.join(tools_to_add)}")
        elif tech_suggestions:
            console.print(f"Would add configs for (suggested): {', '.join(tech_suggestions)}")
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


def _show_installed_ai_tools() -> None:
    """Check which AI coding CLIs are installed on the system."""
    # (cli_command, display_name, install_hint)
    ai_cli_tools = [
        ("claude", "Claude Code", "npm install -g @anthropic-ai/claude-code"),
        ("cursor", "Cursor", "https://cursor.com"),
        ("windsurf", "Windsurf", "https://windsurf.com"),
        ("aider", "Aider", "pip install aider-install && aider-install"),
        ("gemini", "Gemini CLI", "npm install -g @google/gemini-cli"),
        ("codex", "OpenAI Codex", "npm install -g @openai/codex"),
        ("gh", "GitHub CLI (Copilot)", "https://cli.github.com"),
        ("continue", "Continue.dev", "VS Code extension"),
    ]

    found = []
    missing = []

    for cmd, name, hint in ai_cli_tools:
        path = shutil.which(cmd)
        if path:
            found.append((name, path))
        else:
            missing.append((name, hint))

    if not found and not missing:
        return

    console.print("\n[bold]AI CLI Tools (system-wide):[/]")
    tools_table = Table(show_header=False, border_style="dim")
    tools_table.add_column("Tool")
    tools_table.add_column("Status")

    for name, path in found:
        # Shorten the path for display
        short_path = path.replace(str(Path.home()), "~") if str(Path.home()) in path else path
        tools_table.add_row(name, f"[green]✓[/] {short_path}")

    for name, hint in missing[:4]:  # Show first 4 missing only
        tools_table.add_row(name, f"[dim]✗ not installed[/]  [dim]{hint}[/]")

    console.print(tools_table)

    if found:
        console.print(f"\n[green]{len(found)} AI CLI tool(s) installed.[/]")
    if missing:
        console.print(
            f"[dim]{len(missing)} not installed — install to use those AI tools locally.[/]"
        )


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

    # --- AI CLI Tools installed on system ---
    _show_installed_ai_tools()

    # Platform info
    console.print(f"\n[dim]Platform:[/] {platform.system()} {platform.machine()}")
    console.print(f"[dim]Python:[/] {platform.python_version()}")


@main.command("check")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
@click.option(
    "--min-score",
    default=0,
    type=int,
    help="Exit with code 1 if score is below this threshold (for CI)",
)
def check_project(path, output_json, min_score):
    """Analyze a project's AI config quality and give a score.

    Checks for: config files present, quality indicators, best practices.
    Use --min-score for CI pipelines (exits 1 if score below threshold).

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

    # CI exit code support
    if min_score > 0 and overall_pct < min_score:
        console.print(f"\n[red]✗ Score {overall_pct}% is below minimum {min_score}%[/]")
        raise SystemExit(1)


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
@click.option(
    "--format",
    "-f",
    "fmt",
    type=click.Choice(["zip", "json"], case_sensitive=False),
    default="zip",
    help="Output format: zip (default) or json manifest",
)
def export_configs(path, output, include_all, fmt):
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

    # JSON format
    if fmt == "json":
        import json

        manifest = {
            "project": project_name,
            "path": str(target),
            "vcsx_version": __version__,
            "file_count": len(collected),
            "files": [],
        }
        for file_path, rel in collected:
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                content = None
            manifest["files"].append(
                {
                    "path": rel,
                    "size_bytes": file_path.stat().st_size,
                    "content": content,
                }
            )

        if output:
            out_path = Path(output)
            out_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            console.print(f"\n[green]✓ Exported {len(collected)} files → {out_path}[/]")
        else:
            console.print(json.dumps(manifest, indent=2, ensure_ascii=False))
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

    # --- Git commit analysis ---
    _show_git_stats(target)


def _show_git_stats(target: Path) -> None:
    """Show git commit statistics for the project."""
    import subprocess

    git_dir = target / ".git"
    if not git_dir.exists():
        return  # Not a git repo — skip silently

    try:
        # Total commit count
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=str(target),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return
        total_commits = int(result.stdout.strip())

        # Last 30 days commit count
        result_30d = subprocess.run(
            ["git", "log", "--oneline", "--after=30 days ago", "--format=%s"],
            cwd=str(target),
            capture_output=True,
            text=True,
            timeout=5,
        )
        recent_commits_raw = (
            result_30d.stdout.strip().splitlines() if result_30d.returncode == 0 else []
        )
        recent_count = len(recent_commits_raw)

        # Commit type breakdown (conventional commits)
        type_counts: dict[str, int] = {}
        for msg in recent_commits_raw:
            msg_lower = msg.lower()
            for ctype in ("feat", "fix", "refactor", "test", "docs", "chore", "perf", "ci"):
                if msg_lower.startswith(f"{ctype}:") or msg_lower.startswith(f"{ctype}("):
                    type_counts[ctype] = type_counts.get(ctype, 0) + 1
                    break
            else:
                type_counts["other"] = type_counts.get("other", 0) + 1

        # First commit date
        result_first = subprocess.run(
            ["git", "log", "--reverse", "--format=%ar", "--max-count=1"],
            cwd=str(target),
            capture_output=True,
            text=True,
            timeout=5,
        )
        first_commit = result_first.stdout.strip() if result_first.returncode == 0 else "unknown"

        # Latest commit
        result_last = subprocess.run(
            ["git", "log", "-1", "--format=%ar — %s"],
            cwd=str(target),
            capture_output=True,
            text=True,
            timeout=5,
        )
        last_commit = result_last.stdout.strip() if result_last.returncode == 0 else "unknown"

        # Display
        console.print("\n[bold]Git Activity:[/]")
        git_table = Table(border_style="dim", show_header=False)
        git_table.add_column("Metric", style="dim")
        git_table.add_column("Value", style="cyan")

        git_table.add_row("Total commits", str(total_commits))
        git_table.add_row("Last 30 days", str(recent_count))
        git_table.add_row("First commit", first_commit)
        git_table.add_row(
            "Latest commit", last_commit[:80] if len(last_commit) > 80 else last_commit
        )

        if type_counts and recent_count > 0:
            type_summary = ", ".join(
                f"{k}:{v}"
                for k, v in sorted(type_counts.items(), key=lambda x: -x[1])
                if k != "other"
            )
            if type_summary:
                git_table.add_row("Commit types (30d)", type_summary)

        console.print(git_table)

    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass  # Git not available or repo issue — skip silently


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
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
def audit_project(path, auto_fix, output_json):
    """Run a comprehensive audit of all AI configs in a project.

    Combines check + validate + stats into one actionable report.
    With --fix, auto-applies safe fixes.

    Examples:
        vcsx audit                  # Audit current project
        vcsx audit ~/my-project     # Audit specific project
        vcsx audit --fix            # Audit and auto-fix safe issues
    """
    target = Path(path).resolve()
    if not output_json:
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
        if output_json:
            import json as json_mod

            console.print(
                json_mod.dumps(
                    {
                        "status": "pass",
                        "issues": [],
                        "warnings": [],
                        "passed": [],
                        "total_issues": 0,
                        "total_warnings": 0,
                        "path": str(target),
                    }
                )
            )
        else:
            console.print("[yellow]No AI configs found. Run vcsx init to get started.[/]")
        return

    if not output_json:
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

    if output_json:
        import json as json_mod

        result = {
            "path": str(target),
            "issues": issues,
            "warnings": warnings,
            "passed": [],
            "total_issues": len(issues),
            "total_warnings": len(warnings),
            "status": "pass" if total == 0 else ("fail" if issues else "warn"),
        }
        console.print(json_mod.dumps(result, indent=2))
        return

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


@main.command("version")
def show_version():
    """Show vcsx version with recent changelog entries.

    Examples:
        vcsx version  # Show version + last 3 changelog entries
    """
    import re

    console.print(f"\n[bold cyan]vcsx[/] [bold]{__version__}[/]\n")

    # Find CHANGELOG.md
    import vcsx as _vcsx_mod

    changelog_path = Path(_vcsx_mod.__file__).parent.parent.parent / "CHANGELOG.md"
    if not changelog_path.exists():
        for candidate in [
            Path("CHANGELOG.md"),
            Path(__file__).parent.parent.parent / "CHANGELOG.md",
        ]:
            if candidate.exists():
                changelog_path = candidate
                break

    if not changelog_path.exists():
        console.print(
            "[dim]Changelog not found. See: https://github.com/barancanercan/vcsx/releases[/]"
        )
        return

    content = changelog_path.read_text(encoding="utf-8")
    sections = re.split(r"\n## \[", content)

    console.print("[bold]Recent Changes:[/]")
    shown = 0
    for section in sections[1:]:
        if shown >= 3:
            break
        if section.strip() and not section.startswith("Unreleased"):
            # Header line only + first 3 bullet points
            lines = section.strip().splitlines()
            version_line = f"[cyan]## [{lines[0]}[/]"
            console.print(f"\n{version_line}")
            bullets = [ln for ln in lines[1:] if ln.strip().startswith("-")][:3]
            for b in bullets:  # noqa: E741 — `b` is fine here
                console.print(f"  {b.strip()}")
            shown += 1

    console.print("\n[dim]Full changelog: vcsx changelog[/]")


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


@main.command("presets")
@click.argument("query", required=False)
def list_presets(query):
    """List available project presets (alias for vcsx templates).

    Examples:
        vcsx presets             # List all 10 presets
        vcsx presets python      # Search python presets
    """
    results = search_templates(query) if query else list_official_templates()

    if not results:
        console.print("No presets found")
        return

    table = Table(
        title=f"{'Search: ' + query if query else 'Available Presets (10)'}", border_style="cyan"
    )
    table.add_column("Preset", style="cyan")
    table.add_column("Description")
    table.add_column("Language", style="dim")
    table.add_column("Type", style="dim")

    for t in results:
        lang = t.tech_stack.get("language", "—")
        ptype = t.tech_stack.get("type", "—")
        table.add_row(t.name, t.description, lang, ptype)

    console.print(table)
    console.print("\n[dim]Use:[/] vcsx new my-project --preset <name>")


@main.command("prompt")
@click.argument("task", required=False)
@click.option(
    "--lang",
    "-l",
    default=None,
    help="Primary language (auto-detected from current dir if omitted)",
)
@click.option(
    "--framework",
    "-f",
    default=None,
    help="Framework (e.g. fastapi, nextjs, gin)",
)
@click.option(
    "--type",
    "-t",
    "prompt_type",
    type=click.Choice(["feature", "bugfix", "refactor", "review", "test", "docs", "explain"]),
    default="feature",
    help="Type of prompt to generate",
)
@click.option(
    "--copy",
    is_flag=True,
    help="Copy to clipboard (requires pyperclip)",
)
def generate_prompt(task, lang, framework, prompt_type, copy):
    """Generate a structured AI prompt for a coding task.

    Produces a ready-to-paste prompt with project context, task description,
    and explicit instructions — reducing back-and-forth with the AI.

    \b
    Examples:
        vcsx prompt "add JWT authentication"
        vcsx prompt "fix race condition in worker pool" --type bugfix --lang go
        vcsx prompt "refactor payment module" --type refactor --lang python
        vcsx prompt "explain the auth middleware" --type explain
        vcsx prompt "add tests for UserService" --type test --lang typescript
    """
    from vcsx.core.scanner import scan_project

    # Auto-detect project context
    detected = scan_project(".")
    if not lang:
        lang = detected.get("language", "python") or "python"
    if not framework:
        framework = detected.get("framework", "") or ""
    project_name = detected.get("project_name", "this project")
    project_type = detected.get("project_type", "application")
    test_fw = detected.get("test_framework", "") or ""

    if not task:
        from rich.prompt import Prompt
        task = Prompt.ask(f"What do you want to {prompt_type}")

    prompt_content = _build_prompt(task, prompt_type, lang, framework, project_name, project_type, test_fw)

    console.print(f"\n[bold cyan]Generated {prompt_type} prompt:[/]\n")
    console.print(f"[dim]{'─' * 60}[/]")
    console.print(prompt_content)
    console.print(f"[dim]{'─' * 60}[/]")

    if copy:
        try:
            import pyperclip
            pyperclip.copy(prompt_content)
            console.print("\n[green]✓ Copied to clipboard![/]")
        except ImportError:
            console.print("\n[yellow]Install pyperclip to use --copy: pip install pyperclip[/]")

    console.print(f"\n[dim]Prompt type: {prompt_type} | Language: {lang}{f' / {framework}' if framework else ''}[/]")


def _build_prompt(
    task: str,
    prompt_type: str,
    lang: str,
    framework: str,
    project_name: str,
    project_type: str,
    test_fw: str,
) -> str:
    """Build a structured AI coding prompt."""
    ctx_line = f"**Language:** {lang}" + (f" / **Framework:** {framework}" if framework else "")

    if prompt_type == "feature":
        return f"""# Task: Add New Feature

## Context
**Project:** {project_name} ({project_type})
{ctx_line}

## Feature Request
{task}

## Requirements
Before implementing, please:
1. Read the relevant existing code to understand current patterns
2. Propose an implementation plan before writing any code
3. Follow existing code style and conventions

## Implementation Guidelines
- Keep the change focused — only what's needed for this feature
- Write tests for the new functionality using {test_fw or "the existing test framework"}
- Handle error cases, not just the happy path
- No hardcoded values — use constants or config
- Format code before committing

## Definition of Done
- [ ] Feature works as described
- [ ] Tests pass
- [ ] No linting errors
- [ ] Code follows existing patterns
"""

    elif prompt_type == "bugfix":
        return f"""# Task: Fix Bug

## Context
**Project:** {project_name}
{ctx_line}

## Bug Description
{task}

## Debug Process
Please follow these steps:
1. Reproduce the bug — understand exactly when it occurs
2. Identify the root cause (not just the symptom)
3. Propose the fix before implementing it
4. Apply the minimal fix
5. Verify the fix with a test

## Constraints
- Fix the ROOT CAUSE, not the symptom
- Minimal diff — don't refactor while fixing
- Add a regression test if one doesn't exist
- Run {test_fw or "the test suite"} after fixing to ensure nothing broke
"""

    elif prompt_type == "refactor":
        return f"""# Task: Refactor

## Context
**Project:** {project_name}
{ctx_line}

## Refactoring Goal
{task}

## Rules
1. **Behavior must not change** — the external API/output stays identical
2. Run {test_fw or "the test suite"} before starting to establish a baseline
3. Make one change at a time — rename, then extract, then move
4. Run tests after EACH change — stop immediately if tests fail
5. Commit at each green state

## What to Improve
- Reduce complexity (functions > 30 lines, nesting > 3 levels)
- Remove duplication
- Improve naming
- Extract reusable utilities

## What NOT to Do
- Don't add new functionality
- Don't change external interfaces
- Don't reformat in the same commit as logic changes
"""

    elif prompt_type == "review":
        return f"""# Task: Code Review

## Context
**Project:** {project_name}
{ctx_line}

## Review Target
{task}

## Review Checklist

### 🔴 Blocking (must fix)
- Hardcoded secrets or credentials
- Security vulnerabilities (injection, XSS, path traversal)
- Broken or missing tests
- Logic errors

### 🟡 Important (should fix)
- Missing error handling
- Missing edge cases
- Performance concerns
- Breaking API changes without documentation

### 🟢 Suggestions
- Style improvements
- Naming clarity
- Code organization

## Output Format
For each issue: `[SEVERITY] file:line — description → suggested fix`
End with: `Verdict: APPROVE / REQUEST_CHANGES`
"""

    elif prompt_type == "test":
        return f"""# Task: Write Tests

## Context
**Project:** {project_name}
{ctx_line}
**Test Framework:** {test_fw or "auto-detect"}

## What to Test
{task}

## Test Requirements
- Use AAA pattern: Arrange → Act → Assert
- Test naming: `test_<function>_<scenario>_<expected_outcome>`
- Mock ALL external dependencies (DB, HTTP, filesystem, time)
- Cover:
  - [ ] Happy path
  - [ ] Edge cases (empty, null, boundary values)
  - [ ] Error cases (invalid input, network failure, etc.)
- Tests must be independent — no shared mutable state

## Don't Test
- Implementation details (internal variable names)
- Third-party library behavior
- Trivial getters/setters
"""

    elif prompt_type == "docs":
        return f"""# Task: Write Documentation

## Context
**Project:** {project_name}
{ctx_line}

## Documentation Target
{task}

## Documentation Standards
- Explain WHAT the code does, not HOW it does it
- Include: purpose, parameters, return value, errors, example
- Use the language's standard doc format
- Examples must be accurate and runnable
- No placeholder text ("TODO: document this")

## Quality Bar
A good doc answers: "What does this do? How do I use it? What can go wrong?"
"""

    elif prompt_type == "explain":
        return f"""# Task: Explain Code

## Context
**Project:** {project_name}
{ctx_line}

## What to Explain
{task}

## Explanation Format
Please provide:
1. **High-level summary** (1-2 sentences: what does it do and why?)
2. **Key components** (bullet list of important parts)
3. **Data flow** (how does data move through it?)
4. **Dependencies** (what does it depend on / what depends on it?)
5. **Non-obvious parts** (what would trip up a new developer?)

Be concise — aim for understanding, not exhaustiveness.
"""

    return f"# {prompt_type.title()} Task\n\n{task}\n\nLanguage: {lang}\n"


@main.command("langs")
def list_languages():
    """List all supported languages and their detected properties.

    Shows language detection keywords, test framework, formatter, linter.
    """
    from vcsx.core.inference import STACK_MAP

    table = Table(title="Supported Languages (11)", border_style="cyan")
    table.add_column("Language", style="cyan")
    table.add_column("Test Framework")
    table.add_column("Formatter")
    table.add_column("Linter")
    table.add_column("Detect Keywords", style="dim")

    for lang, cfg in STACK_MAP.items():
        keywords = ", ".join(cfg["keywords"][:3]) + ("..." if len(cfg["keywords"]) > 3 else "")
        table.add_row(
            lang,
            cfg.get("test_framework", "—"),
            cfg.get("formatter", "—"),
            cfg.get("linter", "—"),
            keywords,
        )

    console.print(table)
    console.print("\n[dim]Detection: vcsx init --scan auto-detects from project files[/]")


@main.command("quality")
@click.argument("path", default=".", type=click.Path(exists=True))
def quality_report(path):
    """Show a comprehensive quality report for a project's AI setup.

    Combines scanner detection, tool coverage, and actionable suggestions
    into a single report.

    Examples:
        vcsx quality              # Current directory
        vcsx quality ~/my-proj    # Specific project
    """
    from vcsx.core.scanner import format_scan_summary, scan_project

    target = Path(path).resolve()
    console.print(f"\n[bold]vcsx quality[/] — {target.name}\n")
    console.print("=" * 50)

    # 1. Tech stack detection
    scan = scan_project(str(target))
    console.print("\n[bold]Project Stack[/]")
    console.print(f"  {format_scan_summary(scan)}")
    if scan.get("has_docker"):
        console.print("  Docker: ✓")
    if scan.get("has_ci"):
        console.print("  CI/CD: ✓")

    # 2. AI tools configured
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
    missing = [t for t, f in tool_files.items() if t not in configured]

    console.print(f"\n[bold]AI Tools ({len(configured)}/10)[/]")
    for t in configured:
        console.print(f"  [green]✓[/] {t}")
    if missing[:3]:
        console.print(
            f"  [dim]Not configured: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}[/]"
        )

    # 3. Claude Code stats
    if "claude-code" in configured:
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
        console.print("\n[bold]Claude Code[/]")
        console.print(f"  Skills: {skills}  |  Hooks: {hooks}  |  Agents: {agents}")
        if not (target / ".claudeignore").exists():
            console.print("  [yellow]⚠ Missing .claudeignore[/]")

    # 4. Quick wins
    quick_wins = []
    if configured and "agents-md" not in configured:
        quick_wins.append("vcsx update --tool agents-md  [dim](universal standard)[/]")
    if (target / ".windsurfrules").exists() and not (target / ".windsurf" / "rules").exists():
        quick_wins.append("vcsx migrate windsurf  [dim](upgrade to v2 format)[/]")
    if (target / ".cursorrules").exists() and not (target / ".cursor" / "rules").exists():
        quick_wins.append("vcsx migrate cursor  [dim](upgrade to .mdc format)[/]")
    if "claude-code" in configured and not (target / ".claudeignore").exists():
        quick_wins.append("vcsx update --auto  [dim](generate .claudeignore)[/]")

    if quick_wins:
        console.print("\n[bold]Quick Wins[/]")
        for qw in quick_wins[:4]:
            console.print(f"  → {qw}")

    console.print()
    console.print("[dim]For details: vcsx audit | vcsx check --json | vcsx stats[/]\n")


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


# ─── Scaffold file templates ──────────────────────────────────────────────────

_SCAFFOLD_FILES = {
    "gitignore": "Generate a language-aware .gitignore file",
    "dockerfile": "Generate a Dockerfile for the project",
    "makefile": "Generate a Makefile with common dev tasks",
    "dockercompose": "Generate a docker-compose.yml file",
    "editorconfig": "Generate an .editorconfig file",
    "nvmrc": "Generate a .nvmrc file (Node.js version pin)",
    "pythonversion": "Generate a .python-version file",
    "renovate": "Generate a renovate.json (dependency updates)",
    "githubissue": "Generate GitHub issue templates",
    "lintconfig": "Generate linter config (ruff.toml / eslint.config.mjs / golangci.yml)",
    "security": "Generate SECURITY.md (vulnerability disclosure policy)",
    "ciworkflow": "Generate GitHub Actions CI workflow",
    "codeowners": "Generate CODEOWNERS file",
    "pullrequest": "Generate GitHub PR template",
    "tsconfig": "Generate tsconfig.json (strict TypeScript config)",
    "pyproject": "Generate pyproject.toml (modern Python packaging)",
    "flytoml": "Generate fly.toml (Fly.io deployment)",
    "helmvalues": "Generate Helm values.yaml",
    "testfile": "Generate a test file template for a module",
    "envexample": "Generate .env.example with common variables",
    "githook": "Generate a git pre-commit hook script",
}


@main.command("scaffold")
@click.argument("file_type", type=click.Choice(list(_SCAFFOLD_FILES.keys())))
@click.option(
    "--lang",
    "-l",
    type=click.Choice(["python", "typescript", "javascript", "go", "rust", "java"]),
    default=None,
    help="Primary language (auto-detected if omitted)",
)
@click.option(
    "--framework",
    "-f",
    default=None,
    help="Framework (e.g. fastapi, nextjs, gin, axum)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=".",
    help="Output directory (default: current)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print content to stdout without writing files",
)
@click.option(
    "--name",
    "-n",
    default=None,
    help="Module/class name for testfile scaffold (e.g. UserService)",
)
def scaffold_file(file_type, lang, framework, output_dir, dry_run, name):
    """Generate a single scaffold file — no full wizard needed.

    \b
    Available files:
      gitignore     — .gitignore (language-aware)
      dockerfile    — Dockerfile (framework-aware)
      makefile      — Makefile with dev/test/build targets
      dockercompose — docker-compose.yml
      editorconfig  — .editorconfig (consistent editor settings)
      nvmrc         — .nvmrc (Node version pin)
      pythonversion — .python-version
      renovate      — renovate.json (dependency automation)
      githubissue   — GitHub issue templates
      lintconfig    — ruff.toml / eslint.config.mjs / golangci.yml / clippy.toml
      security      — SECURITY.md (vulnerability disclosure policy)
      ciworkflow    — GitHub Actions CI workflow
      codeowners    — CODEOWNERS file
      pullrequest   — GitHub PR template
      tsconfig      — tsconfig.json (strict TypeScript)
      pyproject     — pyproject.toml (modern Python packaging)
      flytoml       — fly.toml (Fly.io deployment)
      helmvalues    — Helm values.yaml
      testfile      — test file template (use --name ModuleName)
      envexample    — .env.example with common variables
      githook       — git pre-commit hook script

    \b
    Examples:
        vcsx scaffold gitignore --lang python
        vcsx scaffold dockerfile --lang python --framework fastapi
        vcsx scaffold makefile --lang go
        vcsx scaffold dockercompose --lang typescript --framework nextjs
        vcsx scaffold editorconfig
    """
    from vcsx.core.scanner import scan_project

    target = Path(output_dir).resolve()

    # Auto-detect language if not specified
    if not lang:
        detected = scan_project(str(target))
        lang = detected.get("language", "typescript") or "typescript"
        if not framework:
            framework = detected.get("framework", "") or ""
        console.print(f"[dim]Auto-detected: {lang}{f' / {framework}' if framework else ''}[/]")

    lang_lower = lang.lower()
    fw_lower = (framework or "").lower()
    content, filename = _generate_scaffold_content(file_type, lang_lower, fw_lower, name or "MyModule")

    if dry_run:
        console.print(f"\n[bold]# {filename}[/]\n")
        console.print(content)
        return

    out_path = target / filename
    if out_path.exists():
        console.print(f"[yellow]⚠ {filename} already exists — skipping.[/]")
        console.print("  Use [dim]--dry-run[/] to preview, or delete the file first.")
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    console.print(f"\n[green]✓ Created:[/] {out_path.relative_to(target)}")


def _generate_scaffold_content(file_type: str, lang: str, framework: str, name: str = "MyModule") -> tuple[str, str]:
    """Return (content, filename) for the given scaffold type."""

    if file_type == "gitignore":
        return _scaffold_gitignore_content(lang), ".gitignore"

    elif file_type == "dockerfile":
        return _scaffold_dockerfile_content(lang, framework), "Dockerfile"

    elif file_type == "makefile":
        return _scaffold_makefile_content(lang, framework), "Makefile"

    elif file_type == "dockercompose":
        return _scaffold_dockercompose_content(lang, framework), "docker-compose.yml"

    elif file_type == "editorconfig":
        return _scaffold_editorconfig_content(lang), ".editorconfig"

    elif file_type == "nvmrc":
        return "22\n", ".nvmrc"

    elif file_type == "pythonversion":
        return "3.12\n", ".python-version"

    elif file_type == "renovate":
        return _scaffold_renovate_content(lang), "renovate.json"

    elif file_type == "githubissue":
        return _scaffold_github_issue_content(), ".github/ISSUE_TEMPLATE/bug_report.md"

    elif file_type == "lintconfig":
        return _scaffold_lintconfig_content(lang), _lintconfig_filename(lang)

    elif file_type == "security":
        return _scaffold_security_md(), "SECURITY.md"

    elif file_type == "ciworkflow":
        return _scaffold_ci_workflow_content(lang), ".github/workflows/ci.yml"

    elif file_type == "codeowners":
        return _scaffold_codeowners_content(), "CODEOWNERS"

    elif file_type == "pullrequest":
        return _scaffold_pr_template_content(), ".github/pull_request_template.md"

    elif file_type == "tsconfig":
        return _scaffold_tsconfig_content(), "tsconfig.json"

    elif file_type == "pyproject":
        return _scaffold_pyproject_toml_content(framework), "pyproject.toml"

    elif file_type == "flytoml":
        return _scaffold_flytoml_content(lang, framework), "fly.toml"

    elif file_type == "helmvalues":
        return _scaffold_helm_values_content(lang), "values.yaml"

    elif file_type == "testfile":
        content, filename = _scaffold_testfile_content(lang, name)
        return content, filename

    elif file_type == "envexample":
        return _scaffold_env_example_content(framework), ".env.example"

    elif file_type == "githook":
        return _scaffold_githook_content(lang), ".githooks/pre-commit"

    return "", f"{file_type}.txt"


def _scaffold_gitignore_content(lang: str) -> str:
    base = """# Editor
.idea/
.vscode/
*.swp
*.swo
.DS_Store
Thumbs.db

# Environment
.env
.env.local
.env.*.local
!.env.example
"""
    lang_sections = {
        "python": """
# Python
__pycache__/
*.py[cod]
*.so
*.egg
*.egg-info/
dist/
build/
.eggs/
.venv/
venv/
env/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
coverage.xml
htmlcov/
""",
        "typescript": """
# Node / TypeScript
node_modules/
dist/
build/
.next/
.nuxt/
out/
.cache/
*.tsbuildinfo
coverage/
""",
        "javascript": """
# Node / JavaScript
node_modules/
dist/
build/
.next/
out/
.cache/
coverage/
""",
        "go": """
# Go
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.out
vendor/
""",
        "rust": """
# Rust
/target/
Cargo.lock
**/*.rs.bk
*.pdb
""",
        "java": """
# Java
*.class
*.jar
*.war
*.ear
target/
.gradle/
build/
""",
    }
    return base + lang_sections.get(lang, "")


def _scaffold_dockerfile_content(lang: str, framework: str) -> str:
    if lang == "python":
        port = "8000"
        if "flask" in framework:
            port = "5000"
        return f"""# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

EXPOSE {port}

# Use non-root user for security
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{port}"]
"""
    elif lang in ("typescript", "javascript"):
        return """# syntax=docker/dockerfile:1
FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json .
RUN npm ci

COPY . .
RUN npm run build

# Production image
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json .
RUN npm ci --omit=dev

# Non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

EXPOSE 3000
CMD ["node", "dist/index.js"]
"""
    elif lang == "go":
        return """# syntax=docker/dockerfile:1
FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod go.sum .
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o app .

# Minimal runtime image
FROM scratch
COPY --from=builder /app/app /app
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

EXPOSE 8080
ENTRYPOINT ["/app"]
"""
    elif lang == "rust":
        return """# syntax=docker/dockerfile:1
FROM rust:1.78-alpine AS builder

RUN apk add --no-cache musl-dev
WORKDIR /app
COPY Cargo.toml Cargo.lock .
RUN mkdir src && echo 'fn main(){}' > src/main.rs
RUN cargo build --release && rm -f target/release/deps/app*

COPY src ./src
RUN cargo build --release

# Minimal runtime
FROM alpine:3.19
RUN apk add --no-cache ca-certificates
COPY --from=builder /app/target/release/app /usr/local/bin/app

EXPOSE 3000
ENTRYPOINT ["app"]
"""
    else:
        return """FROM ubuntu:22.04
WORKDIR /app
COPY . .
EXPOSE 8080
CMD ["./app"]
"""


def _scaffold_makefile_content(lang: str, framework: str) -> str:
    if lang == "python":
        return """.PHONY: install dev test lint format type-check clean

install:
\tpip install -r requirements.txt

dev:
\tuvicorn main:app --reload

test:
\tpytest tests/ -v

test-cov:
\tpytest tests/ --cov=src --cov-report=term-missing

lint:
\truff check .

format:
\truff format .

type-check:
\tpyright src/ || mypy src/

clean:
\tfind . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
\trm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage

check: format lint type-check test
\t@echo "All checks passed!"
"""
    elif lang in ("typescript", "javascript"):
        pkg = "npm"
        return f""".PHONY: install dev build test lint format type-check clean

install:
\t{pkg} install

dev:
\t{pkg} run dev

build:
\t{pkg} run build

test:
\t{pkg} test

test-watch:
\tnpx vitest

lint:
\t{pkg} run lint

format:
\tnpx prettier --write .

type-check:
\tnpx tsc --noEmit

clean:
\trm -rf dist build .next node_modules/.cache coverage

check: format lint type-check test
\t@echo "All checks passed!"
"""
    elif lang == "go":
        return """.PHONY: build test lint format vet clean run

build:
\tgo build -o bin/app ./...

run:
\tgo run .

test:
\tgo test -race -v ./...

test-cov:
\tgo test -race -coverprofile=coverage.out ./...
\tgo tool cover -html=coverage.out -o coverage.html

lint:
\tgolangci-lint run

format:
\tgofmt -w .
\tgoimports -w .

vet:
\tgo vet ./...

tidy:
\tgo mod tidy

clean:
\trm -rf bin/ coverage.out coverage.html

check: format vet lint test
\t@echo "All checks passed!"
"""
    elif lang == "rust":
        return """.PHONY: build release test lint format clean

build:
\tcargo build

release:
\tcargo build --release

run:
\tcargo run

test:
\tcargo test

test-all:
\tcargo test --all-features

lint:
\tcargo clippy -- -D warnings

format:
\tcargo fmt

format-check:
\tcargo fmt --all -- --check

audit:
\tcargo audit

clean:
\tcargo clean

check: format-check lint test
\t@echo "All checks passed!"
"""
    else:
        return """.PHONY: build test clean

build:
\t@echo "Add build command"

test:
\t@echo "Add test command"

clean:
\t@echo "Add clean command"
"""


def _scaffold_dockercompose_content(lang: str, framework: str) -> str:
    port = "3000"
    if lang == "python":
        port = "8000" if "flask" not in framework else "5000"
    elif lang == "go":
        port = "8080"

    return f"""services:
  app:
    build: .
    ports:
      - "{port}:{port}"
    environment:
      - NODE_ENV=development
    env_file:
      - .env
    volumes:
      - .:/app
      - /app/node_modules  # Prevent host node_modules override
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${{POSTGRES_DB:-appdb}}
      POSTGRES_USER: ${{POSTGRES_USER:-appuser}}
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD:-changeme}}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{POSTGRES_USER:-appuser}}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres_data:
"""


def _scaffold_editorconfig_content(lang: str) -> str:
    indent_size = "4" if lang in ("python", "java", "rust") else "2"
    use_tabs = "false"
    if lang == "go":
        use_tabs = "true"
        indent_size = "4"

    return f"""# EditorConfig — https://editorconfig.org
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = {"tab" if use_tabs == "true" else "space"}
indent_size = {indent_size}

[*.md]
trim_trailing_whitespace = false
max_line_length = off

[*.{{json,yaml,yml,toml}}]
indent_size = 2

[Makefile]
indent_style = tab

[*.{{sh,bash}}]
indent_size = 2
"""


def _scaffold_renovate_content(lang: str) -> str:
    import json as _json

    config: dict = {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "extends": ["config:recommended"],
        "schedule": ["before 6am on Monday"],
        "timezone": "UTC",
        "prConcurrentLimit": 10,
        "prHourlyLimit": 2,
        "automerge": False,
        "labels": ["dependencies"],
        "packageRules": [
            {
                "matchUpdateTypes": ["minor", "patch"],
                "matchDepTypes": ["devDependencies"],
                "automerge": True,
                "description": "Auto-merge minor/patch dev dep updates",
            }
        ],
    }
    if lang in ("typescript", "javascript"):
        config["packageRules"].append({
            "matchPackagePatterns": ["^@types/"],
            "automerge": True,
            "description": "Auto-merge @types updates",
        })
    return _json.dumps(config, indent=2) + "\n"


def _scaffold_github_issue_content() -> str:
    return """---
name: Bug Report
about: Report a bug or unexpected behavior
title: "[BUG] "
labels: bug
assignees: ''
---

## Description
A clear description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Run '...'
3. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened. Include error messages and stack traces.

## Environment
- OS: [e.g. macOS 14, Ubuntu 22.04]
- Version: [e.g. 1.2.3]
- Language runtime: [e.g. Python 3.12, Node 20]

## Additional Context
Any other context, screenshots, or logs.
"""


def _lintconfig_filename(lang: str) -> str:
    return {
        "python": "ruff.toml",
        "typescript": "eslint.config.mjs",
        "javascript": "eslint.config.mjs",
        "go": ".golangci.yml",
        "rust": ".clippy.toml",
    }.get(lang, "ruff.toml")


def _scaffold_lintconfig_content(lang: str) -> str:
    if lang == "python":
        return """# ruff.toml — https://docs.astral.sh/ruff/configuration/
target-version = "py312"
line-length = 100
indent-width = 4

[lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
    "RUF",  # ruff-specific rules
]
ignore = [
    "E501",   # Line too long — handled by formatter
    "B008",   # Do not perform function calls in default arguments
    "B904",   # Use raise X from Y
]

[lint.isort]
known-first-party = ["src"]

[lint.per-file-ignores]
"tests/**" = ["S101"]  # Allow assert in tests

[format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true
"""
    elif lang in ("typescript", "javascript"):
        return """// eslint.config.mjs
import js from "@eslint/js";
import ts from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import globals from "globals";

/** @type {import('eslint').Linter.Config[]} */
export default [
  js.configs.recommended,
  {
    files: ["**/*.ts", "**/*.tsx"],
    plugins: { "@typescript-eslint": ts },
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        project: "./tsconfig.json",
        ecmaVersion: "latest",
        sourceType: "module",
      },
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      ...ts.configs["recommended"].rules,
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/explicit-function-return-type": "warn",
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "prefer-const": "error",
      "no-var": "error",
      eqeqeq: ["error", "always"],
    },
  },
  {
    files: ["**/*.test.ts", "**/*.spec.ts", "tests/**"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
  {
    ignores: ["dist/", "build/", ".next/", "node_modules/", "coverage/"],
  },
];
"""
    elif lang == "go":
        return """# .golangci.yml — https://golangci-lint.run/usage/configuration/
run:
  timeout: 5m
  go: "1.22"

linters:
  enable:
    - errcheck       # Check returned errors
    - gosimple       # Simplify code
    - govet          # Go vet
    - ineffassign    # Detect ineffectual assignments
    - staticcheck    # Static analysis
    - unused         # Detect unused code
    - gofmt          # Formatting
    - goimports      # Import ordering
    - misspell       # Spelling errors
    - godot          # Comment periods
    - exhaustive     # Exhaustive switch statements
    - noctx          # HTTP requests without context
    - bodyclose      # HTTP response body close
    - sqlcloserows   # sql.Rows close

linters-settings:
  errcheck:
    check-type-assertions: true
  govet:
    enable:
      - shadow
  goimports:
    local-prefixes: github.com/your-org/your-repo

issues:
  exclude-rules:
    - path: "_test.go"
      linters:
        - errcheck
        - exhaustive
"""
    elif lang == "rust":
        return """# .clippy.toml — https://doc.rust-lang.org/clippy/configuration.html
msrv = "1.78"
cognitive-complexity-threshold = 25
too-many-arguments-threshold = 7
too-many-lines-threshold = 100
type-complexity-threshold = 250
"""
    else:
        return """# Linter configuration
# Add your language-specific linter config here
"""


def _scaffold_security_md() -> str:
    return """# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest  | ✅        |
| < 1.0   | ❌        |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

To report a security vulnerability:

1. **Email** the maintainers at: security@example.com
   (Replace with your actual security contact)

2. **Include** in your report:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

3. **Response time**: We aim to acknowledge reports within **48 hours**
   and provide a fix timeline within **7 days** for critical issues.

## What to Report

- Remote code execution
- SQL injection or other injection attacks
- Authentication bypass
- Sensitive data exposure
- Cross-site scripting (XSS)
- Insecure direct object references
- Security misconfiguration

## What NOT to Report

- Issues that require physical access to the machine
- Denial of service attacks that require > 100 requests/second
- Issues in dependencies (report those to the respective project)

## Disclosure Policy

We follow **coordinated disclosure**:
1. Reporter submits vulnerability privately
2. We confirm and assess the issue
3. We develop and test a fix
4. We release the fix and credit the reporter (if desired)
5. Public disclosure after users have had time to update

Thank you for helping keep this project secure.
"""


def _scaffold_ci_workflow_content(lang: str) -> str:
    """Generate GitHub Actions CI workflow (standalone scaffold version)."""
    if lang == "python":
        steps = """      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
      - run: pip install -r requirements.txt
      - run: ruff format --check .
      - run: ruff check .
      - run: pytest --tb=short -q"""
    elif lang in ("typescript", "javascript"):
        steps = """      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npx tsc --noEmit
      - run: npm run lint
      - run: npm test
      - run: npm run build"""
    elif lang == "go":
        steps = """      - uses: actions/setup-go@v5
        with:
          go-version: "1.22"
          cache: true
      - run: go mod download
      - run: go vet ./...
      - run: go test -race -coverprofile=coverage.out ./...
      - run: go build ./..."""
    elif lang == "rust":
        steps = """      - uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      - uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/bin/
            ~/.cargo/registry/
            target/
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
      - run: cargo fmt --all -- --check
      - run: cargo clippy -- -D warnings
      - run: cargo test"""
    else:
        steps = """      - run: echo "Add build and test steps here\""""

    return f"""name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

concurrency:
  group: ${{{{ github.workflow }}}}-${{{{ github.ref }}}}
  cancel-in-progress: true

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

{steps}
"""


def _scaffold_codeowners_content() -> str:
    return """# CODEOWNERS — https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners

# Global owners (catch-all)
* @your-username

# Source code
/src/ @your-username

# Tests
/tests/ @your-username

# CI/CD
/.github/ @your-username

# Documentation
/docs/ @your-username
*.md @your-username

# Dependencies
package.json @your-username
requirements*.txt @your-username
go.mod @your-username
Cargo.toml @your-username
"""


def _scaffold_pr_template_content() -> str:
    return """## Summary

<!-- One sentence: what does this PR do? -->

## Motivation

<!-- Why is this change needed? Link to issue if applicable. Closes #X -->

## Changes

<!-- Bullet list of what was changed/added/removed -->

- PLACEHOLDER
- PLACEHOLDER
- PLACEHOLDER

## Testing

<!-- How was this tested? What should reviewers verify? -->

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing done (describe steps)

## Checklist

- [ ] Tests pass (`run test suite`)
- [ ] No hardcoded secrets or credentials
- [ ] Documentation updated (if behavior changed)
- [ ] Breaking changes documented (if any)
- [ ] PR is small and focused (one logical change)

## Screenshots / Demo

<!-- If applicable, add screenshots or a short demo -->

## Notes for Reviewers

<!-- Anything the reviewer should pay special attention to -->
"""


def _scaffold_tsconfig_content() -> str:
    return """{
  "$schema": "https://json.schemastore.org/tsconfig",
  "compilerOptions": {
    /* Language */
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",

    /* Strictness */
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true,
    "noPropertyAccessFromIndexSignature": true,

    /* Output */
    "outDir": "dist",
    "rootDir": "src",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "removeComments": false,

    /* Interop */
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "forceConsistentCasingInFileNames": true,

    /* Performance */
    "skipLibCheck": true,
    "incremental": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "coverage", "**/*.test.ts", "**/*.spec.ts"]
}
"""


def _scaffold_pyproject_toml_content(framework: str) -> str:
    fw_lower = (framework or "").lower()

    # Framework-specific dependencies
    if "fastapi" in fw_lower:
        deps = '"fastapi>=0.110.0", "uvicorn[standard]>=0.29.0", "pydantic>=2.0.0"'
        dev_extras = '"httpx>=0.27.0"'  # For testing FastAPI
    elif "django" in fw_lower:
        deps = '"django>=5.0.0", "djangorestframework>=3.15.0"'
        dev_extras = '"pytest-django>=4.8.0"'
    elif "flask" in fw_lower:
        deps = '"flask>=3.0.0"'
        dev_extras = '"pytest-flask>=1.3.0"'
    else:
        deps = '# Add your dependencies here'
        dev_extras = ""

    dev_deps_extra = f",\n  {dev_extras}" if dev_extras else ""

    return f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-project"
version = "0.1.0"
description = "A Python project"
readme = "README.md"
requires-python = ">=3.12"
license = {{text = "MIT"}}
authors = [
  {{name = "Your Name", email = "you@example.com"}},
]
keywords = []
classifiers = [
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.12",
]
dependencies = [
  {deps},
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
  "pytest-cov>=5.0.0",
  "ruff>=0.4.0",
  "pyright>=1.1.0",
  "pre-commit>=3.7.0"{dev_deps_extra},
]

[project.urls]
Repository = "https://github.com/your-org/your-repo"

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
filterwarnings = ["error"]

[tool.coverage.run]
source = ["src"]
omit = ["tests/*"]

[tool.coverage.report]
exclude_lines = [
  "pragma: no cover",
  "if TYPE_CHECKING:",
  "raise NotImplementedError",
]

[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "standard"
venvPath = "."
venv = ".venv"
"""


def _scaffold_flytoml_content(lang: str, framework: str) -> str:
    port = "8080"
    if lang == "python":
        port = "8000"
        if "flask" in (framework or "").lower():
            port = "5000"

    return f"""# fly.toml — Fly.io deployment configuration
# Reference: https://fly.io/docs/reference/configuration/

app = "your-app-name"
primary_region = "iad"  # Change to your preferred region

[build]

[env]
  PORT = "{port}"
  # Add non-secret environment variables here

[[services]]
  protocol = "tcp"
  internal_port = {port}
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [services.concurrency]
    type = "connections"
    hard_limit = 25
    soft_limit = 20

  [[services.http_checks]]
    interval = "10s"
    timeout = "2s"
    grace_period = "5s"
    method = "GET"
    path = "/health"
    protocol = "http"

[metrics]
  port = 9091
  path = "/metrics"

# Scale: fly scale count 2 --region iad
# Secrets: fly secrets set SECRET_KEY=value
"""


def _scaffold_helm_values_content(lang: str) -> str:
    port = 8080
    if lang == "python":
        port = 8000

    values = {
        "replicaCount": 2,
        "image": {
            "repository": "your-registry/your-app",
            "tag": "latest",
            "pullPolicy": "IfNotPresent",
        },
        "service": {
            "type": "ClusterIP",
            "port": 80,
            "targetPort": port,
        },
        "ingress": {
            "enabled": True,
            "className": "nginx",
            "annotations": {
                "cert-manager.io/cluster-issuer": "letsencrypt-prod",
            },
            "hosts": [{"host": "your-app.example.com", "paths": [{"path": "/", "pathType": "Prefix"}]}],
            "tls": [{"secretName": "your-app-tls", "hosts": ["your-app.example.com"]}],
        },
        "resources": {
            "requests": {"cpu": "100m", "memory": "128Mi"},
            "limits": {"cpu": "500m", "memory": "512Mi"},
        },
        "autoscaling": {
            "enabled": True,
            "minReplicas": 2,
            "maxReplicas": 10,
            "targetCPUUtilizationPercentage": 80,
        },
        "env": [],
        "envFrom": [],
        "livenessProbe": {
            "httpGet": {"path": "/health", "port": "http"},
            "initialDelaySeconds": 30,
            "periodSeconds": 10,
        },
        "readinessProbe": {
            "httpGet": {"path": "/ready", "port": "http"},
            "initialDelaySeconds": 5,
            "periodSeconds": 5,
        },
    }

    # Convert to YAML-like format manually for readability
    return f"""# values.yaml — Helm chart configuration
# Override with: helm upgrade -f custom-values.yaml

replicaCount: {values['replicaCount']}

image:
  repository: your-registry/your-app
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80
  targetPort: {port}

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: your-app.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: your-app-tls
      hosts:
        - your-app.example.com

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

env: []
  # - name: DATABASE_URL
  #   valueFrom:
  #     secretKeyRef:
  #       name: app-secrets
  #       key: database-url

livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
"""


def _scaffold_testfile_content(lang: str, name: str) -> tuple[str, str]:
    """Generate a test file template for a given module name."""
    snake = "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip("_")
    # e.g. UserService → user_service

    if lang == "python":
        filename = f"tests/test_{snake}.py"
        content = f"""\"\"\"Tests for {name}.\"\"\"
import pytest


class Test{name}:
    \"\"\"Test suite for {name}.\"\"\"

    # ─── Fixtures ──────────────────────────────────────────────────────────

    @pytest.fixture
    def subject(self):
        \"\"\"Return a fresh instance of {name} for each test.\"\"\"
        # TODO: return {name}(...)
        pass

    # ─── Happy Path ────────────────────────────────────────────────────────

    def test_{snake}_returns_expected_value(self, subject):
        \"\"\"Describe the happy-path behavior here.\"\"\"
        # Arrange
        # TODO: set up input data

        # Act
        # result = subject.some_method(...)

        # Assert
        # assert result == expected
        pass

    # ─── Edge Cases ────────────────────────────────────────────────────────

    def test_{snake}_with_empty_input_raises(self, subject):
        \"\"\"Empty input should raise ValueError (or appropriate error).\"\"\"
        with pytest.raises((ValueError, TypeError)):
            pass  # TODO: subject.some_method("")

    def test_{snake}_with_none_input_raises(self, subject):
        with pytest.raises((ValueError, TypeError)):
            pass  # TODO: subject.some_method(None)

    # ─── Error Cases ───────────────────────────────────────────────────────

    def test_{snake}_handles_external_failure_gracefully(self, subject, mocker):
        \"\"\"When external dependency fails, should raise specific error.\"\"\"
        # mocker.patch("module.external_call", side_effect=ConnectionError)
        pass
"""

    elif lang in ("typescript", "javascript"):
        filename = f"tests/{snake}.test.ts" if lang == "typescript" else f"tests/{snake}.test.js"
        content = f"""import {{ describe, it, expect, beforeEach, vi }} from 'vitest'
// import {{ {name} }} from '../src/{snake}'

describe('{name}', () => {{
  // ─── Setup ───────────────────────────────────────────────────────────────

  let subject: any // TODO: type as {name}

  beforeEach(() => {{
    // subject = new {name}(...)
  }})

  // ─── Happy Path ──────────────────────────────────────────────────────────

  it('should return expected value', () => {{
    // Arrange
    // const input = ...

    // Act
    // const result = subject.someMethod(input)

    // Assert
    // expect(result).toBe(expected)
    expect(true).toBe(true) // TODO: replace with real assertion
  }})

  // ─── Edge Cases ──────────────────────────────────────────────────────────

  it('should throw on empty input', () => {{
    expect(() => {{
      // subject.someMethod('')
    }}).toThrow()
  }})

  it('should throw on null input', () => {{
    expect(() => {{
      // subject.someMethod(null)
    }}).toThrow()
  }})

  // ─── Mocking External Dependencies ──────────────────────────────────────

  it('should handle external failure gracefully', () => {{
    // vi.spyOn(externalModule, 'call').mockRejectedValue(new Error('network'))
    // await expect(subject.someMethod()).rejects.toThrow('network')
    expect(true).toBe(true)
  }})
}})
"""

    elif lang == "go":
        pkg = snake.replace("_", "")
        filename = f"{snake}_test.go"
        content = f"""package {pkg}

import (
\t"testing"
)

func Test{name}(t *testing.T) {{
\tt.Run("returns expected value", func(t *testing.T) {{
\t\t// Arrange
\t\t// input := ...

\t\t// Act
\t\t// result, err := Some{name}Function(input)

\t\t// Assert
\t\t// if err != nil {{
\t\t// \tt.Fatalf("unexpected error: %v", err)
\t\t// }}
\t\t// if result != expected {{
\t\t// \tt.Errorf("got %v, want %v", result, expected)
\t\t// }}
\t}})

\tt.Run("returns error on empty input", func(t *testing.T) {{
\t\t// _, err := Some{name}Function("")
\t\t// if err == nil {{
\t\t// \tt.Fatal("expected error, got nil")
\t\t// }}
\t}})
}}

// Table-driven test pattern (preferred for multiple cases)
func Test{name}Cases(t *testing.T) {{
\ttests := []struct {{
\t\tname    string
\t\tinput   string
\t\twant    string
\t\twantErr bool
\t}}{{
\t\t{{name: "valid input", input: "hello", want: "HELLO", wantErr: false}},
\t\t{{name: "empty input", input: "", want: "", wantErr: true}},
\t}}

\tfor _, tc := range tests {{
\t\tt.Run(tc.name, func(t *testing.T) {{
\t\t\t// got, err := SomeFunc(tc.input)
\t\t\t// if (err != nil) != tc.wantErr {{
\t\t\t// \tt.Errorf("error = %v, wantErr %v", err, tc.wantErr)
\t\t\t// }}
\t\t}})
\t}}
}}
"""

    elif lang == "rust":
        filename = f"tests/{snake}.rs"
        content = f"""// Tests for {name}
// Add to Cargo.toml: [[test]] name = "{snake}" path = "tests/{snake}.rs"
// Or place inline in src/{snake}.rs inside #[cfg(test)]

#[cfg(test)]
mod tests {{
    use super::*;

    // ─── Happy Path ──────────────────────────────────────────────────────

    #[test]
    fn test_{snake}_returns_expected() {{
        // Arrange
        // let input = ...;

        // Act
        // let result = some_function(input);

        // Assert
        // assert_eq!(result, expected);
        assert!(true); // TODO: replace with real assertion
    }}

    // ─── Edge Cases ──────────────────────────────────────────────────────

    #[test]
    fn test_{snake}_empty_input_returns_error() {{
        // let result = some_function("");
        // assert!(result.is_err());
        assert!(true);
    }}

    // ─── Error Cases ─────────────────────────────────────────────────────

    #[test]
    #[should_panic(expected = "expected panic message")]
    fn test_{snake}_panics_on_invariant_violation() {{
        // Call function that should panic
        // panic!("expected panic message"); // TODO: replace
    }}
}}
"""

    else:
        filename = f"tests/test_{snake}.txt"
        content = f"# Test template for {name}\n# TODO: add tests\n"

    return content, filename


def _scaffold_env_example_content(framework: str) -> str:
    fw = (framework or "").lower()

    base = """# .env.example — Copy to .env and fill in values
# Never commit .env to version control

# Application
APP_ENV=development
APP_PORT=8000
APP_SECRET_KEY=change-me-in-production
DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
# Alternatives:
# DATABASE_URL=sqlite:///./app.db
# DATABASE_URL=mysql://user:password@localhost:3306/mydb

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

"""

    if "fastapi" in fw or "django" in fw or "flask" in fw:
        base += """# Python web framework
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

"""
    elif "next" in fw or "react" in fw or "vite" in fw:
        base += """# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
VITE_API_URL=http://localhost:8000

"""

    base += """# Auth (pick one)
JWT_SECRET=change-me
# OAUTH_CLIENT_ID=
# OAUTH_CLIENT_SECRET=
# GITHUB_TOKEN=

# AI / LLM (optional)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GEMINI_API_KEY=AIza...

# Storage (optional)
# S3_BUCKET=my-bucket
# S3_REGION=us-east-1
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=

# Monitoring (optional)
# SENTRY_DSN=https://...
# DATADOG_API_KEY=
"""
    return base


def _scaffold_githook_content(lang: str) -> str:
    if lang == "python":
        lint_cmd = "ruff check ."
        fmt_cmd = "ruff format --check ."
        test_hint = "# pytest tests/ -q --tb=short  # Uncomment to run tests pre-commit"
    elif lang in ("typescript", "javascript"):
        lint_cmd = "npx eslint ."
        fmt_cmd = "npx prettier --check ."
        test_hint = "# npx vitest run  # Uncomment to run tests pre-commit"
    elif lang == "go":
        lint_cmd = "go vet ./..."
        fmt_cmd = "gofmt -l . | grep -q . && echo 'Run gofmt' && exit 1 || true"
        test_hint = "# go test ./...  # Uncomment to run tests pre-commit"
    elif lang == "rust":
        lint_cmd = "cargo clippy -- -D warnings"
        fmt_cmd = "cargo fmt --all -- --check"
        test_hint = "# cargo test  # Uncomment to run tests pre-commit"
    else:
        lint_cmd = "echo 'No linter configured'"
        fmt_cmd = "echo 'No formatter configured'"
        test_hint = "# Add test command here"

    return f"""#!/bin/bash
# Git pre-commit hook — runs automatically before each commit
# Install: chmod +x .githooks/pre-commit && git config core.hooksPath .githooks
#
# To skip for a specific commit: git commit --no-verify

set -e  # Exit immediately on any error

echo "🔍 Pre-commit checks..."

# ─── Secrets scan ────────────────────────────────────────────────────────────
echo "  Checking for secrets..."
if git diff --cached --name-only | xargs grep -l -E "(AKIA[0-9A-Z]{{16}}|sk-[a-zA-Z0-9]{{20,}}|ghp_[a-zA-Z0-9]{{36}}|AIza[0-9A-Za-z_-]{{35}})" 2>/dev/null; then
    echo "❌ Potential secret detected in staged files. Aborting commit."
    echo "   Remove the secret and use environment variables instead."
    exit 1
fi

# ─── No debug artifacts ──────────────────────────────────────────────────────
echo "  Checking for debug artifacts..."
if git diff --cached | grep -E "^\\+.*(console\\.log|print(f)?\\(|debugger|pdb\\.set_trace|breakpoint\\()" | grep -v "//.*console\\.log\\|#.*print" | grep -q .; then
    echo "⚠️  Possible debug statement in staged changes."
    echo "   Review with: git diff --cached | grep -E 'console.log|print|debugger'"
    # Uncomment to make this a hard block:
    # exit 1
fi

# ─── Format check ────────────────────────────────────────────────────────────
echo "  Checking formatting..."
{fmt_cmd}

# ─── Lint ────────────────────────────────────────────────────────────────────
echo "  Running linter..."
{lint_cmd}

# ─── Tests (optional) ────────────────────────────────────────────────────────
{test_hint}

echo "✅ All pre-commit checks passed!"
"""


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
