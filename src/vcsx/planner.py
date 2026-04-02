"""Planner phase — Generates structured plan from discovered context with detailed explanations."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

from vcsx.core.context import ProjectContext


def generate_plan(ctx: ProjectContext, console: Console, cli_tools: list[str]) -> str:
    """Generate a detailed formatted plan from project context."""

    plan_sections = []

    # Header
    plan_sections.append("=" * 70)
    plan_sections.append(f"📋 PROJE PLANI: {ctx.project_name}")
    plan_sections.append("=" * 70)
    plan_sections.append("")

    # Project Overview (YENİ - Purpose & Problem)
    plan_sections.append("┌" + "─" * 68 + "┐")
    plan_sections.append("│ 🎯 PROJECT OVERVIEW                                          │")
    plan_sections.append("└" + "─" * 68 + "┘")
    plan_sections.append("")
    plan_sections.append(f"  📌 Amaç: {ctx.purpose}")
    plan_sections.append(f"  ❌ Problem: {ctx.problem}")
    plan_sections.append(f"  👥 Hedef Kullanıcılar: {ctx.target_users or 'Belirtilmedi'}")
    plan_sections.append("")

    if ctx.user_stories:
        plan_sections.append("  📖 User Stories:")
        for story in ctx.user_stories.strip().split("\n"):
            if story.strip():
                plan_sections.append(f"     • {story.strip()}")
        plan_sections.append("")

    if ctx.success_criteria:
        plan_sections.append("  ✅ Başarı Kriterleri:")
        for criterion in ctx.success_criteria.strip().split("\n"):
            if criterion.strip():
                plan_sections.append(f"     ✓ {criterion.strip()}")
        plan_sections.append("")

    # Technical Architecture
    plan_sections.append("┌" + "─" * 68 + "┐")
    plan_sections.append("│ 🏗️ MİMARİ KARARLAR                                            │")
    plan_sections.append("└" + "─" * 68 + "┘")
    plan_sections.append("")
    plan_sections.append(f"  • Proje Tipi: {ctx.project_type}")
    plan_sections.append(f"  • Tech Stack: {ctx.tech_stack}")
    plan_sections.append(f"  • Dil: {ctx.language}")
    plan_sections.append(f"  • Framework: {ctx.framework or 'Belirtilmedi'}")
    plan_sections.append(f"  • Hosting: {ctx.hosting or 'Sonra belirlenecek'}")
    plan_sections.append(f"  • Auth: {'Evet - ' + ctx.auth_method if ctx.auth_needed else 'Hayır'}")
    plan_sections.append(f"  • Test Seviyesi: {ctx.test_level}")
    plan_sections.append(f"  • CI/CD: {'Evet' if ctx.ci_cd else 'Hayır'}")
    plan_sections.append(f"  • AI Tools: {', '.join(cli_tools)}")
    plan_sections.append("")

    # MVP Features
    plan_sections.append("┌" + "─" * 68 + "┐")
    plan_sections.append("│ 🚀 MVP Sprint 1 - Kritik Özellikler                             │")
    plan_sections.append("└" + "─" * 68 + "┘")
    plan_sections.append("")
    features = ctx.mvp_features.split(",") if ctx.mvp_features else []
    for i, feature in enumerate(features, 1):
        plan_sections.append(f"  {i}. {feature.strip()}")
    if not features:
        plan_sections.extend(
            [
                "  1. Proje iskeleti kurulumu",
                "  2. Temel yapılandırma dosyaları",
                "  3. İlk test setup'ı",
            ]
        )
    plan_sections.append("")

    # Directory Structure
    plan_sections.append("┌" + "─" * 68 + "┐")
    plan_sections.append("│ 📁 DİZİN YAPISI                                               │")
    plan_sections.append("└" + "─" * 68 + "┘")
    plan_sections.append("")
    plan_sections.append(_generate_tree(ctx))
    plan_sections.append("")

    # Configuration Files with DETAILED EXPLANATIONS
    plan_sections.append("┌" + "─" * 68 + "┐")
    plan_sections.append("│ ⚙️ OLUŞTURULACAK YAPILANDIRMA DOSYALARI                        │")
    plan_sections.append("└" + "─" * 68 + "┘")
    plan_sections.append("")

    if "claude-code" in cli_tools:
        plan_sections.extend(
            [
                "  🤖 Claude Code Yapılandırması:",
                "",
                "  📄 CLAUDE.md (Proje Konvansiyonları)",
                "     ├─ Ne işe yarar: AI'ya projenin kurallarını, komutlarını ve yasaklarını söyler",
                "     ├─ İçerik: Build/test komutları, kod standartları, güvenlik kuralları",
                "     ├─ Satır: ~70 satır (max 200)",
                "     └─ Kullanım: Her AI oturumunda otomatik yüklenir",
                "",
                "  📁 .claude/skills/ (Workflow Otomasyonları)",
                "     ├─ commit-message/SKILL.md → Conventional commit mesajları üretir",
                "     ├─ pr-review/SKILL.md → PR'leri team standartlarına göre review eder",
                "     ├─ deploy/SKILL.md → {hosting}'a pre-deploy checklist ile deploy eder".format(
                    hosting=ctx.hosting or "hedef"
                ),
                "     ├─ test-patterns/SKILL.md → {test_framework} ile test yazma kalıpları".format(
                    test_framework=ctx.test_framework or "test"
                ),
                "     ├─ security-review/SKILL.md → Güvenlik açıklarını tarar",
                "     └─ refactor/SKILL.md → Davranışı koruyarak kod iyileştirmeleri önerir",
                "",
                "  📁 .claude/settings.json (Hook'lar - Otomatik Çalışan)",
                "     ├─ PreToolUse → rm -rf, git push --force gibi tehlikeli komutları bloklar",
                "     ├─ PostToolUse → Dosya kaydettiğinde {formatter} çalıştırır".format(
                    formatter=ctx.formatter
                ),
                "     ├─ PostToolUse → Edit sonrası {linter} çalıştırır".format(linter=ctx.linter),
                "     └─ SessionStart/Stop → Test suite çalıştırır",
                "",
                "  📁 .claude/agents/ (Subagent'lar)",
                "     ├─ security-reviewer.md → Özel güvenlik review agent'ı",
                "     ├─ test-writer.md → Özel test yazma agent'ı",
                "     └─ researcher.md → Dokümantasyon araştırma agent'ı",
                "",
            ]
        )

    if "cursor" in cli_tools:
        plan_sections.extend(
            [
                "  🎯 Cursor Yapılandırması:",
                "",
                "  📄 .cursorrules (Ana Kurallar)",
                "     ├─ Ne işe yarar: Cursor IDE'ye proje kurallarını söyler",
                "     └─ Kullanım: Cursor her dosyayı açtığında otomatik yüklenir",
                "",
                "  📁 .cursor/rules/ (Detaylı Kurallar - YENİ .mdc format)",
                "     ├─ Ne işe yarar: Frontmatter ile globs, alwaysApply desteği",
                "     ├─ Format: Markdown + YAML frontmatter",
                "     └─ Örnek: code-style.mdc, api-conventions.mdc, test-patterns.mdc",
                "",
            ]
        )

    if "windsurf" in cli_tools:
        plan_sections.extend(
            [
                "  🌊 Windsurf Yapılandırması:",
                "",
                "  📄 .windsurfrules (Proje Kuralları)",
                "     ├─ Ne işe yarar: Windsurf'a projenin mimarisini ve kurallarını söyler",
                "     └─ Kullanım: Editör oturumunda sürekli referans edilir",
                "",
                "  📁 .windsurf/ (Windsurf Özel)",
                "     ├─ workspace.json → Proje metadata ve komutlar",
                "     ├─ context.md → Proje context dosyası",
                "     └─ conventions.md → Detaylı kod kuralları ve best practices",
                "",
            ]
        )

    if "zed" in cli_tools:
        plan_sections.extend(
            [
                "  ⚡ Zed Yapılandırması:",
                "",
                "  📄 .zed/settings.json (Zed Ayarları)",
                "     ├─ Ne işe yarar: Zed'in AI assistant ve LSP ayarlarını yapar",
                "     └─ Kullanım: Proje bazlı yapılandırma",
                "",
                "  📄 .zed/context.md (Proje Context)",
                "     ├─ Ne işe yarar: AI'ya proje bağlamı sağlar",
                "     └─ Kullanım: Her oturumda yüklenir",
                "",
                "  📄 .zed/hooks.toml (Zed Hook'ları)",
                "     ├─ Pre-commit: {linter} + test çalıştırır".format(linter=ctx.linter),
                "     └─ On-save: Format on save, trim whitespace",
                "",
            ]
        )

    if "aider" in cli_tools:
        plan_sections.extend(
            [
                "  📟 Aider Yapılandırması:",
                "",
                "  📄 .aider.conf.yaml (Aider Konfigürasyonu)",
                "     ├─ Ne işe yarar: Terminal AI için repo yapılandırması",
                "     ├─ Commit prompt: Detailed conventional commits",
                "     └─ Tools: bash, format, lint, test",
                "",
                "  📄 .aider.context.md (Proje Context)",
                "     └─ Ne işe yarar: AI'ya projenin teknik detaylarını sağlar",
                "",
            ]
        )

    if "bolt" in cli_tools:
        plan_sections.extend(
            [
                "  🔩 Bolt.new Yapılandırması:",
                "",
                "  📄 .bolt/workspace.json (Bolt Workspace)",
                "     ├─ Ne işe yarar: Bolt sandbox yapılandırması",
                "     └─ AI model: Claude Sonnet 4",
                "",
                "  📄 .bolt/setup.md (Proje Setup)",
                "     └─ Ne işe yarar: Dev server, build, test komutları",
                "",
                "  📄 .bolt/prompts.md (AI Prompt Şablonları)",
                "     ├─ New Feature → Şablon",
                "     ├─ Bug Fix → Şablon",
                "     ├─ Refactor → Şablon",
                "     └─ Run Tests → Şablon",
                "",
            ]
        )

    if "codex" in cli_tools:
        plan_sections.extend(
            [
                "  🔷 Codex Yapılandırması:",
                "",
                "  📄 .openai/instructions.md (Codex Talimatları)",
                "     └─ Ne işe yarar: Codex'e proje talimatlarını verir",
                "",
            ]
        )

    if "copilot" in cli_tools:
        plan_sections.extend(
            [
                "  🐙 Copilot Yapılandırması:",
                "",
                "  📄 .github/copilot-instructions.md (Copilot Talimatları)",
                "     └─ Ne işe yarar: GitHub Copilot'a proje kurallarını söyler",
                "",
            ]
        )

    # Project Scaffold
    plan_sections.extend(
        [
            "  📦 Proje Scaffold:",
            "     ├─ .gitignore → Git ignore kuralları",
            "     ├─ README.md → Proje dokümantasyonu (purpose, setup, usage)",
            "     └─ (Tech stack'e göre config dosyaları)",
            "",
        ]
    )

    # Deterministik vs Probabilistik
    plan_sections.append("┌" + "─" * 68 + "┐")
    plan_sections.append("│ 🎯 DETERMİNİSTİK vs PROBABİLİSTİK                           │")
    plan_sections.append("└" + "─" * 68 + "┘")
    plan_sections.append("")
    plan_sections.append("  🔒 DETERMİNİSTİK (Her zaman çalışır, güvenlik + zorunlu):")
    plan_sections.append("     • CLAUDE.md → Proje konvansiyonları (max 200 satır)")
    plan_sections.append("     • Hooks → Otomatik çalışan güvenlik kontrolleri")
    plan_sections.append("     • .cursorrules → IDE kuralları")
    plan_sections.append("")
    plan_sections.append("  🎲 PROBABİLİSTİK (Bağlamsal, elle çağrılır):")
    plan_sections.append("     • Skills → /commit, /deploy gibi slash komutları")
    plan_sections.append("     • Agents → Özel görevli subagent'lar")
    plan_sections.append("     • Context files → Ek bilgi dosyaları")
    plan_sections.append("")

    # Skills to Create
    plan_sections.append("┌" + "─" * 68 + "┐")
    plan_sections.append("│ 🛠️ OLUŞTURULACAK SKILL'LER                                     │")
    plan_sections.append("└" + "─" * 68 + "┘")
    plan_sections.append("")

    skills = _determine_skills(ctx)
    for skill in skills:
        plan_sections.append(f"  • /{skill['name']} → {skill['description']}")
    plan_sections.append("")

    # Hooks to Create
    plan_sections.append("┌" + "─" * 68 + "┐")
    plan_sections.append("│ 🔗 OLUŞTURULACAK HOOK'LAR                                    │")
    plan_sections.append("└" + "─" * 68 + "┘")
    plan_sections.append("")
    plan_sections.append("  🔒 Güvenlik Hook'ları:")
    plan_sections.append(
        "     • PreToolUse → Destructive komutları blokla (rm -rf, git push --force)"
    )
    plan_sections.append("     • Secret Scan → API key sızmasını kontrol et")
    plan_sections.append("")
    plan_sections.append("  ⚡ Otomasyon Hook'ları:")
    plan_sections.append(f"     • PostToolUse → {ctx.formatter} on save")
    plan_sections.append(f"     • PostToolUse → {ctx.linter} after edit")
    plan_sections.append("     • SessionStop → Test suite before end")
    plan_sections.append("")

    plan_text = "\n".join(plan_sections)
    console.print(
        Panel(plan_text, title="📋 Detaylı Proje Planı", border_style="cyan", expand=False)
    )
    return plan_text


def confirm_plan(console: Console) -> bool:
    """Ask user to confirm the plan with detailed explanation."""
    console.print("")
    console.print("─" * 70)
    console.print(Text("🤔 Bu planı onaylıyor musunuz?", style="bold cyan"))
    console.print(Text("   • 'E' / 'evet' → Setup başlar", style="dim"))
    console.print(Text("   • 'H' / 'hayır' → İptal edilir", style="dim"))
    console.print(Text("   • Değişiklik için Ctrl+C ile yeniden başlatabilirsiniz", style="dim"))
    console.print("─" * 70)
    return Confirm.ask("\n[bold cyan]Planı onaylıyor musunuz?[/] [dim](E/h)[/]", default=False)


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
    elif ctx.project_type == "data-pipeline":
        lines.extend(
            [
                "├── scrapers/",
                "│   └── (data collectors)",
                "├── intel/",
                "│   └── (analysis & intelligence)",
                "├── data/",
                "│   ├── raw/",
                "│   └── processed/",
                "├── reports/",
                "│   └── (output reports)",
                "├── tests/",
                "│   └── (test files)",
                "├── .env.example",
            ]
        )
    elif ctx.project_type == "ml-model":
        lines.extend(
            [
                "├── src/",
                "│   ├── data/",
                "│   ├── models/",
                "│   └── utils/",
                "├── notebooks/",
                "├── experiments/",
                "├── tests/",
                "├── data/",
                "│   ├── raw/",
                "│   └── processed/",
            ]
        )

    lines.append("└── (config files)")

    # Add indentation
    indented = []
    for line in lines:
        if line.endswith("/"):
            indented.append(line)
        elif line.startswith("├──") or line.startswith("└──"):
            indented.append(line)
        elif line.startswith("│"):
            indented.append(line)
        else:
            indented.append(line)

    return "\n".join(indented)


def _determine_skills(ctx: ProjectContext) -> list[dict]:
    """Determine which skills to create."""
    skills = [
        {
            "name": "commit-message",
            "description": "Git diff'ten conventional commit mesajı üretir",
        },
        {
            "name": "pr-review",
            "description": "PR'leri team standartlarına göre review eder",
        },
        {
            "name": "deploy",
            "description": f"{ctx.hosting or 'hedef'}'a pre-deploy checklist ile deploy eder",
        },
        {
            "name": "security-review",
            "description": "Kodda güvenlik açıklarını tarar",
        },
        {
            "name": "refactor",
            "description": "Davranışı koruyarak kod iyileştirmeleri önerir",
        },
    ]

    if ctx.auth_needed:
        skills.append(
            {
                "name": "auth-conventions",
                "description": f"{ctx.auth_method} ile auth pattern'leri",
            }
        )
    if ctx.project_type == "api":
        skills.append(
            {
                "name": "api-conventions",
                "description": "REST API design patterns ve endpoint naming",
            }
        )
    if ctx.test_level != "none":
        skills.append(
            {
                "name": "test-patterns",
                "description": f"{ctx.test_framework} ile test yazma kalıpları",
            }
        )

    return skills
