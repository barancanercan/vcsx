"""Aider AI generator — produces Aider-specific configuration.

Aider docs: https://aider.chat/docs/config/aider_conf.html
Valid .aider.conf.yaml keys align with Aider's CLI flags.
"""

from pathlib import Path

from vcsx.core.context import ProjectContext
from vcsx.generators.base import BaseGenerator


class AiderGenerator(BaseGenerator):
    """Generates a complete Aider terminal AI setup."""

    @property
    def name(self) -> str:
        return "aider"

    @property
    def output_files(self) -> list[str]:
        return [
            ".aider.conf.yaml",
            ".aider.context.md",
        ]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        """Generate .aider.conf.yaml using valid Aider CLI flags.

        Key valid settings: model, weak-model, editor-model, auto-commits,
        dirty-commits, git, auto-lint, lint-cmd, auto-test, test-cmd,
        read, map-tokens, cache-prompts, suggest-shell-commands.
        """
        lang = (ctx.language or "").lower()

        # Derive test command
        test_cmd = _get_test_cmd(ctx)

        # Derive lint command
        lint_cmd = ctx.linter or ("ruff check" if lang == "python" else "eslint .")

        # Language-specific file patterns for --read (context files to always include)
        read_files = _get_read_files(ctx)

        content = f"""# {ctx.project_name} — Aider Configuration
# Reference: https://aider.chat/docs/config/aider_conf.html

##############################################################
# Model Configuration
##############################################################
# Claude Sonnet is recommended for best coding performance.
# Uncomment the model you want to use:

# model: anthropic/claude-sonnet-4-5
# model: openai/gpt-4o
model: openai/gpt-4o

# Weaker model for simple tasks (faster + cheaper)
weak-model: openai/gpt-4o-mini

##############################################################
# Git Integration
##############################################################
# Auto-commit AI changes with a generated commit message
auto-commits: true

# Allow commits even when repo has uncommitted changes
dirty-commits: true

# Git integration (disable to use aider outside a git repo)
git: true

##############################################################
# Linting & Testing
##############################################################
# Run linter after every code change
auto-lint: true
lint-cmd: {lint_cmd}

# Run tests after every code change
auto-test: false
test-cmd: {test_cmd}

##############################################################
# Context Management
##############################################################
# Files to always include in context (read-only)
{_format_read_files(read_files)}
# Repository map token budget (higher = more context, more tokens)
map-tokens: 2048

# Cache AI prompts to reduce costs (requires aider >= 0.50)
cache-prompts: true

##############################################################
# UX
##############################################################
# Suggest shell commands when appropriate
suggest-shell-commands: true

# Show diffs after applying changes
show-diffs: false
"""
        (Path(output_dir) / ".aider.conf.yaml").write_text(content, encoding="utf-8")
        return content

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate .aider.context.md — always-loaded project context."""
        lang = (ctx.language or "").lower()
        content = f"""# {ctx.project_name} — Aider Project Context

> This file is automatically loaded by Aider as project context.
> Edit it to give Aider better understanding of your project.

## Overview
{ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack}."}

## Purpose & Problem
{"**Purpose:** " + ctx.purpose if ctx.purpose else "*(not specified)*"}
{"**Problem:** " + ctx.problem if ctx.problem else ""}

## Tech Stack
- **Language**: {ctx.language or "Not specified"}
- **Framework**: {ctx.framework or "None"}
- **Testing**: {ctx.test_framework or "None"}
- **Hosting**: {ctx.hosting or "TBD"}

## Common Commands
```bash
# Setup
{_get_setup_cmd(ctx)}

# Build
{_get_build_cmd(ctx)}

# Test
{_get_test_cmd(ctx)}

# Lint
{_get_lint_cmd(ctx)}

# Format
{_get_format_cmd(ctx)}
```

## File Structure
```
{ctx.project_name}/
{_get_file_structure(ctx)}
```

## Architecture Overview
{_get_architecture_overview(ctx)}

## Key Decisions
{_get_key_decisions(ctx)}

## Gotchas & Pitfalls
{_get_gotchas(ctx)}

## Code Conventions
- Follow conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Never commit secrets, API keys, or `.env` files
- Write tests for new functionality
- Keep commits atomic — one logical change per commit
- Run formatter + linter before every commit

