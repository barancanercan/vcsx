"""Cursor generator — produces .cursorrules and .cursor/rules/."""

import json
from pathlib import Path

from vcsx.core.context import ProjectContext
from vcsx.core.inference import infer_formatter, infer_linter, infer_test_framework
from vcsx.generators._shared import (
    get_build_cmd as _shared_build,
)
from vcsx.generators._shared import (
    get_setup_cmd as _shared_setup,
)
from vcsx.generators._shared import (
    get_style_rules as _shared_style,
)
from vcsx.generators._shared import (
    get_test_cmd as _shared_test,
)
from vcsx.generators.base import BaseGenerator


class CursorGenerator(BaseGenerator):
    """Generates a complete Cursor setup."""

    @property
    def name(self) -> str:
        return "cursor"

    @property
    def output_files(self) -> list[str]:
        return [".cursorrules", ".cursor/rules/*.mdc"]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        """Generate .cursorrules file (legacy format - fallback)."""
        lines = [
            f"# {ctx.project_name} — Cursor Rules",
            "",
            "## Project Overview",
            ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack}.",
            "",
            "## Commands",
            "```bash",
            f"# Setup: {_get_setup_cmd(ctx)}",
            f"# Build: {_get_build_cmd(ctx)}",
            f"# Test: {_get_test_cmd(ctx)}",
            f"# Lint: {ctx.linter or infer_linter(ctx.language)} src/",
            f"# Format: {ctx.formatter or infer_formatter(ctx.language)} src/",
            "```",
            "",
            "## Code Style",
        ]
        lines.extend(_get_style_rules(ctx))
        lines.extend(
            [
                "",
                "## Architecture",
                f"- **Type**: {ctx.project_type}",
                f"- **Language**: {ctx.language}",
                f"- **Framework**: {ctx.framework or 'None'}",
                "",
                "## Rules",
                "- NEVER commit secrets or API keys",
                "- ALWAYS run tests before committing",
                "- ALWAYS follow existing code patterns",
                "- Keep functions small and single-purpose",
            ]
        )

        content = "\n".join(lines)
        (Path(output_dir) / ".cursorrules").write_text(content, encoding="utf-8")
        return content

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate .cursor/rules/*.mdc files (modern format)."""
        rules_dir = Path(output_dir) / ".cursor" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        created = []

        # Modern .mdc format with frontmatter
        created.append(_rule_build_test_mdc(rules_dir, ctx))
        created.append(_rule_commit_message_mdc(rules_dir))
        created.append(_rule_pr_review_mdc(rules_dir))
        created.append(_rule_test_patterns_mdc(rules_dir, ctx))

        if ctx.project_type == "api":
            created.append(_rule_api_conventions_mdc(rules_dir))

        if ctx.auth_needed:
            created.append(_rule_auth_mdc(rules_dir, ctx))

        # Always include performance + refactoring rules
        created.append(_rule_performance_mdc(rules_dir, ctx))
        created.append(_rule_refactoring_mdc(rules_dir, ctx))

        return created

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        """Cursor doesn't have hooks — return empty."""
        return {"note": "Cursor hooks not supported — use pre-commit hooks instead"}

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Cursor doesn't have agents — return empty."""
        return []

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate project scaffold."""
        created = []
        created.append(_scaffold_gitignore(output_dir, ctx))
        created.append(_scaffold_readme(output_dir, ctx))
        created.append(_scaffold_env_example(output_dir, ctx))

        if ctx.language in ("typescript", "javascript"):
            created.append(_scaffold_tsconfig(output_dir))
            created.append(_scaffold_package_json(output_dir, ctx))
        elif ctx.language == "python":
            created.append(_scaffold_requirements(output_dir, ctx))
            created.append(_scaffold_pyproject(output_dir, ctx))
        elif ctx.language == "go":
            created.append(_scaffold_go_mod(output_dir, ctx))

        created.append(_scaffold_source_dirs(output_dir, ctx))
        return created


# ─── Modern .mdc Rule Templates ─────────────────────────────────────────────


def _rule_build_test_mdc(rules_dir: Path, ctx: ProjectContext) -> str:
    """Build and test commands rule (modern .mdc format)."""
    d = rules_dir / "build-test.mdc"
    content = f"""---
description: Build, test, and development commands for {ctx.project_name}
globs: ["*.py", "*.ts", "*.js", "*.go", "*.rs"]
alwaysApply: false
---

# Build & Test Commands

## Setup
```bash
{_get_setup_cmd(ctx)}
```

## Build
```bash
{_get_build_cmd(ctx)}
```

## Test
```bash
{_get_test_cmd(ctx)}
```

## Lint
```bash
{ctx.linter or infer_linter(ctx.language)} src/
```

## Format
```bash
{ctx.formatter or infer_formatter(ctx.language)} src/
```

## Rules
- Always run tests before committing
- Run linter before pushing
- Follow existing code patterns
"""
    d.write_text(content, encoding="utf-8")
    return "build-test"


def _rule_commit_message_mdc(rules_dir: Path) -> str:
    """Commit message generation rule."""
    d = rules_dir / "commit-message.mdc"
    content = """---
description: Generate conventional commit messages from git diff
globs: ["*.py", "*.ts", "*.js", "*.go", "*.rs", "*.java"]
alwaysApply: false
---

# Commit Message Rules

Format: `<type>(<scope>): <description>`

## Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

## Process
1. Run `git diff --cached` to see staged changes
2. Analyze changes to determine type
3. Generate concise description (max 72 chars)
4. If multiple types, suggest separate commits
"""
    d.write_text(content, encoding="utf-8")
    return "commit-message"


def _rule_pr_review_mdc(rules_dir: Path) -> str:
    """PR review rule."""
    d = rules_dir / "pr-review.mdc"
    content = """---
description: Review pull requests — severity-rated checklist
globs: ["*.py", "*.ts", "*.js", "*.go", "*.rs"]
alwaysApply: false
---

# PR Review Rules

## Process
1. Run `git diff main...HEAD --stat` for overview
2. Run `git diff main...HEAD` for full diff
3. Rate each issue: 🔴 BLOCKING / 🟡 IMPORTANT / 🟢 SUGGESTION

## 🔴 Blocking (must fix)
- [ ] No secrets or API keys committed
- [ ] Tests pass (`run test suite`)
- [ ] No obvious security vulnerabilities
- [ ] No debug `print()` / `console.log()` left in
- [ ] No broken imports or syntax errors

## 🟡 Important (should fix)
- [ ] New code has tests
- [ ] Error cases handled (not just happy path)
- [ ] No unnecessary dependencies added
- [ ] Breaking changes documented

## 🟢 Suggestions
- [ ] Code follows existing style patterns
- [ ] Descriptive variable/function names
- [ ] Complex logic has comments

## Output Format
```
## PR Review

### 🔴 BLOCKING
- [file:line] Issue → Fix

### 🟡 IMPORTANT
- [file:line] Issue

### 🟢 SUGGESTIONS
- [file:line] Suggestion

### Verdict: APPROVE / REQUEST_CHANGES
```
"""
    d.write_text(content, encoding="utf-8")
    return "pr-review"


def _rule_test_patterns_mdc(rules_dir: Path, ctx: ProjectContext) -> str:
    """Test patterns rule."""
    d = rules_dir / "test-patterns.mdc"
    fw = ctx.test_framework or infer_test_framework(ctx.language)
    lang = (ctx.language or "").lower()
    test_glob = (
        "test_*.py,*_test.py,tests/**"
        if lang == "python"
        else "**/*.test.ts,**/*.spec.ts,**/*.test.js"
    )
    content = f"""---
description: Test writing patterns — AAA structure, naming, mocking
globs: ["{test_glob}"]
alwaysApply: true
---

# Test Patterns — {fw}

## AAA Structure (mandatory)
```
Arrange → Act → Assert
```

## Naming Convention
`test_<function>_<scenario>_<expected>`
- `test_create_user_valid_email_returns_id`
- `test_login_wrong_password_returns_401`
- `test_send_email_smtp_down_raises_error`

## Rules
- Tests must be **independent** — no shared mutable state
- Mock ALL external dependencies (DB, HTTP, filesystem)
- Test both happy path AND error paths
- Use fixtures/factories, not hardcoded test data

## Framework: {fw}
```bash
# Run all tests
{fw if fw != "vitest" else "npx vitest run"}

# Run with coverage
{"pytest --cov=src" if lang == "python" else "npx vitest run --coverage"}
```
"""
    d.write_text(content, encoding="utf-8")
    return "test-patterns"


