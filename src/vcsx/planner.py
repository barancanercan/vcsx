"""Planner phase — Generates structured plan from discovered context."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from vcsx.core.context import ProjectContext


def generate_plan(ctx: ProjectContext, console: Console, cli_tools: list[str]) -> str:
    """Generate a formatted plan from project context."""
    plan_parts = [
        f"📋 PROJE PLANI: {ctx.project_name}",
        "",
        "🏗️ Mimari Kararlar",
        f"• Proje Tipi: {ctx.project_type}",
        f"• Tech Stack: {ctx.tech_stack}",
        f"• Dil: {ctx.language}",
        f"• Framework: {ctx.framework or 'None'}",
        f"• Hosting: {ctx.hosting or 'Belirtilmedi'}",
        f"• CLI Tools: {', '.join(cli_tools)}",
        "",
        "📁 Dizin Ağacı",
        _generate_tree(ctx),
        "",
        "🔧 Kurulacak Yapılandırma Dosyaları",
    ]

    if "claude-code" in cli_tools:
        plan_parts.extend(
            [
                "• CLAUDE.md → Build/test komutları, kod standartları, yasaklar (~70 satır)",
                "• .claude/skills/ → Workflow skill'leri (commit, PR, deploy, test, security, refactor)",
                "• .claude/settings.json → Hooks (güvenlik, otomasyon)",
                "• .claude/agents/ → Subagent tanımları (security-reviewer, test-writer, researcher)",
            ]
        )
    if "cursor" in cli_tools:
        plan_parts.extend(
            [
                "• .cursorrules → Cursor kuralları",
                "• .cursor/rules/ → Cursor rule dosyaları",
            ]
        )
    if "codex" in cli_tools:
        plan_parts.extend(["• .openai/instructions.md → Codex talimatları"])
    if "copilot" in cli_tools:
        plan_parts.extend(["• .github/copilot-instructions.md → Copilot talimatları"])

    plan_parts.extend(
        [
            "• Proje scaffold → Config dosyaları, .gitignore, README",
            "",
            "⚡ Deterministik vs Probabilistik Ayrımı",
            "• CLAUDE.md + Hooks = %100 zorunlu, her zaman çalışır",
            "• Skills + Agents = Bağlamsal/otomatik tetiklenme",
            "",
            "📦 MVP Sprint 1",
        ]
    )

    features = ctx.mvp_features.split(",") if ctx.mvp_features else []
    for i, feature in enumerate(features, 1):
        plan_parts.append(f"{i}. {feature.strip()}")
    if not features:
        plan_parts.extend(
            [
                "1. Proje iskeleti kurulumu",
                "2. Temel yapılandırma dosyaları",
                "3. İlk test setup'ı",
            ]
        )

    plan_parts.extend(
        [
            "",
            "🧩 Oluşturulacak Skill'ler",
        ]
    )

    skills = _determine_skills(ctx)
    for skill in skills:
        plan_parts.append(f"• /{skill['name']} — {skill['description']}")

    plan_parts.extend(
        [
            "",
            "🪝 Oluşturulacak Hook'lar",
            "• PreToolUse: Block destructive commands (rm -rf, git push --force)",
            f"• PostToolUse: Run {ctx.formatter} on file changes",
            f"• PostToolUse: Run {ctx.linter} after edits",
        ]
    )

    if ctx.test_level != "none":
        plan_parts.append("• Stop: Run test suite before session ends")

    plan_text = "\n".join(plan_parts)
    console.print(Panel(plan_text, title="Plan", border_style="cyan"))
    return plan_text


def confirm_plan(console: Console) -> bool:
    """Ask user to confirm the plan."""
    return Confirm.ask("\n✅ Planı onaylıyor musunuz? [y/N]", default=False)


def _generate_tree(ctx: ProjectContext) -> str:
    """Generate directory tree based on project type."""
    lines = [
        f"{ctx.project_name}/",
        "├── CLAUDE.md",
        "├── .claude/",
        "│   ├── settings.json",
        "│   ├── skills/",
        "│   │   ├── commit-message/SKILL.md",
        "│   │   ├── pr-review/SKILL.md",
        "│   │   ├── deploy/SKILL.md",
        "│   │   ├── test-patterns/SKILL.md",
        "│   │   ├── security-review/SKILL.md",
        "│   │   └── refactor/SKILL.md",
        "│   ├── agents/",
        "│   │   ├── security-reviewer.md",
        "│   │   ├── test-writer.md",
        "│   │   └── researcher.md",
        "│   └── hooks/",
        "│       ├── block_destructive.sh",
        "│       ├── auto_format.sh",
        "│       ├── auto_lint.sh",
        "│       └── secret_scan.sh",
        "├── .gitignore",
        "├── README.md",
    ]

    if ctx.project_type in ("web", "api", "cli"):
        lines.extend(["├── src/", "│   └── (source code)", "├── tests/", "│   └── (test files)"])
    elif ctx.project_type == "library":
        lines.extend(
            [
                "├── src/",
                "│   └── (library code)",
                "├── tests/",
                "│   └── (test files)",
                "├── docs/",
            ]
        )

    lines.append("└── (config files)")
    return "\n".join(lines)


def _determine_skills(ctx: ProjectContext) -> list[dict]:
    """Determine which skills to create."""
    skills = [
        {
            "name": "commit-message",
            "description": "Generates conventional commit messages from git diff",
        },
        {
            "name": "pr-review",
            "description": "Reviews PRs against team standards before submission",
        },
        {
            "name": "deploy",
            "description": f"Deploys to {ctx.hosting} with pre-deploy checklist"
            if ctx.hosting
            else "Deploys with pre-deploy checklist",
        },
        {
            "name": "security-review",
            "description": "Reviews code for security vulnerabilities",
        },
        {
            "name": "refactor",
            "description": "Suggests code improvements while maintaining behavior",
        },
    ]

    if ctx.auth_needed:
        skills.append(
            {
                "name": "auth-conventions",
                "description": f"Auth patterns using {ctx.auth_method}",
            }
        )
    if ctx.project_type == "api":
        skills.append(
            {
                "name": "api-conventions",
                "description": "REST API design patterns and endpoint naming",
            }
        )
    if ctx.test_level != "none":
        skills.append(
            {
                "name": "test-patterns",
                "description": f"Test writing patterns using {ctx.test_framework}",
            }
        )

    return skills
