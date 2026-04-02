"""Question bank for discovery phase — Turkish and English with intelligent defaults."""

import platform
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Supported AI tools
AI_TOOLS = [
    "claude-code",
    "cursor",
    "windsurf",
    "zed",
    "aider",
    "bolt",
    "codex",
    "copilot",
]


def get_prompts(lang: str = "tr") -> dict:
    """Get prompts dictionary in specified language with rich metadata."""
    raw_prompts = _TR_PROMPTS if lang == "tr" else _EN_PROMPTS
    return _normalize_prompts(raw_prompts)


def _normalize_prompts(prompts: dict) -> dict:
    """Normalize prompts to always have question, description, hint, placeholder."""
    normalized = {}
    for key, value in prompts.items():
        if isinstance(value, str):
            normalized[key] = {
                "question": value,
                "description": "",
                "hint": "",
                "placeholder": "",
            }
        else:
            normalized[key] = value
    return normalized


def get_prompt_value(prompts: dict, key: str, field: str, default: str = "") -> str:
    """Get a specific field from a prompt, with fallback to default."""
    prompt = prompts.get(key, {})
    if isinstance(prompt, str):
        return default
    return prompt.get(field, default)


def get_prompt_question(prompts: dict, key: str, default: str = "") -> str:
    """Get question text from prompt."""
    return get_prompt_value(prompts, key, "question", default)


def get_prompt_hint(prompts: dict, key: str, default: str = "") -> str:
    """Get hint text from prompt with variable substitution."""
    hint = get_prompt_value(prompts, key, "hint", default)
    return hint


def get_prompt_placeholder(prompts: dict, key: str, default: str = "") -> str:
    """Get placeholder text from prompt."""
    return get_prompt_value(prompts, key, "placeholder", default)


def detect_platform() -> str:
    """Auto-detect the current platform/terminal."""
    system = platform.system()

    # Check WSL
    if "WSL" in os.environ.get("WSL_DISTRO_NAME", ""):
        return "wsl"

    if system == "Windows":
        return "windows-powershell"
    elif system == "Darwin":
        return "macos"
    else:
        return "linux"


def detect_ai_tool() -> str | None:
    """Auto-detect which AI coding tool is configured in the project.

    Checks in priority order (project-specific files first).
    """
    current_dir = Path(".")

    # File to tool mapping (priority order)
    checks = [
        (".cursorrules", "cursor"),
        (".cursor/rules", "cursor"),
        (".claude/settings.json", "claude-code"),
        (".claude/CLAUDE.md", "claude-code"),
        (".windsurfrules", "windsurf"),
        (".aider.conf.yaml", "aider"),
        (".bolt/workspace.json", "bolt"),
        (".openai/instructions.md", "codex"),
        (".github/copilot-instructions.md", "copilot"),
        (".zed/settings.json", "zed"),
    ]

    for file_path, tool in checks:
        if Path(file_path).exists():
            return tool

    return None


def detect_installed_ai_tools() -> list[str]:
    """Check system for installed AI coding tools (CLI binaries)."""
    tools = []

    # Binary to tool mapping
    binaries = {
        "claude": "claude-code",
        "cursor": "cursor",
        "windsurf": "windsurf",
        "zed": "zed",
        "aider": "aider",
    }

    for binary, tool in binaries.items():
        if shutil.which(binary):
            tools.append(tool)

    return tools


# Cache file location and management
def _get_cache_dir() -> Path:
    cache_dir = Path.home() / ".vcsx" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _is_cache_valid(cache_file: Path, max_age_days: int = 7) -> bool:
    """Check if cache is valid (not older than max_age_days)."""
    if not cache_file.exists():
        return False
    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    return datetime.now() - mtime < timedelta(days=max_age_days)


def _load_best_practices() -> dict:
    """Load best practices from cache or fetch fresh."""
    cache_file = _get_cache_dir() / "best_practices.json"

    # Return cached if valid
    if _is_cache_valid(cache_file):
        import json

        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except:
            pass

    # Return default practices while async fetch would happen
    return _DEFAULT_PRACTICES