def _rule_api_conventions_mdc(rules_dir: Path) -> str:
    """API conventions rule."""
    d = rules_dir / "api-conventions.mdc"
    content = """---
description: REST API design — URL naming, HTTP codes, response shapes
globs: ["**/api/**", "**/routes/**", "**/controllers/**", "**/endpoints/**"]
alwaysApply: false
---

# API Conventions

## URL Rules
| ✅ Good | ❌ Bad |
|---------|--------|
| `/v1/users` | `/users` (no version) |
| `/v1/user-profiles` | `/v1/userProfiles` |
| `/v1/orders` | `/v1/getOrders` (verb) |

## HTTP Methods & Status Codes
| Method | Use | Success | Error |
|--------|-----|---------|-------|
| GET | Read | 200 | 404 |
| POST | Create | 201 | 400/422 |
| PATCH | Update | 200 | 404/400 |
| DELETE | Remove | 204 | 404 |

## Response Envelope
```json
{ "data": {...}, "meta": { "requestId": "req_abc123" } }
```

## Error Shape
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is invalid",
    "details": [{ "field": "email", "message": "Must be valid email" }]
  }
}
```

## Must Do
- Paginate ALL list endpoints
- Validate ALL input at boundary
- Return consistent error shapes
- Never expose internal errors to clients
"""
    d.write_text(content, encoding="utf-8")
    return "api-conventions"