## What NOT to Do
- Do not run `git push --force`
- Do not modify production database migrations
- Do not install global packages without updating requirements
{_get_language_dont_do(lang)}"""
        (Path(output_dir) / ".aider.context.md").write_text(content, encoding="utf-8")
        return [".aider.context.md"]

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        """Aider handles hooks via auto-lint and auto-test in config."""
        return {}

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        return []


# ─── Private helpers ──────────────────────────────────────────────────────────


def _get_setup_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm install",
        "javascript": "npm install",
        "python": "pip install -e '.[dev]'"
        if "pyproject" in (ctx.tech_stack or "").lower()
        else "pip install -r requirements.txt",
        "go": "go mod tidy",
        "rust": "cargo build",
    }.get((ctx.language or "").lower(), "npm install")


def _get_build_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm run build",
        "javascript": "npm run build",
        "python": "python -m build",
        "go": "go build ./...",
        "rust": "cargo build --release",
    }.get((ctx.language or "").lower(), "npm run build")


def _get_test_cmd(ctx: ProjectContext) -> str:
    fw = (ctx.test_framework or "").lower()
    if fw == "pytest" or (not fw and (ctx.language or "").lower() == "python"):
        return "pytest"
    if fw in ("vitest", "jest"):
        return f"npx {fw} run"
    if fw == "go test":
        return "go test ./..."
    if (ctx.language or "").lower() == "rust":
        return "cargo test"
    return "npm test"


def _get_read_files(ctx: ProjectContext) -> list[str]:
    """Return files Aider should always read as context."""
    candidates = ["README.md", "AGENTS.md", "CLAUDE.md"]
    lang = (ctx.language or "").lower()
    if lang == "python":
        candidates.extend(["pyproject.toml", "requirements.txt"])
    elif lang in ("typescript", "javascript"):
        candidates.append("package.json")
    elif lang == "go":
        candidates.append("go.mod")
    elif lang == "rust":
        candidates.append("Cargo.toml")
    return candidates


def _format_read_files(files: list[str]) -> str:
    if not files:
        return ""
    lines = ["read:"]
    for f in files:
        lines.append(f"  - {f}")
    return "\n".join(lines) + "\n"


def _get_lint_cmd(ctx: ProjectContext) -> str:
    lang = (ctx.language or "").lower()
    if ctx.linter:
        return ctx.linter
    return {
        "python": "ruff check .",
        "go": "golangci-lint run",
        "rust": "cargo clippy -- -D warnings",
        "typescript": "eslint src/",
        "javascript": "eslint src/",
    }.get(lang, "eslint src/")


def _get_format_cmd(ctx: ProjectContext) -> str:
    lang = (ctx.language or "").lower()
    if ctx.formatter:
        return ctx.formatter
    return {
        "python": "ruff format .",
        "go": "gofmt -w .",
        "rust": "cargo fmt",
        "typescript": "prettier --write src/",
        "javascript": "prettier --write src/",
    }.get(lang, "prettier --write src/")


def _get_file_structure(ctx: ProjectContext) -> str:
    lang = (ctx.language or "").lower()

    structures = {
        "go": """\
├── cmd/
│   └── {name}/
│       └── main.go
├── internal/
│   └── (private packages)
├── pkg/
│   └── (public packages)
├── go.mod
└── go.sum""",
        "rust": """\
├── src/
│   ├── main.rs         # Binary entry point
│   ├── lib.rs          # Library root (if dual crate)
│   └── (modules)
├── tests/              # Integration tests
├── benches/            # Benchmarks
├── Cargo.toml
└── Cargo.lock""",
        "python": """\
├── src/
│   └── {name}/
│       ├── __init__.py
│       └── (modules)
├── tests/
├── pyproject.toml
└── README.md""",
        "typescript": """\
├── src/
│   ├── index.ts
│   └── (modules)
├── tests/
├── package.json
├── tsconfig.json
└── README.md""",
    }

    template = structures.get(
        lang,
        """\
├── src/
├── tests/
└── (config files)""",
    )
    return template.replace("{name}", ctx.project_name or "app")


def _get_architecture_overview(ctx: ProjectContext) -> str:
    lang = (ctx.language or "").lower()
    project_type = ctx.project_type or "application"
    framework = ctx.framework or "none"

    overviews = {
        "go": f"""\
This is a Go {project_type} project.
- Entry point: `cmd/` directory (one sub-dir per binary)
- Internal packages in `internal/` (not importable by external projects)
- Public library packages in `pkg/`
- Framework: {framework}
- Error handling: explicit `error` returns, no panics in library code
- Concurrency: goroutines + channels; all shared state protected""",
        "rust": f"""\