# Default practices (fallback when offline)
_DEFAULT_PRACTICES = {
    "python": {
        "cli": {
            "recurring_tasks": [
                "run-cli - Test CLI komutlarını çalıştır",
                "build-exe - PyInstaller ile exe oluştur",
                "package-distribution - PyPI için paketle",
                "cli-testing - CLI argüman testleri",
            ],
            "automations": [
                "auto-format on save",
                "run tests before commit",
                "run ruff check on save",
                "type-check with mypy",
            ],
            "forbidden_actions": [
                "rm -rf",
                "git push --force",
                "DROP TABLE",
                "deleting production data",
                "git add .",  # from user input
            ],
        },
        "api": {
            "recurring_tasks": [
                "api-test - API endpoint testleri",
                "db-migrate - Veritabanı migrasyonları",
                "seed-data - Test verisi oluştur",
                "openapi-doc - OpenAPI dokümantasyon",
            ],
            "automations": [
                "auto-format on save",
                "run tests before commit",
                "run ruff check on save",
                "openapi-validation on push",
            ],
            "forbidden_actions": [
                "rm -rf",
                "git push --force",
                "DROP TABLE",
                "deleting production data",
            ],
        },
        "web": {
            "recurring_tasks": [
                "build-prod - Production build",
                "static-analysis - Static code analysis",
                "lighthouse-audit - Performance audit",
                "bundle-analyze - Bundle size analysis",
            ],
            "automations": [
                "auto-format on save",
                "run tests before commit",
                "type-check on save",
                "lint on push",
            ],
            "forbidden_actions": [
                "rm -rf",
                "git push --force",
            ],
        },
    },
    "typescript": {
        "web": {
            "recurring_tasks": [
                "build-prod - Production build",
                "deploy-vercel - Vercel deploy",
                "lighthouse-audit - Performance audit",
                "bundle-analyze - Bundle size analysis",
            ],
            "automations": [
                "auto-format on save",
                "run tests before commit",
                "type-check on save",
                "lint on push",
            ],
            "forbidden_actions": [
                "rm -rf",
                "git push --force",
            ],
        },
    },
    "rust": {
        "cli": {
            "recurring_tasks": [
                "build-release - Release build",
                "cross-compile - Cross platform compile",
                "cargo-audit - Security audit",
                "doc-gen - Documentation generate",
            ],
            "automations": [
                "auto-format on save (cargo fmt)",
                "run tests before commit",
                "clippy check on save",
                "cargo check on push",
            ],
            "forbidden_actions": [
                "rm -rf",
                "git push --force",
            ],
        },
    },
    "go": {
        "api": {
            "recurring_tasks": [
                "go-test - Testleri çalıştır",
                "go-vet - Vet kontrolü",
                "docker-build - Docker image oluştur",
                "k8s-deploy - Kubernetes deploy",
            ],
            "automations": [
                "auto-format on save (gofmt)",
                "run tests before commit",
                "go vet on save",
                "lint on push",
            ],
            "forbidden_actions": [
                "rm -rf",
                "git push --force",
            ],
        },
    },
}


def get_intelligent_defaults(language: str, project_type: str) -> dict:
    """Get intelligent default values based on language and project type."""
    practices = _load_best_practices()

    lang_practices = practices.get(language.lower(), {})
    type_practices = lang_practices.get(project_type.lower(), {})

    return {
        "recurring_tasks": ", ".join(type_practices.get("recurring_tasks", [])),
        "automations": ", ".join(type_practices.get("automations", [])),
        "forbidden_actions": ", ".join(
            type_practices.get(
                "forbidden_actions",
                [
                    "rm -rf",
                    "git push --force",
                    "DROP TABLE",
                    "deleting production data",
                ],
            )
        ),
    }