def _rule_auth_mdc(rules_dir: Path, ctx: ProjectContext) -> str:
    """Auth conventions rule."""
    d = rules_dir / "auth-conventions.mdc"
    auth_method = ctx.auth_method or "JWT"
    content = f"""---
description: Authentication patterns — {auth_method} security rules
globs: ["**/auth/**", "**/middleware/**", "**/guards/**"]
alwaysApply: true
---

# Auth Conventions — {auth_method}

## Security Rules (Non-Negotiable)
- NEVER log tokens, passwords, or session IDs
- NEVER expose whether an email exists on login failure
- Rate limit: login (5/min), register (3/min), reset-password (3/hour)
- Passwords: bcrypt/argon2 only (not MD5/SHA1)
- All protected endpoints: verify auth on EVERY request

## {auth_method} Implementation
- Access tokens: short-lived (15 min)
- Refresh tokens: rotate on each use, invalidate old
- Store in httpOnly cookies (web) or secure storage (mobile)
- Never in localStorage (XSS vulnerable)

## Login Response Pattern
```
# ✅ Same error for wrong email AND wrong password
raise AuthError("Invalid credentials")  # Don't leak user existence

# ❌ Leaks that email doesn't exist
raise AuthError("User not found")
```
"""
    d.write_text(content, encoding="utf-8")
    return "auth-conventions"


