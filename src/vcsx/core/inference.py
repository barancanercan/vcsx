"""Smart inference engine — derives language, framework, tools from tech stack."""

STACK_MAP = {
    "typescript": {
        "keywords": [
            "react",
            "vue",
            "svelte",
            "node",
            "express",
            "next",
            "typescript",
            "javascript",
            "angular",
            "nestjs",
            "fastify",
            "hono",
            "remix",
            "astro",
        ],
        "framework_map": {
            "next": "Next.js",
            "react": "React",
            "vue": "Vue",
            "svelte": "Svelte",
            "angular": "Angular",
            "express": "Express",
            "nestjs": "NestJS",
            "fastify": "Fastify",
            "hono": "Hono",
            "remix": "Remix",
            "astro": "Astro",
        },
        "test_framework": "vitest",
        "formatter": "prettier",
        "linter": "eslint",
    },
    "python": {
        "keywords": [
            "python",
            "django",
            "flask",
            "fastapi",
            "pyramid",
            "tornado",
            "starlette",
            "celery",
            "sqlalchemy",
            "pandas",
            "numpy",
            "scrapy",
            "pytest",
        ],
        "framework_map": {
            "django": "Django",
            "flask": "Flask",
            "fastapi": "FastAPI",
            "pyramid": "Pyramid",
            "tornado": "Tornado",
            "starlette": "Starlette",
        },
        "test_framework": "pytest",
        "formatter": "ruff format",
        "linter": "ruff check",
    },
    "go": {
        "keywords": ["go", "gin", "echo", "fiber", "chi", "gorm", "cobra", "viper"],
        "framework_map": {"gin": "Gin", "echo": "Echo", "fiber": "Fiber", "chi": "Chi"},
        "test_framework": "go test",
        "formatter": "gofmt",
        "linter": "golangci-lint",
    },
    "rust": {
        "keywords": ["rust", "actix", "rocket", "axum", "tokio", "serde", "diesel"],
        "framework_map": {"actix": "Actix", "rocket": "Rocket", "axum": "Axum"},
        "test_framework": "cargo test",
        "formatter": "rustfmt",
        "linter": "clippy",
    },
    "java": {
        "keywords": [
            "java",
            "spring",
            "spring boot",
            "quarkus",
            "micronaut",
            "hibernate",
            "maven",
            "gradle",
        ],
        "framework_map": {
            "spring": "Spring Boot",
            "quarkus": "Quarkus",
            "micronaut": "Micronaut",
        },
        "test_framework": "junit",
        "formatter": "google-java-format",
        "linter": "checkstyle",
    },
}


def infer_language(tech_stack: str) -> str:
    """Infer primary language from tech stack description."""
    if not tech_stack:
        return "typescript"
    stack_lower = tech_stack.lower()
    for lang, config in STACK_MAP.items():
        if any(kw in stack_lower for kw in config["keywords"]):
            return lang
    return "typescript"


def infer_framework(tech_stack: str) -> str:
    """Infer primary framework from tech stack."""
    if not tech_stack:
        return ""
    stack_lower = tech_stack.lower()
    lang = infer_language(tech_stack)
    framework_map = STACK_MAP[lang]["framework_map"]
    for key, fw in framework_map.items():
        if key in stack_lower:
            return fw
    return ""


def infer_test_framework(language: str) -> str:
    """Infer test framework from language."""
    for lang, config in STACK_MAP.items():
        if lang == language:
            return config["test_framework"]
    return "pytest"


def infer_formatter(language: str) -> str:
    """Infer formatter from language."""
    for lang, config in STACK_MAP.items():
        if lang == language:
            return config["formatter"]
    return "prettier"


def infer_linter(language: str) -> str:
    """Infer linter from language."""
    for lang, config in STACK_MAP.items():
        if lang == language:
            return config["linter"]
    return "eslint"