# Turkish prompts
_TR_PROMPTS = {
    "welcome": """
=============================================================
   Vibe Coding Setup Expert - Keşif Aşaması (v3.3)
=============================================================
   Projeni derinlemesine anlayarak sana özel bir AI 
   kodlama ortamı kuracağım.
   
   📌 Süreç: 3 tur + detaylı plan onayı
   🎯 Amaç: Sadece yapılandırma değil, projenin 
            başarısını destekleyecek akıllı bir ortam
=============================================================
""",
    # Phase 0: AI Tool & Platform
    "ai_tool": {
        "question": "AI Coding Tool",
        "description": "Hangisini kullanıyorsun?",
        "hint": "Otomatik algılanan: {default}. Değiştirmek için yaz.",
        "examples": ["claude-code", "cursor", "windsurf", "zed", "aider", "bolt"],
    },
    "platform": {
        "question": "Platform/Terminal",
        "description": "Hangi ortamda çalışıyorsun?",
        "hint": "Otomatik algılanan: {default}",
        "examples": ["windows-powershell", "macos", "linux", "wsl"],
    },
    # Phase 1: Project Foundation (EN ÖNEMLİ)
    "purpose": {
        "question": "Projenin Amacı",
        "description": "Bu proje ile neyi başarmak istiyorsun?",
        "hint": "Örn: Kullanıcıların faturalarını otomatik yönetmesini sağlamak",
        "placeholder": "Projenin temel amacını 1-2 cümleyle anlat...",
        "required": True,
    },
    "problem": {
        "question": "Çözülen Problem",
        "description": "Bu proje hangi sorunu çözüyor?",
        "hint": "Mevcut çözümlerdeki eksiklikleri belirt. Örn: Fatura takibi manuel yapılıyor, zaman kaybı yaşanıyor",
        "placeholder": "Kullanıcıların yaşadığı sorunları anlat...",
        "required": True,
    },
    "project_name": {
        "question": "Proje Adı",
        "description": "Proje klasörünün adı ne olacak?",
        "hint": "Küçük harfle, tire ile. Örn: invoice-manager",
        "placeholder": "my-awesome-project",
        "validation": "^[a-z0-9-]+$",
        "required": True,
    },
    "description": {
        "question": "Kısa Açıklama",
        "description": "Projenin ne yaptığını özetle",
        "hint": "Tek cümle. Örn: Kullanıcıların faturalarını tarayıp dijital ortama aktaran CLI aracı",
        "placeholder": "Projenin ne yaptığını özetle...",
    },
    # Phase 1b: Tech Stack & Architecture
    "tech_stack": {
        "question": "Tech Stack",
        "description": "Hangi teknolojileri kullanacaksın?",
        "hint": "Örn: Python, FastAPI, PostgreSQL, Redis, Docker",
        "placeholder": "Python, FastAPI, PostgreSQL",
        "examples": [
            "Python + FastAPI + PostgreSQL",
            "TypeScript + Next.js + Tailwind",
            "Go + Chi + PostgreSQL",
            "Rust + Actix + SQLite",
        ],
    },
    "project_type": {
        "question": "Proje Tipi",
        "description": "Ne tür bir uygulama?",
        "hint": "Bu seçim dosya yapısını belirler",
        "options": {
            "web": "Web uygulaması (frontend + backend)",
            "api": "Sadece API servisi",
            "cli": "Komut satırı aracı",
            "mobile": "Mobil uygulama",
            "desktop": "Masaüstü uygulaması",
            "library": "Kütüphane/paket",
            "other": "Diğer",
        },
    },
    # Phase 2: User Stories (DETAYLI)
    "user_stories": {
        "question": "User Stories",
        "description": "Kullanıcı hikayelerini detaylı yaz",
        "hint": "Format: 'Kullanıcı olarak, [eylem], böylece [fayda] sağlarım'",
        "placeholder": """Örnek format:
Kullanıcı olarak, faturaları PNG olarak yükleyebilmeliyim, böylece manuel veri girişi yapmak zorunda kalmam.
Kullanıcı olarak, tüm faturalarımı tek bir panelden görebilmeliyim, böylece ödeme takibi kolaylaşır.
Kullanıcı olarak, faturaları tarihe göre filtreleyebilmeliyim, böylece dönem bazlı raporlar alabilirim.""",
        "required": False,
    },
    "success_criteria": {
        "question": "Başarı Kriterleri",
        "description": "Proje başarılı sayılırsa ne olmalı?",
        "hint": "Ölçülebilir metrikler belirt",
        "placeholder": """Örnek:
- İlk 100 kullanıcıya ulaşılması
- Fatura işleme süresinin %50 azalması
- Kullanıcı memnuniyetinin 4/5 olması
- API yanıt süresinin 200ms altında olması""",
        "required": False,
    },
    "mvp_features": {
        "question": "MVP Kritik Özellikler",
        "description": "İlk versiyonda olması gereken 3 temel özellik",
        "hint": "Virgülle ayır. Örn: Kullanıcı kaydı, fatura yükleme, otomatik kategorize",
        "placeholder": "Özellik 1, Özellik 2, Özellik 3",
    },
    "target_users": {
        "question": "Hedef Kullanıcılar",
        "description": "Kimler kullanacak?",
        "hint": "Kimlerin problemi çözülüyor?",
        "placeholder": "Örn: KOBİ sahipleri, Muhasebeciler, Freelancerlar",
    },
    # Phase 3: Technical Details
    "hosting": {
        "question": "Hosting/Deployment",
        "description": "Nereye deploy edeceksin?",
        "hint": "Boş bırakırsan sonra karar veririz",
        "placeholder": "Vercel, AWS, Railway, Render, Self-hosted...",
    },
    "auth_needed": {
        "question": "Authentication",
        "description": "Kullanıcı girişi gerekli mi?",
        "type": "confirm",
    },
    "auth_method": {
        "question": "Auth Yöntemi",
        "description": "Nasıl kimlik doğrulama?",
        "hint": "Proje tipine göre önerilir",
        "placeholder": "JWT, OAuth2 (Google/GitHub), Clerk, NextAuth, Supabase Auth...",
    },
    "external_services": {
        "question": "External Servisler",
        "description": "Hangi 3. party servisler kullanılacak?",
        "hint": "Boş bırakabilirsin",
        "placeholder": "Örn: Stripe (ödeme), OpenAI (AI), SendGrid (email), Sentry (hata izleme)...",
    },
    "monorepo": {
        "question": "Monorepo",
        "description": "Tek repo içinde multiple projeler mi?",
        "hint": "Frontend + Backend aynı repo",
        "type": "confirm",
    },
    # Phase 4: Development Standards
    "test_level": {
        "question": "Test Seviyesi",
        "description": "Ne kadar test istiyorsun?",
        "options": {
            "none": "Test yok (hızlı başlangıç)",
            "unit": "Unit testler (fonksiyon bazlı)",
            "integration": "Integration testler (API/DB dahil)",
            "full": "Tam test (unit + integration + e2e)",
        },
    },
    "test_framework": {
        "question": "Test Framework",
        "description": "Hangi test kütüphanesi?",
        "hint": "Dil ve projeye göre önerilir",
    },
    "ci_cd": {
        "question": "CI/CD Pipeline",
        "description": "Otomatik deployment istiyor musun?",
        "hint": "GitHub Actions ile otomatik test + deploy",
        "type": "confirm",
    },
    "code_style": {
        "question": "Kod Stili",
        "description": "Özel kod stili kuralları var mı?",
        "hint": "Boş bırakabilirsin, varsa yaz",
        "placeholder": "Örn: Airbnb style, Google style, PEP 8...",
    },
    "formatter": {
        "question": "Formatter",
        "description": "Kod formatlama aracı",
        "hint": "Otomatik algılanan: {default}",
    },
    "linter": {
        "question": "Linter",
        "description": "Kod linting aracı",
        "hint": "Otomatik algılanan: {default}",
    },
    # Claude Code Specific
    "recurring_tasks": {
        "question": "Sık Tekrarlanan İşler",
        "description": "Hangileri sıklıkla tekrarlanıyor? (Skill olacak)",
        "hint": "Skill olarak otomatikleştirilir",
        "placeholder": "Örn: commit, test, deploy, security-review...",
    },
    "forbidden_actions": {
        "question": "Yasaklı Eylemler",
        "description": "Kesinlikle yapılmaması gerekenler (Hook ile bloklanacak)",
        "hint": "Otomatik engellenir",
        "placeholder": "rm -rf, git push --force, DROP TABLE...",
    },
    "automations": {
        "question": "Otomasyonlar",
        "description": "Otomatik yapılmasını istediklerin",
        "hint": "Her dosya kaydında otomatik çalışır",
        "placeholder": "auto-format on save, run tests before commit...",
    },
}