def _rule_performance_mdc(rules_dir: Path, ctx: ProjectContext) -> str:
    """Performance optimization rules — language-aware."""
    d = rules_dir / "performance.mdc"
    lang = (ctx.language or "").lower()

    lang_tips: dict[str, list[str]] = {
        "python": [
            "Use `__slots__` for data classes with many instances.",
            "Prefer list comprehensions over `map()`/`filter()` for clarity.",
            "Use `functools.lru_cache` for pure functions called repeatedly.",
            "Avoid `global` and module-level mutable state.",
            "Use `asyncio` for I/O-bound work; `concurrent.futures` for CPU-bound.",
            "Profile before optimizing: `python -m cProfile -s cumtime your_script.py`",
            "Batch DB queries — avoid N+1 with `select_related` / `prefetch_related`.",
            "Use `generators` for large datasets — never load everything into memory.",
        ],
        "typescript": [
            "Avoid unnecessary re-renders — memoize with `React.memo`, `useMemo`, `useCallback`.",
            "Lazy-load routes and heavy components with `React.lazy` + `Suspense`.",
            "Use `Map`/`Set` over plain objects for frequent lookups.",
            "Avoid synchronous loops over large arrays in render paths.",
            "Prefer `structuredClone` over `JSON.parse(JSON.stringify(...))` for deep copies.",
            "Debounce search inputs and expensive event handlers.",
            "Profile with Chrome DevTools Performance tab before optimizing.",
            "Tree-shake unused imports — check bundle with `vite-bundle-visualizer`.",
        ],
        "go": [
            "Use `sync.Pool` for frequently allocated temporary objects.",
            "Prefer `[]byte` over `string` for heavy manipulation.",
            "Profile with `go tool pprof` before optimizing.",
            "Use buffered channels to decouple producer/consumer goroutines.",
            "Avoid reflection in hot paths.",
            "Benchmark with `go test -bench=. -benchmem`.",
            "Use `strings.Builder` for string concatenation in loops.",
            "Reuse HTTP clients — don't create a new one per request.",
        ],
        "rust": [
            "Prefer borrowing over cloning — avoid `.clone()` in hot paths.",
            "Use `Vec` + index over linked lists for cache efficiency.",
            "Benchmark with `criterion` before any micro-optimization.",
            "Use `Rc`/`Arc` sparingly — prefer ownership.",
            "Avoid `Box<dyn Trait>` in hot paths — prefer generics (monomorphization).",
            "Use `rayon` for data-parallel CPU-bound work.",
            "Profile with `perf` or `flamegraph` on Linux.",
            "Prefer stack allocation; avoid heap when data is small and short-lived.",
        ],
    }

    tips = lang_tips.get(
        lang,
        [
            "Profile before optimizing — measure, don't guess.",
            "Avoid premature optimization.",
            "Cache expensive computations.",
            "Minimize I/O in hot paths.",
            "Use lazy loading for large resources.",
        ],
    )

    tips_md = "\n".join(f"- {t}" for t in tips)
    lang_display = ctx.language or "any language"

    content = f"""---
description: Performance optimization guidelines for {lang_display} projects
globs: ["src/**", "lib/**", "app/**"]
alwaysApply: false
---

# Performance Guidelines — {lang_display.title()}

## Golden Rule
**Measure first, optimize second.** Always profile before changing code for performance.

## Language-Specific Tips
{tips_md}

## General Principles
- **N+1 queries**: always batch or use eager loading for DB relationships.
- **Caching**: cache at the right layer (DB, service, HTTP) — not everywhere.
- **Pagination**: never return unbounded lists from APIs or DB queries.
- **Async I/O**: don't block the event loop / goroutine scheduler with sync I/O.
- **Memory**: prefer streaming over loading full datasets into memory.

## Before Merging Performance Changes
1. Run benchmarks to confirm improvement (not just "feels faster").
2. Check memory usage doesn't increase unexpectedly.
3. Verify the change doesn't break correctness under load.
"""
    d.write_text(content, encoding="utf-8")
    return "performance"


def _rule_refactoring_mdc(rules_dir: Path, ctx: ProjectContext) -> str:
    """Safe refactoring workflow rule."""
    d = rules_dir / "refactoring.mdc"
    test_cmd = ctx.test_framework or "run tests"
    lang = (ctx.language or "").lower()

    if lang == "python":
        smell_examples = [
            "Function > 30 lines → extract sub-functions",
            "Class > 300 lines → split responsibilities (SRP)",
            "Nested ifs > 3 deep → invert conditions or extract",
            "Duplicated logic in 3+ places → extract to shared function",
            "Magic numbers → named constants",
            "`except Exception: pass` → handle or re-raise with context",
        ]
    elif lang in ("typescript", "javascript"):
        smell_examples = [
            "Component > 200 lines → split into smaller components",
            "Function > 30 lines → extract helpers",
            "Prop drilling > 2 levels → use context or state management",
            "Duplicated logic → custom hook or shared utility",
            "Magic numbers → named constants or enums",
            "`any` type in TypeScript → narrow to specific type",
        ]
    elif lang == "go":
        smell_examples = [
            "Function > 30 lines → extract helpers",
            "Package with > 10 exported symbols doing different things → split packages",
            "Repeated error wrapping patterns → helper function",
            "Long parameter lists (> 4) → use struct options pattern",
            "Magic numbers → typed constants",
            "Global mutable state → inject as dependency",
        ]
    else:
        smell_examples = [
            "Function > 30 lines → extract",
            "Deep nesting > 3 levels → invert / extract",
            "Duplicated logic in 3+ places → DRY it",
            "Magic numbers → named constants",
            "Large class/module → split by responsibility",
        ]

    smells_md = "\n".join(f"- {s}" for s in smell_examples)

    content = f"""---
description: Safe refactoring workflow — step-by-step with tests as safety net
globs: ["src/**", "lib/**", "app/**"]
alwaysApply: false
---

# Refactoring Workflow

## Golden Rules
1. **Tests first** — if there are no tests, write them before refactoring.
2. **One change at a time** — rename, then extract, then move. Not all at once.
3. **Run tests after each step** — `{test_cmd}`
4. **Commit at each green state** — small, reversible steps.

## Code Smells to Watch For
{smells_md}

## Step-by-Step Process

### 1. Understand before changing
```bash
# See what tests exist for this code
# Read the code and its callers before touching anything
```

### 2. Make tests pass (if they don't)
```bash
{test_cmd}
```

### 3. Refactor one thing
- Rename a variable → run tests → commit
- Extract a function → run tests → commit
- Move to a module → run tests → commit

### 4. Verify behavior is identical
```bash
{test_cmd}
# Compare output/API contracts before and after
```

### 5. Commit with clear message
```
refactor(<scope>): extract payment validation into PaymentValidator

No behavior change. Splitting 80-line process_payment() for readability.
```

## Common Patterns

### Extract Function
```
# Before: inline 15-line logic
# After: call validate_payment(data) + test it independently
```

### Replace Magic Number
```
# Before: if retries > 3:
# After: MAX_RETRIES = 3 ... if retries > MAX_RETRIES:
```

### Invert Condition (reduce nesting)
```
# Before: if user: if user.active: if user.has_role("admin"): ...
# After: if not user: return; if not user.active: return; ...
```
"""
    d.write_text(content, encoding="utf-8")
    return "refactoring"


