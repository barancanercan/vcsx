"""Question bank for discovery phase — Turkish and English."""


def get_prompts(lang: str = "tr") -> dict:
    """Get prompts dictionary in specified language."""
    return _TR_PROMPTS if lang == "tr" else _EN_PROMPTS


_TR_PROMPTS = {
    "welcome": """[bold cyan]
╔══════════════════════════════════════════════════════════╗
║   🧠 Vibe Coding Setup Expert — Keşif Aşaması           ║
║                                                          ║
║   Projeni anlayarak sana özel bir AI kodlama ortamı      ║
║   kuracağım. Maksimum 3 tur soru soracağım.              ║
╚══════════════════════════════════════════════════════════╝
[/bold cyan]""",
    "project_name": "Proje adı",
    "description": "Proje açıklaması (kısa)",
    "project_type": "Proje tipi",
    "tech_stack": "Tech stack (örn: Python, FastAPI, PostgreSQL)",
    "mvp_features": "MVP'deki en kritik 3 özellik (virgülle ayır)",
    "target_users": "Hedef kullanıcılar",
    "hosting": "Hosting/deployment hedefi (örn: Vercel, AWS, Railway)",
    "auth_needed": "Auth gerekiyor mu?",
    "auth_method": "Auth yöntemi (örn: JWT, OAuth, Clerk)",
    "external_services": "External servisler (ödeme, AI, email, analytics)",
    "monorepo": "Monorepo mu?",
    "test_level": "Test seviyesi",
    "test_framework": "Test framework",
    "ci_cd": "CI/CD pipeline istiyor musun?",
    "code_style": "Kod stili kuralları (varsa)",
    "formatter": "Formatter",
    "linter": "Linter",
    "recurring_tasks": "Sık tekrarlanan işler (skill olacak)",
    "forbidden_actions": "Kesinlikle yapılmaması gerekenler (hook ile bloklanacak)",
    "automations": "Otomatik olmasını istediklerin (hook ile yapılacak)",
}


_EN_PROMPTS = {
    "welcome": """[bold cyan]
╔══════════════════════════════════════════════════════════╗
║   🧠 Vibe Coding Setup Expert — Discovery Phase         ║
║                                                          ║
║   I'll understand your project and create a custom       ║
║   AI coding environment. Max 3 rounds of questions.      ║
╚══════════════════════════════════════════════════════════╝
[/bold cyan]""",
    "project_name": "Project name",
    "description": "Project description (short)",
    "project_type": "Project type",
    "tech_stack": "Tech stack (e.g., Python, FastAPI, PostgreSQL)",
    "mvp_features": "Top 3 critical MVP features (comma-separated)",
    "target_users": "Target users",
    "hosting": "Hosting/deployment target (e.g., Vercel, AWS, Railway)",
    "auth_needed": "Is auth required?",
    "auth_method": "Auth method (e.g., JWT, OAuth, Clerk)",
    "external_services": "External services (payment, AI, email, analytics)",
    "monorepo": "Is it a monorepo?",
    "test_level": "Test level",
    "test_framework": "Test framework",
    "ci_cd": "Do you want a CI/CD pipeline?",
    "code_style": "Code style rules (if any)",
    "formatter": "Formatter",
    "linter": "Linter",
    "recurring_tasks": "Frequently recurring tasks (will become skills)",
    "forbidden_actions": "Absolutely forbidden actions (will be blocked by hooks)",
    "automations": "Things you want automated (will be done by hooks)",
}