# English prompts
_EN_PROMPTS = {
    "welcome": """
=============================================================
   Vibe Coding Setup Expert - Discovery Phase (v3.3)
=============================================================
   I'll deeply understand your project and create a custom
   AI coding environment tailored to your success.
   
   📌 Process: 3 rounds + detailed plan approval
   🎯 Goal: Not just config, but an intelligent environment
            that supports your project's success
=============================================================
""",
    # Phase 0: AI Tool & Platform
    "ai_tool": {
        "question": "AI Coding Tool",
        "description": "Which one are you using?",
        "hint": "Auto-detected: {default}. Change if needed.",
        "examples": ["claude-code", "cursor", "windsurf", "zed", "aider", "bolt"],
    },
    "platform": {
        "question": "Platform/Terminal",
        "description": "What environment do you work in?",
        "hint": "Auto-detected: {default}",
        "examples": ["windows-powershell", "macos", "linux", "wsl"],
    },
    # Phase 1: Project Foundation (MOST IMPORTANT)
    "purpose": {
        "question": "Project Purpose",
        "description": "What do you aim to achieve with this project?",
        "hint": "Example: Enable users to manage their invoices automatically",
        "placeholder": "Describe the fundamental goal in 1-2 sentences...",
        "required": True,
    },
    "problem": {
        "question": "Problem Solved",
        "description": "What problem does this project solve?",
        "hint": "Identify gaps in current solutions. Example: Invoice tracking is manual, time-consuming",
        "placeholder": "Describe the user problems being solved...",
        "required": True,
    },
    "project_name": {
        "question": "Project Name",
        "description": "What will the project folder be named?",
        "hint": "Lowercase with hyphens. Example: invoice-manager",
        "placeholder": "my-awesome-project",
        "validation": "^[a-z0-9-]+$",
        "required": True,
    },
    "description": {
        "question": "Short Description",
        "description": "Summarize what the project does",
        "hint": "One sentence. Example: CLI tool that scans invoices and digitizes them",
        "placeholder": "Summarize what the project does...",
    },
    # Phase 1b: Tech Stack & Architecture
    "tech_stack": {
        "question": "Tech Stack",
        "description": "What technologies will you use?",
        "hint": "Example: Python, FastAPI, PostgreSQL, Redis, Docker",
        "placeholder": "Python, FastAPI, PostgreSQL",
        "examples": [
            "Python + FastAPI + PostgreSQL",
            "TypeScript + Next.js + Tailwind",
            "Go + Chi + PostgreSQL",
            "Rust + Actix + SQLite",
        ],
    },
    "project_type": {
        "question": "Project Type",
        "description": "What kind of application?",
        "hint": "This determines the file structure",
        "options": {
            "web": "Web application (frontend + backend)",
            "api": "API service only",
            "cli": "Command-line tool",
            "mobile": "Mobile application",
            "desktop": "Desktop application",
            "library": "Library/package",
            "other": "Other",
        },
    },
    # Phase 2: User Stories (DETAILED)
    "user_stories": {
        "question": "User Stories",
        "description": "Write detailed user stories",
        "hint": "Format: 'As a user, I can [action], so that [benefit]'",
        "placeholder": """Example format:
As a user, I can upload invoices as PNG, so I don't have to manually enter data.
As a user, I can see all my invoices in a single panel, so tracking payments is easier.
As a user, I can filter invoices by date, so I can generate period-based reports.""",
        "required": False,
    },
    "success_criteria": {
        "question": "Success Criteria",
        "description": "What constitutes project success?",
        "hint": "Specify measurable metrics",
        "placeholder": """Example:
- Reach first 100 users
- Reduce invoice processing time by 50%
- Achieve user satisfaction of 4/5
- API response time under 200ms""",
        "required": False,
    },
    "mvp_features": {
        "question": "MVP Critical Features",
        "description": "The 3 essential features for the first version",
        "hint": "Comma-separated. Example: User registration, invoice upload, auto-categorize",
        "placeholder": "Feature 1, Feature 2, Feature 3",
    },
    "target_users": {
        "question": "Target Users",
        "description": "Who will use this?",
        "hint": "Whose problem are we solving?",
        "placeholder": "Example: SMB owners, Accountants, Freelancers",
    },
    # Phase 3: Technical Details
    "hosting": {
        "question": "Hosting/Deployment",
        "description": "Where will you deploy?",
        "hint": "Leave empty to decide later",
        "placeholder": "Vercel, AWS, Railway, Render, Self-hosted...",
    },
    "auth_needed": {
        "question": "Authentication",
        "description": "Is user login required?",
        "type": "confirm",
    },
    "auth_method": {
        "question": "Auth Method",
        "description": "What kind of authentication?",
        "hint": "Recommended based on project type",
        "placeholder": "JWT, OAuth2 (Google/GitHub), Clerk, NextAuth, Supabase Auth...",
    },
    "external_services": {
        "question": "External Services",
        "description": "Which 3rd party services will be used?",
        "hint": "Can leave empty",
        "placeholder": "Example: Stripe (payments), OpenAI (AI), SendGrid (email), Sentry (error tracking)...",
    },
    "monorepo": {
        "question": "Monorepo",
        "description": "Multiple projects in single repo?",
        "hint": "Frontend + Backend in same repo",
        "type": "confirm",
    },
    # Phase 4: Development Standards
    "test_level": {
        "question": "Test Level",
        "description": "How much testing do you want?",
        "options": {
            "none": "No tests (fast start)",
            "unit": "Unit tests (function-level)",
            "integration": "Integration tests (including API/DB)",
            "full": "Full tests (unit + integration + e2e)",
        },
    },
    "test_framework": {
        "question": "Test Framework",
        "description": "Which testing library?",
        "hint": "Recommended based on language and project",
    },
    "ci_cd": {
        "question": "CI/CD Pipeline",
        "description": "Do you want automatic deployment?",
        "hint": "Automatic test + deploy via GitHub Actions",
        "type": "confirm",
    },
    "code_style": {
        "question": "Code Style",
        "description": "Any specific code style rules?",
        "hint": "Can leave empty, specify if needed",
        "placeholder": "Example: Airbnb style, Google style, PEP 8...",
    },
    "formatter": {
        "question": "Formatter",
        "description": "Code formatting tool",
        "hint": "Auto-detected: {default}",
    },
    "linter": {
        "question": "Linter",
        "description": "Code linting tool",
        "hint": "Auto-detected: {default}",
    },
    # Claude Code Specific
    "recurring_tasks": {
        "question": "Frequently Recurring Tasks",
        "description": "Which tasks happen often? (Will become skills)",
        "hint": "Automated as skills",
        "placeholder": "Example: commit, test, deploy, security-review...",
    },
    "forbidden_actions": {
        "question": "Forbidden Actions",
        "description": "Actions that should never happen (Will be blocked by hooks)",
        "hint": "Automatically blocked",
        "placeholder": "rm -rf, git push --force, DROP TABLE...",
    },
    "automations": {
        "question": "Automations",
        "description": "Things you want automated",
        "hint": "Runs automatically on file save",
        "placeholder": "auto-format on save, run tests before commit...",
    },
}
