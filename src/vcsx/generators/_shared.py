"""Shared helper utilities used across all generators.

These functions centralize common logic (command inference, style rules)
to avoid copy-paste duplication across generator modules.
"""

from vcsx.core.context import ProjectContext
from vcsx.core.inference import infer_formatter, infer_linter, infer_test_framework


def get_setup_cmd(ctx: ProjectContext) -> str:
    """Return the project setup/install command based on language."""
    lang = (ctx.language or "").lower()
    (ctx.framework or "").lower()
    tech = (ctx.tech_stack or "").lower()

    if lang == "python":
        if "pyproject" in tech or "uv" in tech:
            return "pip install -e '.[dev]'"
        return "pip install -r requirements.txt"
    if lang in ("typescript", "javascript"):
        if "pnpm" in tech:
            return "pnpm install"
        if "yarn" in tech:
            return "yarn install"
        return "npm install"
    if lang == "go":
        return "go mod tidy"
    if lang == "rust":
        return "cargo build"
    if lang == "java":
        return "mvn install"
    return "npm install"


def get_build_cmd(ctx: ProjectContext) -> str:
    """Return the build command based on language."""
    lang = (ctx.language or "").lower()
    tech = (ctx.tech_stack or "").lower()

    if lang == "python":
        return "python -m build"
    if lang in ("typescript", "javascript"):
        if "pnpm" in tech:
            return "pnpm run build"
        return "npm run build"
    if lang == "go":
        return "go build ./..."
    if lang == "rust":
        return "cargo build --release"
    if lang == "java":
        return "mvn package"
    return "npm run build"


def get_dev_cmd(ctx: ProjectContext) -> str:
    """Return the development server command."""
    lang = (ctx.language or "").lower()
    framework = (ctx.framework or "").lower()
    tech = (ctx.tech_stack or "").lower()

    if lang == "python":
        if "fastapi" in framework:
            return "uvicorn main:app --reload"
        if "flask" in framework:
            return "flask run --debug"
        if "django" in framework:
            return "python manage.py runserver"
        return "python main.py"
    if lang in ("typescript", "javascript"):
        if "pnpm" in tech:
            return "pnpm run dev"
        return "npm run dev"
    if lang == "go":
        return "go run main.go"
    if lang == "rust":
        return "cargo run"
    return "npm run dev"


def get_test_cmd(ctx: ProjectContext) -> str:
    """Return the test command based on test framework or language."""
    fw = (ctx.test_framework or "").lower()
    lang = (ctx.language or "").lower()

    if fw == "pytest" or (not fw and lang == "python"):
        return "pytest"
    if fw == "vitest":
        return "npx vitest run"
    if fw == "jest":
        return "npx jest"
    if fw == "go test":
        return "go test ./..."
    if lang == "rust":
        return "cargo test"
    if lang == "java":
        return "mvn test"
    if ctx.test_level == "none":
        return "# No tests configured"

    # Fallback: infer from language
    inferred = infer_test_framework(lang)
    if inferred == "pytest":
        return "pytest"
    if inferred == "vitest":
        return "npx vitest run"
    if inferred == "go test":
        return "go test ./..."
    return "npm test"


def get_lint_cmd(ctx: ProjectContext) -> str:
    """Return the lint command."""
    if ctx.linter:
        return ctx.linter
    return infer_linter(ctx.language or "")


def get_format_cmd(ctx: ProjectContext) -> str:
    """Return the format command."""
    if ctx.formatter:
        return ctx.formatter
    return infer_formatter(ctx.language or "")


def get_style_rules(ctx: ProjectContext) -> list[str]:
    """Return language-specific code style rules."""
    lang = (ctx.language or "").lower()
    rules: list[str] = []

    if lang == "python":
        rules = [
            "- Follow PEP 8 conventions",
            "- Use type hints on all public functions",
            "- `snake_case` for variables and functions",
            "- `PascalCase` for classes",
            "- Docstrings on all public functions and classes",
            "- Prefer `pathlib.Path` over `os.path`",
            "- Use `dataclasses` or `pydantic` for structured data",
        ]
    elif lang == "typescript":
        rules = [
            "- Use TypeScript strict mode",
            "- Prefer `const` over `let`; avoid `var`",
            "- Named exports preferred over default exports",
            "- Explicit return types on all functions",
            "- `camelCase` for variables, `PascalCase` for types/classes",
            "- Use async/await over raw Promises",
        ]
    elif lang == "javascript":
        rules = [
            "- Prefer `const` over `let`; avoid `var`",
            "- Use async/await over raw Promises",
            "- Use JSDoc comments for public APIs",
        ]
    elif lang == "go":
        rules = [
            "- Follow `gofmt` formatting",
            "- Check errors immediately — never ignore",
            "- Package names: lowercase, single word",
            "- Exported names start with uppercase",
            "- Use table-driven tests",
        ]
    elif lang == "rust":
        rules = [
            "- Use `rustfmt` formatting",
            "- Prefer `Result<T, E>` over `panic!` for error handling",
            "- Run `cargo clippy` and fix all warnings",
            "- Write doc comments on public items",
        ]
    elif lang == "java":
        rules = [
            "- Follow Google Java Style Guide",
            "- `camelCase` for variables, `PascalCase` for classes",
            "- Javadoc on all public methods",
        ]
    else:
        rules = ["- Follow language-standard conventions and idioms"]

    # Project-type additions
    if ctx.project_type == "api":
        rules += [
            "- Use correct HTTP status codes (200/201/400/401/403/404/422/500)",
            "- Validate all input at API boundaries",
            "- Return consistent error shapes: `{error, message, code}`",
        ]
    elif ctx.project_type == "data-pipeline":
        rules += [
            "- Process data in chunks — never load full datasets into memory",
            "- Log progress at meaningful intervals",
            "- Make operations idempotent where possible",
        ]

    return rules


def get_commands_block(ctx: ProjectContext, shell: str = "bash") -> str:
    """Return a formatted commands block for a given project context."""
    setup = get_setup_cmd(ctx)
    build = get_build_cmd(ctx)
    test = get_test_cmd(ctx)
    lint = get_lint_cmd(ctx)
    fmt = get_format_cmd(ctx)

    return f"""```{shell}
# Setup
{setup}

# Build
{build}

# Test
{test}

# Lint
{lint}

# Format
{fmt}
```"""
