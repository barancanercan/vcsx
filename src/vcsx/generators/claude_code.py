"""Claude Code generator — produces CLAUDE.md, skills, hooks, agents."""

import json
import stat
from pathlib import Path

from vcsx.core.context import ProjectContext
from vcsx.core.inference import infer_formatter, infer_linter, infer_test_framework
from vcsx.generators.base import BaseGenerator


class ClaudeCodeGenerator(BaseGenerator):
    """Generates a complete Claude Code setup."""

    @property
    def name(self) -> str:
        return "claude-code"

    @property
    def output_files(self) -> list[str]:
        return [
            "CLAUDE.md",
            ".claude/settings.json",
            ".claude/skills/*/SKILL.md",
            ".claude/agents/*.md",
            ".claude/hooks/*.sh",
        ]

    def generate_config(self, ctx: ProjectContext, output_dir: str) -> str:
        """Generate CLAUDE.md file."""
        lines = [
            f"# {ctx.project_name} — CLAUDE.md",
            "",
            "## Project Overview",
            ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack}.",
            "",
            "## Quick Commands",
            "",
            "### Setup",
            "```bash",
            _get_setup_cmd(ctx),
            "```",
            "",
            "### Build",
            "```bash",
            _get_build_cmd(ctx),
            "```",
            "",
            "### Lint & Format",
            "```bash",
            f"{ctx.linter or infer_linter(ctx.language)} src/",
            f"{ctx.formatter or infer_formatter(ctx.language)} src/",
            "```",
            "",
            "### Test",
            "```bash",
            _get_test_cmd(ctx),
            "```",
            "",
            "### Run Single Test",
            "```bash",
            _get_single_test_cmd(ctx),
            "```",
            "",
            "## Code Style",
            "",
            *_get_style_rules(ctx),
            "",
            "## Architecture",
            "",
            f"- **Type**: {ctx.project_type}",
            f"- **Language**: {ctx.language}",
            f"- **Framework**: {ctx.framework or 'None'}",
            f"- **Hosting**: {ctx.hosting or 'TBD'}",
            f"- **Auth**: {ctx.auth_method if ctx.auth_needed else 'None'}",
            "",
            "## Absolute Rules",
            "",
            "- NEVER commit secrets or API keys",
            "- NEVER run destructive commands without explicit confirmation",
            "- ALWAYS run tests before committing",
            "- ALWAYS follow existing code patterns",
            "- Keep CLAUDE.md under 200 lines — move domain knowledge to skills",
            "",
            "## Skills (Auto-Triggered)",
            "",
            "- `/commit-message` — Generate conventional commit messages",
            "- `/pr-review` — Review against team standards",
            "- `/deploy` — Deployment checklist",
        ]

        if ctx.auth_needed:
            lines.append("- `/auth-conventions` — Auth patterns and flows")
        if ctx.project_type == "api":
            lines.append("- `/api-conventions` — REST API design patterns")
        if ctx.test_level != "none":
            lines.append("- `/test-patterns` — Test writing conventions")

        lines.extend(
            [
                "",
                "## Hooks (Deterministic)",
                "",
                "- PreToolUse: Blocks destructive commands (rm -rf, git push --force)",
                f"- PostToolUse: Auto-runs {ctx.formatter or 'prettier'} on file changes",
                f"- PostToolUse: Auto-runs {ctx.linter or 'eslint'} after edits",
                "",
            ]
        )

        content = "\n".join(lines)
        (Path(output_dir) / "CLAUDE.md").write_text(content, encoding="utf-8")
        return content

    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate all skill files."""
        skills_dir = Path(output_dir) / ".claude" / "skills"
        created = []

        created.append(_skill_commit_message(skills_dir))
        created.append(_skill_pr_review(skills_dir))
        created.append(_skill_deploy(skills_dir, ctx))
        created.append(_skill_squash(skills_dir))
        created.append(_skill_revert(skills_dir))
        created.append(_skill_rollback(skills_dir, ctx))
        created.append(_skill_migration(skills_dir, ctx))
        created.append(_skill_orm_conventions(skills_dir, ctx))
        created.append(_skill_docker_conventions(skills_dir))
        created.append(_skill_k8s_conventions(skills_dir))
        created.append(_skill_ci_cd_builder(skills_dir, ctx))
        created.append(_skill_mutation_testing(skills_dir, ctx))
        created.append(_skill_e2e_patterns(skills_dir))
        created.append(_skill_performance(skills_dir))
        created.append(_skill_debt_analyzer(skills_dir))
        created.append(_skill_openapi_generator(skills_dir))
        created.append(_skill_grpc_conventions(skills_dir))
        created.append(_skill_query_optimization(skills_dir))

        if ctx.auth_needed:
            created.append(_skill_auth(skills_dir, ctx))
        if ctx.project_type == "api":
            created.append(_skill_api_conventions(skills_dir))
        if ctx.test_level != "none":
            created.append(_skill_test_patterns(skills_dir, ctx))

        created.append(_skill_security_review(skills_dir))
        created.append(_skill_refactor(skills_dir))

        return created

    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> dict:
        """Generate hooks configuration and scripts."""
        claude_dir = Path(output_dir) / ".claude"
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        formatter = ctx.formatter or infer_formatter(ctx.language)
        linter = ctx.linter or infer_linter(ctx.language)
        test_cmd = ctx.test_framework or "pytest"

        # Platform detection for script extension
        platform = getattr(ctx, "platform", "") or "macos"
        is_windows = platform in ("windows-powershell", "wsl")
        ext = ".ps1" if platform == "windows-powershell" else ".sh"

        # Generate platform-specific scripts
        scripts = {
            "block_destructive": _script_block_destructive(hooks_dir, ext),
            "validate_syntax": _script_validate_syntax(hooks_dir, ctx.language, ext),
            "check_permissions": _script_check_permissions(hooks_dir, ext),
            "check_env": _script_check_env(hooks_dir, ext),
            "check_deps": _script_check_deps(hooks_dir, ext),
            "git_status": _script_git_status(hooks_dir, ext),
            "run_tests": _script_run_tests(hooks_dir, test_cmd, ext),
            "cleanup_temp": _script_cleanup_temp(hooks_dir, ext),
            "commit_prompt": _script_commit_prompt(hooks_dir, ext),
            "type_check": _script_type_check(hooks_dir, ctx.language, ext),
            "auto_format": _script_auto_format(hooks_dir, formatter, ext),
            "auto_lint": _script_auto_lint(hooks_dir, linter, ext),
            "secret_scan": _script_secret_scan(hooks_dir, ext),
        }

        settings = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": scripts["block_destructive"],
                                "statusMessage": "Checking for destructive commands...",
                            },
                            {
                                "type": "command",
                                "command": scripts["validate_syntax"],
                                "statusMessage": "Validating syntax...",
                            },
                            {
                                "type": "command",
                                "command": scripts["check_permissions"],
                                "statusMessage": "Checking permissions...",
                            },
                        ],
                    }
                ],
                "PostToolUse": [
                    {
                        "matcher": "Write|Edit",
                        "hooks": [
                            {
                                "type": "command",
                                "command": scripts["auto_format"],
                                "statusMessage": "Auto-formatting file...",
                            },
                            {
                                "type": "command",
                                "command": scripts["auto_lint"],
                                "statusMessage": "Linting file...",
                            },
                            {
                                "type": "command",
                                "command": scripts["type_check"],
                                "statusMessage": "Type checking...",
                            },
                            {
                                "type": "command",
                                "command": scripts["secret_scan"],
                                "statusMessage": "Scanning for secrets...",
                            },
                        ],
                    }
                ],
                "SessionStart": [
                    {
                        "matcher": ".*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": scripts["check_env"],
                                "statusMessage": "Checking environment...",
                            },
                            {
                                "type": "command",
                                "command": scripts["check_deps"],
                                "statusMessage": "Checking dependencies...",
                            },
                            {
                                "type": "command",
                                "command": scripts["git_status"],
                                "statusMessage": "Checking git status...",
                            },
                        ],
                    }
                ],
                "Stop": [
                    {
                        "matcher": ".*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": scripts["run_tests"],
                                "statusMessage": "Running test suite...",
                            },
                            {
                                "type": "command",
                                "command": scripts["cleanup_temp"],
                                "statusMessage": "Cleaning up temp files...",
                            },
                            {
                                "type": "command",
                                "command": scripts["commit_prompt"],
                                "statusMessage": "Checking for uncommitted changes...",
                            },
                        ],
                    }
                ],
            }
        }

        (claude_dir / "settings.json").write_text(
            json.dumps(settings, indent=2) + "\n", encoding="utf-8"
        )
        return settings

    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate subagent definitions."""
        agents_dir = Path(output_dir) / ".claude" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        created = []

        created.append(_agent_security_reviewer(agents_dir, ctx))
        if ctx.test_level != "none":
            created.append(_agent_test_writer(agents_dir, ctx))
        created.append(_agent_researcher(agents_dir))

        return created

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate project scaffold files."""
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


# ─── Skill Templates ─────────────────────────────────────────────────────────


def _skill_commit_message(skills_dir: Path) -> str:
    d = skills_dir / "commit-message"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: commit-message
description: Generates conventional commit messages from git diff. Use when committing changes or when the user asks to commit.
---

# Commit Message Skill

Generate conventional commit messages: `<type>(<scope>): <description>`

## Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependencies

## Process
1. Run `git diff --cached` to see staged changes
2. Analyze changes to determine type
3. Generate concise description (max 72 chars)
4. If multiple types, suggest separate commits
5. Run `git commit -m "<message>"`
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "commit-message"


def _skill_pr_review(skills_dir: Path) -> str:
    d = skills_dir / "pr-review"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: pr-review
description: Reviews pull requests against team standards before submission. Use when creating a PR or reviewing changes.
---

# PR Review Skill

## Checklist
- [ ] Code follows project style guidelines
- [ ] No secrets or API keys committed
- [ ] Tests cover new functionality
- [ ] Error handling is appropriate
- [ ] No unnecessary dependencies
- [ ] Documentation updated if needed

## Process
1. Run `git diff main...HEAD`
2. Check each file against checklist
3. Report findings with line references
4. Suggest fixes for issues found
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "pr-review"


def _skill_deploy(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "deploy"
    d.mkdir(parents=True, exist_ok=True)
    hosting = ctx.hosting or "your hosting provider"
    content = f"""---