This is a Rust {project_type} project.
- Entry point: `src/main.rs` (binary) or `src/lib.rs` (library)
- Error handling: `Result<T, E>` throughout; `thiserror` for custom errors
- Memory model: ownership + borrowing — avoid unnecessary clones
- Async: tokio runtime (if async features present)
- Framework: {framework}""",
        "python": f"""\
This is a Python {project_type} project.
- Package layout: `src/{ctx.project_name or "app"}/` (src layout)
- Framework: {framework}
- Type hints used throughout; validate with mypy/pyright
- Config: environment variables via `.env` / `pydantic-settings`""",
    }

    return overviews.get(
        lang,
        f"""\
This is a {project_type} project using {ctx.language or "the configured language"}.
- Framework: {framework}
- Follow existing patterns in the codebase.""",
    )


def _get_key_decisions(ctx: ProjectContext) -> str:
    lang = (ctx.language or "").lower()

    decisions = {
        "go": """\
- **Standard library first**: use stdlib before reaching for external packages
- **Explicit error handling**: all errors checked and wrapped with context
- **Interface-based design**: accept interfaces, return concrete types
- **Table-driven tests**: preferred pattern for comprehensive test coverage
- **No global state**: dependencies injected via function parameters or structs""",
        "rust": """\
- **Zero-cost abstractions**: prefer iterators and traits over manual loops
- **Error hierarchy**: `thiserror` for library errors, `anyhow` for binaries
- **Fearless concurrency**: prefer message passing (channels) over shared memory
- **Cargo features**: use feature flags for optional functionality
- **No unwrap in library code**: all error paths explicitly handled""",
        "python": """\
- **Src layout**: code in `src/` to prevent import confusion during development
- **Type hints everywhere**: enables better tooling and catches bugs early
- **Dependency injection**: avoid module-level singletons; pass dependencies explicitly
- **Pydantic for validation**: all external data validated at the boundary""",
    }

    return decisions.get(
        lang,
        """\
- Follow existing patterns in the codebase
- Document non-obvious decisions inline
- Keep dependencies minimal""",
    )


def _get_gotchas(ctx: ProjectContext) -> str:
    lang = (ctx.language or "").lower()

    gotchas = {
        "go": """\
- `defer` in loops creates all defers before any run — be careful with file handles
- Goroutine leaks: always cancel contexts and close channels
- Shadowing `:=` in nested scopes can silently create new variables
- `nil` maps can be read but not written to — initialize with `make(map[K]V)`
- `range` copies values — use index or pointer for mutation
- `http.DefaultClient` has no timeout — always set one explicitly""",
        "rust": """\
- Borrow checker: you cannot have mutable and immutable refs simultaneously
- `String` vs `&str`: `String` owns data; `&str` is a borrowed slice
- `clone()` is explicit — suspicious if overused in hot paths
- Trait objects (`dyn Trait`) have runtime cost; generics are zero-cost
- `unwrap()` panics at runtime — use `?` or `match` in production code
- Lifetimes in structs: lifetime of struct ≤ lifetime of borrowed field
- Async: `.await` only works inside `async fn`; don't block in async context""",
        "python": """\
- Mutable default arguments: `def f(x=[])` shares the list across calls — use `None`
- Late binding closures in lambdas/loops: capture variable, not value
- `__init__.py` imports affect package import time — keep them minimal
- `pytest` fixture scope: module-scoped fixtures shared between tests (side effects!)
- `ruff` replaces both `flake8` and `isort` — don't run both""",
    }

    return gotchas.get(
        lang,
        """\
- Check existing issues before starting new work
- Run tests before committing
- Review diff before pushing""",
    )


def _get_language_dont_do(lang: str) -> str:
    dont_dos = {
        "go": """\
- Do not use `panic` for expected error cases
- Do not ignore errors with `_`
- Do not use `init()` for complex initialization
- Do not commit `vendor/` unless explicitly required""",
        "rust": """\
- Do not use `unwrap()` or `expect()` in library crate code
- Do not use `unsafe` without a detailed comment explaining why
- Do not commit `Cargo.lock` deletions for binary crates
- Do not ignore clippy warnings — they exist for good reasons""",
        "python": """\
- Do not use bare `except:` — always specify the exception type
- Do not use `os.system()` — use `subprocess.run()` with check=True
- Do not mutate function default arguments""",
    }
    return dont_dos.get(lang, "")