def _rule_commit_message(rules_dir: Path) -> str:
    d = rules_dir / "commit-message.md"
    content = """---
description: Generate conventional commit messages
---

# Commit Message Rules

Format: `<type>(<scope>): <description>`

## Types
- `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Process
1. Run `git diff --cached`
2. Determine type from changes
3. Generate concise description (max 72 chars)
4. Suggest separate commits if multiple types
"""
    d.write_text(content, encoding="utf-8")
    return "commit-message"


def _rule_pr_review(rules_dir: Path) -> str:
    d = rules_dir / "pr-review.md"
    content = """---
description: Review PRs against team standards
---

# PR Review Rules

## Checklist
- [ ] Code follows style guidelines
- [ ] No secrets committed
- [ ] Tests cover new functionality
- [ ] Error handling is appropriate
- [ ] Documentation updated

## Process
1. Run `git diff main...HEAD`
2. Check each file against checklist
3. Report findings with line references
"""
    d.write_text(content, encoding="utf-8")
    return "pr-review"


def _rule_test_patterns(rules_dir: Path, ctx: ProjectContext) -> str:
    d = rules_dir / "test-patterns.md"
    content = f"""---
description: Test writing patterns using {ctx.test_framework or infer_test_framework(ctx.language)}
---

# Test Patterns

## Framework: {ctx.test_framework or infer_test_framework(ctx.language)}

## Structure
1. Arrange — Set up test data
2. Act — Execute code under test
3. Assert — Verify outcome

## Guidelines
- Test behavior, not implementation
- One assertion per test when possible
- Descriptive test names
- Mock external dependencies
"""
    d.write_text(content, encoding="utf-8")
    return "test-patterns"


def _rule_api_conventions(rules_dir: Path) -> str:
    d = rules_dir / "api-conventions.md"
    content = """---
description: REST API design patterns
---

# API Conventions

- kebab-case for paths: `/api/user-profiles`
- Nouns not verbs: `/api/users`
- Version in URL: `/api/v1/users`
- Plural nouns for collections
- GET/POST/PUT/PATCH/DELETE for CRUD
"""
    d.write_text(content, encoding="utf-8")
    return "api-conventions"


# ─── Scaffold (reused from claude_code) ──────────────────────────────────────


def _get_setup_cmd(ctx: ProjectContext) -> str:
    return _shared_setup(ctx)


def _get_build_cmd(ctx: ProjectContext) -> str:
    return _shared_build(ctx)


def _get_test_cmd(ctx: ProjectContext) -> str:
    return _shared_test(ctx)


def _get_style_rules(ctx: ProjectContext) -> list[str]:
    return _shared_style(ctx)


def _scaffold_gitignore(output_dir: str, ctx: ProjectContext) -> str:
    lines = [
        "# Dependencies",
        "node_modules/",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        "vendor/",
        "",
        "# Build",
        "dist/",
        "build/",
        "",
        "# Environment",
        ".env",
        ".env.local",
        "!.env.example",
        "",
        "# IDE",
        ".idea/",
        ".vscode/",
        "",
        "# OS",
        ".DS_Store",
        "Thumbs.db",
        "",
        "# Coverage",
        "coverage/",
        "htmlcov/",
    ]
    p = Path(output_dir) / ".gitignore"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ".gitignore"


