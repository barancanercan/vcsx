"""GitHub Copilot generator — produces .github/copilot-instructions.md.

GitHub Copilot reads:
- .github/copilot-instructions.md — main project instructions
- .github/instructions/*.instructions.md — scoped instructions (2025+)
Reference: https://docs.github.com/en/copilot/customizing-copilot
"""

from pathlib import Path

from vcsx.core.context import ProjectContext
from vcsx.generators._shared import (
    get_build_cmd,
    get_format_cmd,
    get_lint_cmd,
    get_setup_cmd,
    get_style_rules,
    get_test_cmd,
)
from vcsx.generators.base import BaseGenerator


class CopilotGenerator(BaseGenerator):
    """Generates a GitHub Copilot setup with scoped instructions."""

    @property
    def name(self) -> str:
        return "copilot"

    @property
    def output_files(self) -> list[str]:
        return [
            ".github/copilot-instructions.md",
            ".github/instructions/*.instructions.md",
        ]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        """Generate .github/copilot-instructions.md — main Copilot context."""
        setup = get_setup_cmd(ctx)
        build = get_build_cmd(ctx)
        test = get_test_cmd(ctx)
        lint = get_lint_cmd(ctx)
        fmt = get_format_cmd(ctx)
        style_rules = get_style_rules(ctx)

        style_section = "\n".join(style_rules) if style_rules else "- Follow language idioms"

        purpose_block = ""
        if ctx.purpose or ctx.problem:
            lines = []
            if ctx.purpose:
                lines.append(f"**Purpose:** {ctx.purpose}")
            if ctx.problem:
                lines.append(f"**Problem:** {ctx.problem}")
            purpose_block = "\n".join(lines) + "\n\n"

        content = f"""# {ctx.project_name} — GitHub Copilot Instructions

> This file configures GitHub Copilot for this repository.
> Copilot reads this file automatically when suggesting code.

## Project Overview
{purpose_block}- **Name:** {ctx.project_name}
- **Type:** {ctx.project_type}
- **Language:** {ctx.language}
- **Framework:** {ctx.framework or "None"}
- **Description:** {ctx.description or "No description provided."}

## Quick Commands
```bash
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
```

## Code Style & Conventions
{style_section}

## Rules (always follow)
- NEVER suggest hardcoded API keys, tokens, or passwords.
- ALWAYS include error handling in suggested code.
- ALWAYS write tests for new functions when asked.
- Follow conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Keep functions small (< 30 lines) and single-purpose.
- Prefer explicit over implicit.
- No magic numbers — use named constants.

## What NOT to suggest
- `os.system()` with user input (command injection risk)
- `eval()` or `exec()` with user data
- Raw SQL with string formatting (use parameterized queries)
- `SELECT *` (always specify columns)
- Ignoring exceptions with bare `except: pass`
"""

        d = Path(output_dir) / ".github"
        d.mkdir(parents=True, exist_ok=True)
        (d / "copilot-instructions.md").write_text(content, encoding="utf-8")

        # Scoped instructions (.github/instructions/)
        self._generate_scoped_instructions(ctx, output_dir)

        return content

    def _generate_scoped_instructions(self, ctx: ProjectContext, output_dir: str) -> None:
        """Generate .github/instructions/ scoped instruction files.

        GitHub Copilot (2025+) supports scoped instructions with frontmatter:
        - applyTo: glob pattern for files this instruction applies to
        """
        instructions_dir = Path(output_dir) / ".github" / "instructions"
        instructions_dir.mkdir(parents=True, exist_ok=True)

        lang = (ctx.language or "").lower()
        fmt = get_format_cmd(ctx)
        lint = get_lint_cmd(ctx)

        # Code style instructions (scoped to source files)
        glob_pattern = (
            "**/*.py"
            if lang == "python"
            else "**/*.ts,**/*.tsx,**/*.js,**/*.jsx"
            if lang in ("typescript", "javascript")
            else "**/*"
        )
        type_hint_rule = (
            "- Use type hints on all public functions."
            if lang == "python"
            else "- Use explicit TypeScript types; avoid `any`."
            if lang == "typescript"
            else ""
        )

        (instructions_dir / "code-style.instructions.md").write_text(
            f"""---
applyTo: "{glob_pattern}"
---

# Code Style

- Format with `{fmt}` before committing.
- Run `{lint}` and fix all warnings.
- Keep functions small and focused — single responsibility.
- Prefer explicit over implicit.
- Use descriptive variable names.
{type_hint_rule}
- No magic numbers — use named constants.
- Handle all error cases explicitly.
""",
            encoding="utf-8",
        )

        # Testing instructions
        if lang == "python":
            test_glob = "tests/**,test_*.py,*_test.py"
            test_fw = ctx.test_framework or "pytest"
            test_example = "def test_<function>_<scenario>_<expected>():"
        else:
            test_glob = "**/*.test.*,**/*.spec.*,tests/**"
            test_fw = ctx.test_framework or "vitest"
            test_example = "it('<function> should <expected behavior>', () => {"

        (instructions_dir / "testing.instructions.md").write_text(
            f"""---
applyTo: "{test_glob}"
---

# Testing Guidelines

## Framework: {test_fw}

## Structure: AAA
1. **Arrange** — set up test data
2. **Act** — execute the function
3. **Assert** — verify the result

## Naming: `{test_example}`
Examples:
- `test_create_user_valid_email_returns_id`
- `test_login_wrong_password_returns_401`

## Rules
- Mock ALL external dependencies (DB, HTTP, filesystem).
- Test both happy path AND error cases.
- Tests must be independent — no shared mutable state.
- One logical assertion focus per test.
""",
            encoding="utf-8",
        )

        # Security instructions (all files)
        (instructions_dir / "security.instructions.md").write_text(
            """---
applyTo: "**"
---

# Security Guidelines

## Absolute Prohibitions
- NEVER hardcode API keys, passwords, tokens, or secrets.
- NEVER use `eval()`, `exec()`, or dynamic code with user input.
- NEVER trust user input — validate and sanitize at boundaries.
- NEVER log sensitive data (tokens, passwords, session IDs, PII).
- NEVER return internal error details or stack traces to API clients.

## Required Practices
- All secrets → environment variables.
- SQL queries → parameterized (never f-strings in queries).
- File paths → sanitized against path traversal (`../`).
- Auth → verified on every protected endpoint.
- Dependencies → check for known vulnerabilities before adding.
""",
            encoding="utf-8",
        )

        # API instructions if applicable
        if ctx.project_type == "api":
            (instructions_dir / "api.instructions.md").write_text(
                """---
applyTo: "**/routes/**,**/api/**,**/controllers/**,**/endpoints/**"
---

# API Design Guidelines

## URL Conventions
- Plural nouns: `/v1/users`, `/v1/orders`
- Kebab-case: `/v1/user-profiles`
- Always versioned: `/v1/...`
- No verbs in URLs: `/v1/users` not `/v1/getUsers`

## HTTP Methods
- GET → read, POST → create (201), PATCH → update, DELETE → remove (204)

## Response Shapes
```json
{ "data": {...}, "meta": { "requestId": "..." } }
```

## Error Shape
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [] } }
```

## Rules
- Paginate ALL list endpoints.
- Validate ALL input at the boundary.
- Return consistent error shapes.
- Rate limit auth endpoints.
""",
                encoding="utf-8",
            )

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        return {"note": "Copilot hooks not supported — use pre-commit hooks or GitHub Actions"}

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate GitHub Actions CI workflow — complements Copilot setup."""
        return self._generate_github_actions(ctx, output_dir)

    def _generate_github_actions(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate .github/workflows/ci.yml — language-aware CI pipeline."""
        workflows_dir = Path(output_dir) / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        lang = (ctx.language or "").lower()
        test_cmd = get_test_cmd(ctx)
        lint_cmd = get_lint_cmd(ctx)
        fmt_cmd = get_format_cmd(ctx)
        build_cmd = get_build_cmd(ctx)

        if lang == "python":
            setup_steps = f"""      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Check formatting
        run: {fmt_cmd} --check .

      - name: Lint
        run: {lint_cmd} .

      - name: Type check
        run: pyright src/ || mypy src/ || true

      - name: Test
        run: {test_cmd} --tb=short"""
            matrix_section = ""

        elif lang in ("typescript", "javascript"):
            setup_steps = f"""      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: {lint_cmd} .

      - name: Type check
        run: npx tsc --noEmit || true

      - name: Test
        run: {test_cmd}

      - name: Build
        run: {build_cmd}"""
            matrix_section = """    strategy:
      matrix:
        node-version: ["18", "20", "22"]
"""

        elif lang == "go":
            setup_steps = """      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: "1.22"
          cache: true

      - name: Download dependencies
        run: go mod download

      - name: Vet
        run: go vet ./...

      - name: Test
        run: go test -race -coverprofile=coverage.out ./...

      - name: Build
        run: go build ./..."""
            matrix_section = ""

        elif lang == "rust":
            setup_steps = """      - name: Install Rust toolchain
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy

      - name: Cache Cargo
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/bin/
            ~/.cargo/registry/index/
            ~/.cargo/registry/cache/
            ~/.cargo/git/db/
            target/
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}

      - name: Check formatting
        run: cargo fmt --all -- --check

      - name: Clippy
        run: cargo clippy -- -D warnings

      - name: Test
        run: cargo test

      - name: Build release
        run: cargo build --release"""
            matrix_section = ""

        else:
            setup_steps = f"""      - name: Install dependencies
        run: {get_setup_cmd(ctx)}

      - name: Test
        run: {test_cmd}"""
            matrix_section = ""

        workflow_content = f"""name: CI

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
    name: Build & Test
    runs-on: ubuntu-latest
{matrix_section}    steps:
      - name: Checkout
        uses: actions/checkout@v4

{setup_steps}
"""

        (workflows_dir / "ci.yml").write_text(workflow_content, encoding="utf-8")

        # Also generate dependabot.yml for automated dependency updates
        dependabot_content = """version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
"""

        if lang in ("typescript", "javascript"):
            dependabot_content += """
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    groups:
      dev-dependencies:
        dependency-type: "development"
"""
        elif lang == "python":
            dependabot_content += """
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
"""
        elif lang == "rust":
            dependabot_content += """
  - package-ecosystem: "cargo"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
"""

        (Path(output_dir) / ".github" / "dependabot.yml").write_text(
            dependabot_content, encoding="utf-8"
        )

        return ["ci.yml", "dependabot.yml"]

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        created = []
        created.append(_scaffold_gitignore(output_dir, ctx))
        created.append(_scaffold_readme(output_dir, ctx))
        lang = (ctx.language or "").lower()
        if lang in ("typescript", "javascript"):
            created.append(_scaffold_package_json(output_dir, ctx))
        elif lang == "python":
            created.append(_scaffold_requirements(output_dir, ctx))
        elif lang == "go":
            created.append(_scaffold_go_mod(output_dir, ctx))
        created.append(_scaffold_source_dirs(output_dir, ctx))
        return created