name: deploy
description: Deploys the application to {hosting}. Use when deploying or when the user asks to deploy.
disable-model-invocation: true
---

# Deployment Skill

## Pre-Deployment Checklist
- [ ] All tests pass
- [ ] Linting passes with no errors
- [ ] Build succeeds
- [ ] No secrets in code
- [ ] Environment variables configured

## Steps
1. Verify build: {_get_build_cmd(ctx)}
2. Run tests: {_get_test_cmd(ctx)}
3. Deploy to {hosting}
4. Verify deployment (health check, logs)
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "deploy"


def _skill_auth(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "auth-conventions"
    d.mkdir(parents=True, exist_ok=True)
    content = f"""---
name: auth-conventions
description: Authentication patterns and flows using {ctx.auth_method}. Use when working with auth code.
---

# Auth Conventions

## Method: {ctx.auth_method}

## Patterns
- All protected endpoints require valid auth token
- Tokens stored securely (httpOnly cookies or secure storage)
- Refresh tokens rotated on each use
- Failed attempts logged but don't expose user existence

## Security
- Never log tokens or passwords
- Use bcrypt or equivalent for password hashing
- Implement CSRF protection for web apps
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "auth-conventions"


def _skill_api_conventions(skills_dir: Path) -> str:
    d = skills_dir / "api-conventions"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: api-conventions
description: REST API design patterns and endpoint naming conventions. Use when creating or modifying API endpoints.
---

# API Conventions

## URL Design
- kebab-case for paths: `/api/user-profiles`
- Nouns not verbs: `/api/users`
- Version in URL: `/api/v1/users`
- Plural nouns for collections

## HTTP Methods
- GET — Retrieve, POST — Create, PUT — Update, PATCH — Partial, DELETE — Remove

## Response Format
```json
{"data": {...}, "meta": {"page": 1, "perPage": 20, "total": 100}}
```

## Error Format
```json
{"error": {"code": "VALIDATION_ERROR", "message": "...", "details": []}}
```
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "api-conventions"


def _skill_test_patterns(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "test-patterns"
    d.mkdir(parents=True, exist_ok=True)
    content = f"""---
name: test-patterns
description: Test writing patterns using {ctx.test_framework or infer_test_framework(ctx.language)}. Use when writing tests.
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
- Test edge cases and error conditions
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "test-patterns"


def _skill_security_review(skills_dir: Path) -> str:
    d = skills_dir / "security-review"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: security-review
description: Reviews code for security vulnerabilities. Use when reviewing code or before merging.
---

# Security Review Skill

## Checklist
- Injection vulnerabilities (SQL, XSS, command)
- Authentication and authorization flaws
- Secrets or credentials in code
- Insecure data handling
- Missing input validation
- Unsafe deserialization
- Path traversal vulnerabilities

## Process
1. Read the files in question
2. Check each item on checklist
3. Provide specific line references
4. Suggest concrete fixes
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "security-review"


def _skill_refactor(skills_dir: Path) -> str:
    d = skills_dir / "refactor"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: refactor
description: Suggests code improvements while maintaining behavior. Use when asked to refactor or improve code.
---

# Refactor Skill

## Principles
- Maintain existing behavior
- Improve readability
- Reduce complexity
- Follow DRY and SOLID
- Keep functions small

## Process
1. Read the code to understand intent
2. Identify code smells
3. Suggest specific improvements
4. Apply changes incrementally
5. Run tests to verify behavior unchanged
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "refactor"


def _skill_squash(skills_dir: Path) -> str:
    d = skills_dir / "squash"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: squash
description: Squashes multiple commits into one using git rebase. Use when cleaning up commit history before merging.
---

# Squash Skill

## When to Use
- Before merging a feature branch
- After code review feedback
- When commits are too granular

## Process
1. List commits: git log
2. Determine number to squash: git rebase -i HEAD~n
3. Change 'pick' to 'squash' for commits to combine
4. Write new commit message
5. Force push if needed
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "squash"


def _skill_revert(skills_dir: Path) -> str:
    d = skills_dir / "revert"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: revert
description: Reverts changes using git revert with proper commit messages. Use when undoing specific changes without losing history.
---

# Revert Skill

## When to Use
- Undo a committed change
- Reverse a deployment
- Rollback a merge

## Process
1. Identify commit to revert: git log
2. Revert with: git revert <commit>
3. Write revert commit message
4. Push changes
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "revert"


def _skill_rollback(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "rollback"
    d.mkdir(parents=True, exist_ok=True)
    hosting = ctx.hosting or "deployment platform"
    content = f"""---
name: rollback
description: Rolls back deployment to previous version on {hosting}. Use when deployment fails or issues are detected.
---

# Rollback Skill

## Pre-Flight Checks
- [ ] Current deployment is broken
- [ ] Previous version was stable
- [ ] Database migration not required

## Process
1. Check deployment history
2. Verify previous stable version
3. Execute rollback command
4. Verify health check passes
5. Document incident
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "rollback"


def _skill_migration(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "migration"
    d.mkdir(parents=True, exist_ok=True)
    content = f"""---
name: migration
description: Generates database migration files using {ctx.test_framework or "ORM"}. Use when creating database schema changes.
---

# Migration Skill

## Framework: {ctx.test_framework or "SQLAlchemy/Django ORM"}

## Process
1. Generate migration: alembic revision --autogenerate
2. Review generated migration
3. Apply locally: alembic upgrade head
4. Test rollback: alembic downgrade -1
5. Commit migration file

## Guidelines
- Never modify committed migrations
- Always include rollback
- Test on staging first
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "migration"


def _skill_orm_conventions(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "orm-conventions"
    d.mkdir(parents=True, exist_ok=True)
    content = f"""---
name: orm-conventions
description: Database ORM patterns and conventions for {ctx.language}. Use when defining models or querying data.
---

# ORM Conventions

## Language: {ctx.language}

## Patterns
- Use migrations for schema changes
- Define relationships explicitly
- Use migrations for data changes
- Index foreign keys

## Best Practices
- Never hardcode credentials
- Use connection pooling
- Implement soft deletes where appropriate
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "orm-conventions"


def _skill_docker_conventions(skills_dir: Path) -> str:
    d = skills_dir / "docker-conventions"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: docker-conventions
description: Docker container best practices and Dockerfile conventions. Use when containerizing applications.
---

# Docker Conventions

## Dockerfile Guidelines
- Use official base images
- Pin versions in FROM
- Use multi-stage builds
- Minimize layers
- Use .dockerignore

## Security
- Never run as root
- Use read-only filesystem
- Scan for vulnerabilities

## Best Practices
- Health checks required
- Use specific tags, not latest
- Clean up in same layer
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "docker-conventions"


def _skill_k8s_conventions(skills_dir: Path) -> str:
    d = skills_dir / "k8s-conventions"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: k8s-conventions
description: Kubernetes deployment conventions and YAML patterns. Use when deploying to Kubernetes.
---

# Kubernetes Conventions

## Resource Types
- Deployment for stateless apps
- StatefulSet for stateful apps
- Job for batch operations

## Best Practices
- Use liveness/readiness probes
- Resource limits required
- Use ConfigMaps for config
- Use Secrets for sensitive data

## Security
- Never run privileged
- Use RBAC
- Network policies
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "k8s-conventions"


def _skill_ci_cd_builder(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "ci-cd-builder"
    d.mkdir(parents=True, exist_ok=True)
    content = f"""---
name: ci-cd-builder
description: Builds CI/CD pipeline configuration for {ctx.project_type} projects. Use when setting up automated pipelines.
---

# CI/CD Builder

## Project Type: {ctx.project_type}

## Pipeline Stages
1. Lint
2. Test
3. Build
4. Deploy

## Tools
- GitHub Actions / GitLab CI / ArgoCD
- Docker for containerization
- Cloud-native deployments
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "ci-cd-builder"


def _skill_mutation_testing(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "mutation-testing"
    d.mkdir(parents=True, exist_ok=True)
    content = f"""---
name: mutation-testing
description: Mutation testing setup using {ctx.test_framework or "mutmut"}. Use when validating test quality.
---

# Mutation Testing

## Framework: {ctx.test_framework or "mutmut"}

## Process
1. Install mutation testing library
2. Run mutation tests
3. Review killed mutations
4. Improve weak tests

## Metrics
- Mutation Score Indicator (MSI)
- Coverage percentage
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "mutation-testing"


def _skill_e2e_patterns(skills_dir: Path) -> str:
    d = skills_dir / "e2e-patterns"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: e2e-patterns
description: End-to-end testing patterns and best practices. Use when writing E2E tests.
---

# E2E Patterns

## Framework
- Playwright / Cypress / Puppeteer

## Best Practices
- Test critical user flows
- Use realistic test data
- Clean up after tests
- Parallel where possible
- Screenshot on failure
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "e2e-patterns"


def _skill_performance(skills_dir: Path) -> str:
    d = skills_dir / "performance"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: performance
description: Performance optimization patterns and profiling techniques. Use when optimizing application performance.
---

# Performance Skill

## Profiling
- CPU profiling
- Memory profiling
- Network profiling

## Optimization Areas
- Database queries
- Algorithm complexity
- Caching strategies
- Bundle size
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "performance"


def _skill_debt_analyzer(skills_dir: Path) -> str:
    d = skills_dir / "debt-analyzer"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: debt-analyzer
description: Analyzes code for technical debt and code smells. Use when assessing code quality.
---

# Technical Debt Analyzer

## Metrics
- Cyclomatic complexity
- Coupling
- Code duplication
- Missing documentation

## Tools
- SonarQube
- CodeClimate
- SonarLint

## Process
1. Run analysis
2. Review high-priority issues
3. Create refactoring tickets
4. Track debt over time
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "debt-analyzer"


def _skill_openapi_generator(skills_dir: Path) -> str:
    d = skills_dir / "openapi-generator"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: openapi-generator
description: Generates API documentation and client code from OpenAPI specs. Use when building APIs.
---

# OpenAPI Generator

## Workflow
1. Write OpenAPI spec (YAML/JSON)
2. Generate server stubs
3. Generate client SDKs
4. Generate documentation

## Tools
- OpenAPI Generator
- Swagger UI
- Redoc
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "openapi-generator"


def _skill_grpc_conventions(skills_dir: Path) -> str:
    d = skills_dir / "grpc-conventions"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: grpc-conventions
description: gRPC service design patterns and protobuf conventions. Use when building gRPC services.
---

# gRPC Conventions

## Protocol Buffers
- Use proto3 syntax
- Define services and messages
- Use well-known types

## Best Practices
- Version your protos
- Use streaming sparingly
- Implement proper error handling
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "grpc-conventions"


def _skill_query_optimization(skills_dir: Path) -> str:
    d = skills_dir / "query-optimization"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: query-optimization
description: Database query optimization techniques and indexing strategies. Use when optimizing database performance.
---

# Query Optimization

## Techniques
- Analyze query plans
- Add appropriate indexes
- Avoid SELECT *
- Use pagination
- Implement caching

## Anti-Patterns
- N+1 queries
- Missing indexes
- Full table scans
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "query-optimization"


# ─── Hook Scripts ────────────────────────────────────────────────────────────


def _get_script_header(ext: str) -> str:
    """Get appropriate script header based on file extension."""
    if ext == ".ps1":
        return "#!/usr/bin/env pwsh"
    else:
        return "#!/bin/bash"


def _script_block_destructive(hooks_dir: Path, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"block_destructive{ext}"
    p = hooks_dir / filename

    if is_ps:
        content = """$Input | ForEach-Object {
    $cmd = $_ -replace '.*"command"[^"]*"([^"]*)".*', '$1'
    $patterns = @('rm -rf', 'rm -r /', 'git push --force', 'git push -f', 'DROP TABLE', 'DROP DATABASE', 'DELETE FROM', 'TRUNCATE', 'mkfs', 'dd if=')
    foreach ($pat in $patterns) {
        if ($cmd -match $pat) {
            Write-Error "BLOCKED: Destructive command: $pat"
            exit 2
        }
    }
}
exit 0
"""
    else:
        content = """#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\(.*\)"/\1/')

PATTERNS=("rm -rf" "rm -r /" "git push --force" "git push -f" "DROP TABLE" "DROP DATABASE" "DELETE FROM" "TRUNCATE" "mkfs" "dd if=" "sudo rm")

for pattern in "${PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qi "$pattern"; then
        echo "BLOCKED: Destructive command: $pattern" >&2
        exit 2
    fi
done
exit 0
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _script_validate_syntax(hooks_dir: Path, language: str, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"validate_syntax{ext}"
    p = hooks_dir / filename
    linters = {
        "typescript": "tsc --noEmit",
        "python": "python -m py_compile",
        "go": "go build",
        "rust": "cargo check",
    }
    cmd = linters.get(language, "echo 'No syntax checker for this language'")

    if is_ps:
        content = f"""$Input | ForEach-Object {{
    $file = $_ -replace '.*"file_path"[^"]*"([^"]*)".*', '$1'
    if (-not $file) {{ exit 0 }}
    {cmd} $file 2>&1
}}
exit 0
"""
    else:
        content = f"""#!/bin/bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\\(.*\\)"/\\1/')
[ -z "$FILE" ] && exit 0
{cmd} "$FILE" 2>&1
exit 0
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _script_check_permissions(hooks_dir: Path, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"check_permissions{ext}"
    p = hooks_dir / filename

    if is_ps:
        content = """$Input | ForEach-Object {
    $cmd = $_ -replace '.*"command"[^"]*"([^"]*)".*', '$1'
    $patterns = @('chmod 777', 'chown', 'sudo chown', 'sudo chmod')
    foreach ($pat in $patterns) {
        if ($cmd -match $pat) {
            Write-Warning "Permission change command: $pat"
        }
    }
}
exit 0
"""
    else:
        content = r"""#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\(.*\)"/\1/')

DANGEROUS_PATTERNS=("chmod 777" "chown" "sudo chown" "sudo chmod")

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qi "$pattern"; then
        echo "WARNING: Permission change command: $pattern" >&2
    fi
done
exit 0
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _script_check_env(hooks_dir: Path, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"check_env{ext}"
    p = hooks_dir / filename

    if is_ps:
        content = r"""if (-not $env:NODE_ENV) { Write-Warning "NODE_ENV not set" }
if (-not $env:DATABASE_URL) { Write-Warning "DATABASE_URL not set" }
exit 0
"""
    else:
        content = r"""#!/bin/bash
[ -z "$NODE_ENV" ] && echo "WARNING: NODE_ENV not set" >&2
[ -z "$DATABASE_URL" ] && echo "WARNING: DATABASE_URL not set" >&2
exit 0
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _script_check_deps(hooks_dir: Path, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"check_deps{ext}"
    p = hooks_dir / filename

    if is_ps:
        content = r"""if (Test-Path "package.json" -and -not (Test-Path "node_modules")) { Write-Warning "Run npm install" }
if (Test-Path "requirements.txt" -and -not ((Test-Path ".venv") -or (Test-Path "venv"))) { Write-Warning "Create virtual environment" }
if (Test-Path "go.mod" -and -not (Test-Path "go.sum")) { Write-Warning "Run go mod tidy" }
exit 0
"""
    else:
        content = r"""#!/bin/bash
if [ -f "package.json" ]; then
    [ ! -d "node_modules" ] && echo "WARNING: Run npm install" >&2
fi
if [ -f "requirements.txt" ]; then
    [ ! -d ".venv" ] && [ ! -d "venv" ] && echo "WARNING: Create virtual environment" >&2
fi
if [ -f "go.mod" ]; then
    [ ! -f "go.sum" ] && echo "WARNING: Run go mod tidy" >&2
fi
exit 0
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _script_git_status(hooks_dir: Path, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"git_status{ext}"
    p = hooks_dir / filename

    if is_ps:
        content = r"""if (Test-Path ".git") {
    $unstaged = (git status --porcelain | Where-Object { $_ -match "^.M" }).Count
    $untracked = (git status --porcelain | Where-Object { $_ -match "^\?\?" }).Count
    if ($unstaged -gt 0) { Write-Host "INFO: $unstaged unstaged files" }
    if ($untracked -gt 0) { Write-Host "INFO: $untracked untracked files" }
}
exit 0
"""
    else:
        content = r"""#!/bin/bash
if [ -d ".git" ]; then
    UNSTAGED=$(git status --porcelain | grep "^.M" | wc -l)
    UNTRACKED=$(git status --porcelain | grep "^??" | wc -l)
    [ "$UNSTAGED" -gt 0 ] && echo "INFO: $UNSTAGED unstaged files" >&2
    [ "$UNTRACKED" -gt 0 ] && echo "INFO: $UNTRACKED untracked files" >&2
fi
exit 0
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _script_run_tests(hooks_dir: Path, test_cmd: str, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"run_tests{ext}"
    p = hooks_dir / filename

    if is_ps:
        content = f"""Write-Host "Running test suite..."
{test_cmd}
$exitCode = $LASTEXITCODE
if ($exitCode -eq 0) {{ Write-Host "All tests passed" }}
else {{ Write-Error "Tests failed with exit code $exitCode" }}
exit $exitCode
"""
    else:
        content = f"""#!/bin/bash
echo "Running test suite..."
{test_cmd}
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "All tests passed"
else
    echo "Tests failed with exit code $EXIT_CODE" >&2
fi
exit $EXIT_CODE
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _script_cleanup_temp(hooks_dir: Path, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"cleanup_temp{ext}"
    p = hooks_dir / filename

    if is_ps:
        content = r"""Get-ChildItem -Recurse -Filter "*.tmp" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter ".pytest_cache" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
exit 0
"""
    else:
        content = r"""#!/bin/bash
find . -name "*.tmp" -delete 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null
exit 0
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _script_commit_prompt(hooks_dir: Path, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"commit_prompt{ext}"
    p = hooks_dir / filename

    if is_ps:
        content = r"""if (Test-Path ".git") {
    $changes = git status --porcelain
    if ($changes) {
        Write-Host "Uncommitted changes detected. Consider committing before ending session."
        git diff --stat
    }
}
exit 0
"""
    else:
        content = r"""#!/bin/bash
if [ -d ".git" ]; then
    CHANGES=$(git status --porcelain)
    if [ -n "$CHANGES" ]; then
        echo "Uncommitted changes detected. Consider committing before ending session."
        git diff --stat
    fi
fi
exit 0
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _script_type_check(hooks_dir: Path, language: str, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"type_check{ext}"
    p = hooks_dir / filename
    type_checkers = {
        "typescript": "tsc --noEmit",
        "python": "mypy src/",
        "go": "go vet ./...",
    }
    cmd = type_checkers.get(language, "echo 'No type checker for this language'")

    if is_ps:
        content = f"""$Input | ForEach-Object {{
    $file = $_ -replace '.*"file_path"[^"]*"([^"]*)".*', '$1'
    if (-not $file) {{ exit 0 }}
    {cmd} $file 2>&1
}}
exit 0
"""
    else:
        content = f"""#!/bin/bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\\(.*\\)"/\\1/')
[ -z "$FILE" ] && exit 0
{cmd} "$FILE" 2>&1
exit 0
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _script_auto_format(hooks_dir: Path, formatter: str, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"auto_format{ext}"
    p = hooks_dir / filename

    if is_ps:
        content = f"""$Input | ForEach-Object {{
    $file = $_ -replace '.*"file_path"[^"]*"([^"]*)".*', '$1'
    if (-not $file) {{ exit 0 }}
    {formatter} $file 2>$null
}}
exit 0
"""
    else:
        content = f"""#!/bin/bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\\(.*\\)"/\\1/')
[ -z "$FILE" ] && exit 0
{formatter} "$FILE" 2>/dev/null || true
exit 0
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _script_auto_lint(hooks_dir: Path, linter: str, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"auto_lint{ext}"
    p = hooks_dir / filename

    if is_ps:
        content = f"""$Input | ForEach-Object {{
    $file = $_ -replace '.*"file_path"[^"]*"([^"]*)".*', '$1'
    if (-not $file) {{ exit 0 }}
    {linter} $file 2>$null
}}
exit 0
"""
    else:
        content = f"""#!/bin/bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\\(.*\\)"/\\1/')
[ -z "$FILE" ] && exit 0
{linter} "$FILE" 2>/dev/null || true
exit 0
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def _script_secret_scan(hooks_dir: Path, ext: str = ".sh") -> str:
    is_ps = ext == ".ps1"
    filename = f"secret_scan{ext}"
    p = hooks_dir / filename

    if is_ps:
        content = r"""$Input | ForEach-Object {
    $file = $_ -replace '.*"file_path"[^"]*"([^"]*)".*', '$1'
    if (-not $file -or -not (Test-Path $file)) { exit 0 }
    $patterns = @('api[_-]?key', 'secret[_-]?key', 'access[_-]?token', 'private[_-]?key', 'password', 'aws_access_key', 'ghp_', 'sk-', 'BEGIN.*PRIVATE KEY')
    foreach ($pat in $patterns) {
        if (Select-String -Path $file -Pattern $pat -Quiet) {
            Write-Warning "Potential secret in $file : $pat"
        }
    }
}
exit 0
"""
    else:
        content = r"""#!/bin/bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\\(.*\\)"/\1/')
[ -z "$FILE" ] || [ ! -f "$FILE" ] && exit 0

PATTERNS=("api[_-]?key" "secret[_-]?key" "access[_-]?token" "private[_-]?key" "password" "aws_access_key" "ghp_[a-zA-Z0-9]" "sk-[a-zA-Z0-9]" "BEGIN.*PRIVATE KEY")

for pattern in "${PATTERNS[@]}"; do
    if grep -qi "$pattern" "$FILE" 2>/dev/null; then
        echo "WARNING: Potential secret in $FILE: $pattern" >&2
    fi
done
exit 0
"""

    p.write_text(content, encoding="utf-8")
    if ext != ".ps1":
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


# ─── Agent Templates ─────────────────────────────────────────────────────────


def _agent_security_reviewer(agents_dir: Path, ctx: ProjectContext) -> str:
    content = f"""---
name: security-reviewer
description: Reviews code for security vulnerabilities
tools: Read, Grep, Glob, Bash
---

You are a senior security engineer. Review code for:

## Checklist
- Injection vulnerabilities (SQL, XSS, command injection)
- Authentication and authorization flaws
- Secrets or credentials in code
- Insecure data handling
- Missing input validation

## Process
1. Read the files
2. Check each item on checklist
3. Provide specific line references
4. Suggest concrete fixes

## Context
- Language: {ctx.language}
- Framework: {ctx.framework or "None"}
"""
    p = agents_dir / "security-reviewer.md"
    p.write_text(content, encoding="utf-8")
    return "security-reviewer"


def _agent_test_writer(agents_dir: Path, ctx: ProjectContext) -> str:
    content = f"""---
name: test-writer
description: Writes comprehensive tests for code changes
tools: Read, Grep, Glob, Write, Bash
---

You are a senior QA engineer. Write tests that:

## Guidelines
- Test behavior, not implementation
- Cover happy path and edge cases
- Test error conditions
- Use descriptive test names

## Framework: {ctx.test_framework or infer_test_framework(ctx.language)}

## Structure
1. Arrange — Set up test data
2. Act — Execute code under test
3. Assert — Verify outcome
"""
    p = agents_dir / "test-writer.md"
    p.write_text(content, encoding="utf-8")
    return "test-writer"


def _agent_researcher(agents_dir: Path) -> str:
    content = """---
name: researcher
description: Investigates codebase questions and returns concise summaries
tools: Read, Grep, Glob
---

You are a codebase researcher. Answer the specific question asked.

## Guidelines
- Reference exact file paths and line numbers
- Be concise — summaries over details
- Note uncertainties explicitly

## Output Format
```
## Research Summary: [Question]

### Findings
- [Finding] (file:line)

### Conclusion
[Brief answer]
```
"""
    p = agents_dir / "researcher.md"
    p.write_text(content, encoding="utf-8")
    return "researcher"


# ─── Scaffold ────────────────────────────────────────────────────────────────


def _scaffold_gitignore(output_dir: str, ctx: ProjectContext) -> str:
    lines = [
        "# Dependencies",
        "node_modules/",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        "venv/",
        "vendor/",
        "target/",
        "",
        "# Build outputs",
        "dist/",
        "build/",
        "*.egg-info/",
        "",
        "# Environment",
        ".env",
        ".env.local",
        ".env.*.local",
        "!.env.example",
        "",
        "# IDE",
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        "",
        "# OS",
        ".DS_Store",
        "Thumbs.db",
        "",
        "# Test coverage",
        "coverage/",
        ".nyc_output/",
        "htmlcov/",
        "",
        "# Logs",
        "*.log",
        "npm-debug.log*",
    ]
    p = Path(output_dir) / ".gitignore"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ".gitignore"


def _scaffold_readme(output_dir: str, ctx: ProjectContext) -> str:
    content = f"""# {ctx.project_name}

{ctx.description or f"A {ctx.project_type} project built with {ctx.tech_stack}."}

## Quick Start

### Setup
```bash
{_get_setup_cmd(ctx)}
```

### Development
```bash
{_get_run_cmd(ctx)}
```

### Testing
```bash
{_get_test_cmd(ctx)}
```

## Architecture

- **Type**: {ctx.project_type}
- **Language**: {ctx.language}
- **Framework**: {ctx.framework or "None"}
- **Hosting**: {ctx.hosting or "TBD"}
{f"- **Auth**: {ctx.auth_method}" if ctx.auth_needed else ""}

## Claude Code Setup

This project includes a production-ready Claude Code environment:
- `CLAUDE.md` — Project conventions and commands
- `.claude/skills/` — Reusable workflows
- `.claude/settings.json` — Automated hooks
- `.claude/agents/` — Specialized subagents

## License

MIT
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
        "",
    ]
    if ctx.auth_needed:
        lines.extend(["# Auth", "JWT_SECRET=your-secret-key-here", ""])
    lines.extend(
        [
            "# External Services",
            "# Add your service keys here",
        ]
    )
    p = Path(output_dir) / ".env.example"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ".env.example"


def _scaffold_tsconfig(output_dir: str) -> str:
    content = """{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "baseUrl": ".",
    "paths": {"@/*": ["src/*"]}
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
"""
    p = Path(output_dir) / "tsconfig.json"
    p.write_text(content, encoding="utf-8")
    return "tsconfig.json"


def _scaffold_package_json(output_dir: str, ctx: ProjectContext) -> str:
    import json

    content = {
        "name": ctx.project_name,
        "version": "0.1.0",
        "description": ctx.description or "",
        "type": "module",
        "scripts": {
            "dev": "echo 'Add your dev command'",
            "build": "echo 'Add your build command'",
            "start": "echo 'Add your start command'",
            "test": "npx vitest run",
            "test:watch": "npx vitest",
            "lint": "eslint src/",
            "lint:fix": "eslint src/ --fix",
            "format": "prettier --write src/",
            "typecheck": "tsc --noEmit",
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
        "# Core dependencies",
        "# Add your dependencies here",
        "",
        "# Development",
        "pytest>=7.0",
        "pytest-cov>=4.0",
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
description = "{ctx.description or ""}"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
disallow_untyped_defs = true
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
                "src/utils",
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
                "src/styles",
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


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _get_setup_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm install",
        "javascript": "npm install",
        "python": "pip install -r requirements.txt",
        "go": "go mod tidy",
        "rust": "cargo build",
        "java": "mvn install",
    }.get(ctx.language, "npm install")


def _get_build_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm run build",
        "javascript": "npm run build",
        "python": "python -m compileall src/",
        "go": "go build ./...",
        "rust": "cargo build --release",
        "java": "mvn package",
    }.get(ctx.language, "npm run build")


def _get_run_cmd(ctx: ProjectContext) -> str:
    return {
        "typescript": "npm run dev",
        "javascript": "npm run dev",
        "python": "python -m src.main",
        "go": "go run ./cmd/main.go",
    }.get(ctx.language, "npm run dev")


def _get_test_cmd(ctx: ProjectContext) -> str:
    if ctx.test_level == "none":
        return "# No tests configured"
    return {
        "vitest": "npx vitest run",
        "jest": "npx jest",
        "pytest": "pytest",
        "go test": "go test ./...",
        "cargo test": "cargo test",
        "junit": "mvn test",
    }.get(ctx.test_framework or infer_test_framework(ctx.language), "npm test")


def _get_single_test_cmd(ctx: ProjectContext) -> str:
    if ctx.test_level == "none":
        return "# No tests configured"
    return {
        "vitest": 'npx vitest run -t "test name"',
        "jest": 'npx jest -t "test name"',
        "pytest": "pytest tests/test_file.py::test_name -v",
        "go test": "go test ./path -run TestName -v",
        "cargo test": "cargo test test_name",
    }.get(
        ctx.test_framework or infer_test_framework(ctx.language),
        'npm test -- -t "test name"',
    )


def _get_style_rules(ctx: ProjectContext) -> list[str]:
    rules = {
        "typescript": [
            "- Use TypeScript strict mode",
            "- Prefer `const` over `let`, avoid `var`",
            "- Named exports over default exports",
            "- Type all function parameters and return values",
            "- Use `async/await` over raw promises",
            "- camelCase for variables/functions, PascalCase for types",
        ],
        "python": [
            "- Follow PEP 8 style guide",
            "- Use type hints for all public functions",
            "- `snake_case` for variables/functions, `PascalCase` for classes",
            "- Prefer f-strings over .format()",
            "- Use dataclasses for simple data containers",
            "- Docstrings for all public functions and classes",
        ],
        "go": [
            "- Follow `gofmt` formatting",
            "- `camelCase` for local, `PascalCase` for exported",
            "- Check errors immediately, don't defer",
            "- Use interfaces for abstraction",
            "- Package names: lowercase, single word",
        ],
        "rust": [
            "- Follow `rustfmt` and `clippy`",
            "- `snake_case` for variables/functions, `PascalCase` for types",
            "- Prefer `Result` over panics",
            "- Use `Option` instead of null checks",
            "- Document public APIs with `///` comments",
        ],
    }
    return rules.get(ctx.language, ["- Follow language idioms and community standards"])