def _scaffold_readme(output_dir: str, ctx: ProjectContext) -> str:
    content = f"""# {ctx.project_name}

{ctx.description or f"A {ctx.project_type} project."}

## Setup
```bash
{_get_setup_cmd(ctx)}
```

## Test
```bash
{_get_test_cmd(ctx)}
```

## Architecture
- **Type**: {ctx.project_type}
- **Language**: {ctx.language}
- **Framework**: {ctx.framework or "None"}
"""
    p = Path(output_dir) / "README.md"
    p.write_text(content, encoding="utf-8")
    return "README.md"


def _scaffold_env_example(output_dir: str, ctx: ProjectContext) -> str:
    lines = [
        "# Application",
        "NODE_ENV=development",
        "PORT=3000",
        "",
        "# Database",
        "DATABASE_URL=postgresql://user:password@localhost:5432/dbname",
    ]
    if ctx.auth_needed:
        lines.extend(["", "# Auth", "JWT_SECRET=your-secret-key-here"])
    p = Path(output_dir) / ".env.example"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ".env.example"


def _scaffold_tsconfig(output_dir: str) -> str:
    content = '{"compilerOptions":{"target":"ES2022","module":"ESNext","moduleResolution":"bundler","strict":true,"esModuleInterop":true,"skipLibCheck":true,"forceConsistentCasingInFileNames":true,"resolveJsonModule":true,"isolatedModules":true,"noEmit":true,"outDir":"./dist","rootDir":"./src","baseUrl":".","paths":{"@/*":["src/*"]}},"include":["src/**/*"],"exclude":["node_modules","dist"]}'
    p = Path(output_dir) / "tsconfig.json"
    p.write_text(content, encoding="utf-8")
    return "tsconfig.json"


def _scaffold_package_json(output_dir: str, ctx: ProjectContext) -> str:

    content = {
        "name": ctx.project_name,
        "version": "0.1.0",
        "type": "module",
        "scripts": {
            "dev": "echo 'Add dev command'",
            "build": "echo 'Add build command'",
            "test": "npx vitest run",
            "lint": "eslint src/",
            "format": "prettier --write src/",
        },
        "devDependencies": {
            "eslint": "^9.0.0",
            "prettier": "^3.0.0",
            "typescript": "^5.0.0",
            "vitest": "^2.0.0",
        },
    }
    p = Path(output_dir) / "package.json"
    p.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    return "package.json"


def _scaffold_requirements(output_dir: str, ctx: ProjectContext) -> str:
    lines = [
        "# Core",
        "# Add dependencies",
        "",
        "# Dev",
        "pytest>=7.0",
        "ruff>=0.1.0",
        "mypy>=1.0",
    ]
    p = Path(output_dir) / "requirements.txt"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "requirements.txt"


def _scaffold_pyproject(output_dir: str, ctx: ProjectContext) -> str:
    content = f"""[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{ctx.project_name}"
version = "0.1.0"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
"""
    p = Path(output_dir) / "pyproject.toml"
    p.write_text(content, encoding="utf-8")
    return "pyproject.toml"


def _scaffold_go_mod(output_dir: str, ctx: ProjectContext) -> str:
    content = f"module {ctx.project_name}\n\ngo 1.21\n"
    p = Path(output_dir) / "go.mod"
    p.write_text(content, encoding="utf-8")
    return "go.mod"


def _scaffold_source_dirs(output_dir: str, ctx: ProjectContext) -> str:
    base = Path(output_dir)
    dirs = ["src", "tests"]
    if ctx.project_type == "api":
        dirs.extend(
            [
                "src/api",
                "src/models",
                "src/middleware",
                "tests/unit",
                "tests/integration",
            ]
        )
    elif ctx.project_type == "web":
        dirs.extend(
            [
                "src/components",
                "src/pages",
                "src/utils",
                "tests/unit",
                "tests/integration",
            ]
        )
    elif ctx.project_type == "cli":
        dirs.extend(["src/commands", "src/utils", "tests/unit"])
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
    if ctx.language == "python":
        for d in dirs:
            init_file = base / d / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")
    return "source directories"