# ─── Scaffold helpers ────────────────────────────────────────────────────────


def _scaffold_gitignore(output_dir: str, ctx: ProjectContext) -> str:
    lines = [
        "node_modules/",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        ".env",
        ".env.local",
        "!.env.example",
        "dist/",
        "build/",
        ".idea/",
        ".vscode/",
        ".DS_Store",
        "coverage/",
    ]
    p = Path(output_dir) / ".gitignore"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ".gitignore"


def _scaffold_readme(output_dir: str, ctx: ProjectContext) -> str:
    setup = get_setup_cmd(ctx)
    test = get_test_cmd(ctx)
    content = f"# {ctx.project_name}\n\n{ctx.description or 'A project.'}\n\n## Setup\n```bash\n{setup}\n```\n\n## Test\n```bash\n{test}\n```\n"
    p = Path(output_dir) / "README.md"
    p.write_text(content, encoding="utf-8")
    return "README.md"


def _scaffold_package_json(output_dir: str, ctx: ProjectContext) -> str:
    import json

    content = {
        "name": ctx.project_name,
        "version": "0.1.0",
        "type": "module",
        "scripts": {"dev": "echo 'Add dev'", "build": "echo 'Add build'", "test": "npx vitest run"},
        "devDependencies": {"typescript": "^5.0.0", "vitest": "^2.0.0"},
    }
    p = Path(output_dir) / "package.json"
    p.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    return "package.json"


def _scaffold_requirements(output_dir: str, ctx: ProjectContext) -> str:
    lines = ["# Core\n# Add dependencies\n\n# Dev\npytest>=7.0\nruff>=0.1.0"]
    p = Path(output_dir) / "requirements.txt"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "requirements.txt"


def _scaffold_go_mod(output_dir: str, ctx: ProjectContext) -> str:
    content = f"module {ctx.project_name}\n\ngo 1.21\n"
    p = Path(output_dir) / "go.mod"
    p.write_text(content, encoding="utf-8")
    return "go.mod"


def _scaffold_source_dirs(output_dir: str, ctx: ProjectContext) -> str:
    base = Path(output_dir)
    dirs = ["src", "tests"]
    if ctx.project_type == "api":
        dirs.extend(["src/api", "src/models"])
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
    lang = (ctx.language or "").lower()
    if lang == "python":
        for d in dirs:
            init_file = base / d / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")
    return "source directories"
