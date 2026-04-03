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
        created.append(_agent_code_reviewer(agents_dir, ctx))
        created.append(_agent_debugger(agents_dir, ctx))
        if ctx.project_type == "api":
            created.append(_agent_api_designer(agents_dir, ctx))
        if ctx.project_type in ("data-pipeline", "ml-model"):
            created.append(_agent_data_analyst(agents_dir, ctx))

        return created

    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate project scaffold files."""
        created = []
        created.append(_scaffold_gitignore(output_dir, ctx))
        created.append(_scaffold_claudeignore(output_dir, ctx))
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
- `feat`: New feature that adds functionality
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Formatting, missing semicolons — no logic change
- `refactor`: Code change that is neither a fix nor a feature
- `test`: Adding or correcting tests
- `chore`: Build process, dependencies, tooling
- `perf`: Performance improvement
- `ci`: CI/CD configuration changes
- `revert`: Reverts a previous commit

## Format Rules
- Subject line: max 72 characters, imperative mood ("add" not "added")
- No period at end of subject
- Scope is optional but useful: `feat(auth): add OAuth2 login`
- Breaking changes: add `!` after type: `feat!: redesign API`
- Multi-line body for complex changes: blank line after subject

## Process
1. Run `git diff --cached` to see staged changes
2. Identify the primary change type
3. Determine scope from affected files/modules
4. Write subject: `<type>(<scope>): <imperative description>`
5. Add body if the change needs explanation
6. Reference issues if applicable: `Closes #123`
7. Run `git commit -m "<message>"`

## Examples
```
feat(auth): add JWT token refresh endpoint
fix(api): handle null response from payment gateway
refactor(db): extract query builder into separate module
docs(readme): update installation steps for Windows
test(auth): add edge cases for token expiration
chore(deps): upgrade pytest to 8.0
perf(query): add index on users.email column
feat!: redesign authentication API (breaking change)
```

## Multi-commit Strategy
If diff spans multiple concerns, suggest splitting:
- `git add -p` to stage selectively
- Separate commits per logical unit
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

Review the current branch changes before submitting a PR.

## Process
1. Run `git diff main...HEAD --stat` for overview
2. Run `git diff main...HEAD` for full diff
3. Check each changed file against the checklist below
4. Report findings grouped by severity

## Review Checklist

### 🔴 Blocking (must fix before merge)
- [ ] No hardcoded secrets, API keys, or credentials
- [ ] No broken tests (`run test suite`)
- [ ] No obvious security vulnerabilities (SQL injection, XSS, path traversal)
- [ ] No `print()` / `console.log()` debug statements left in
- [ ] No `TODO: fix before merge` or `HACK:` comments

### 🟡 Important (should fix)
- [ ] New functionality has tests
- [ ] Error cases are handled (not just happy path)
- [ ] No unnecessary dependencies added
- [ ] Breaking changes are documented
- [ ] Public API changes are backward compatible or versioned

### 🟢 Nice to have (suggestions)
- [ ] Code follows existing style and patterns
- [ ] Variable/function names are descriptive
- [ ] Complex logic has comments
- [ ] README / docs updated if behavior changed

## Output Format
```
## PR Review Summary

### 🔴 Blocking Issues
- [file:line] Description → Suggested fix

### 🟡 Important
- [file:line] Description

### 🟢 Suggestions
- [file:line] Suggestion

### Verdict
[APPROVE / REQUEST_CHANGES]
Reason: ...
```

## PR Description Template
After review, generate PR description:
```
## What
[Brief description of changes]

## Why
[Context and motivation]

## How
[Implementation approach]

## Testing
[How this was tested]

## Checklist
- [ ] Tests pass
- [ ] No secrets committed
- [ ] Docs updated
```
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "pr-review"


def _skill_deploy(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "deploy"
    d.mkdir(parents=True, exist_ok=True)
    hosting = ctx.hosting or "production"
    build_cmd = _get_build_cmd(ctx)
    test_cmd = _get_test_cmd(ctx)
    (ctx.language or "").lower()

    # Hosting-specific deploy commands
    deploy_cmd_map = {
        "railway": "railway up",
        "fly.io": "fly deploy",
        "vercel": "vercel --prod",
        "netlify": "netlify deploy --prod",
        "heroku": "git push heroku main",
        "aws": "aws ecs update-service --force-new-deployment ...",
        "gcp": "gcloud run deploy ...",
        "docker": "docker build -t app . && docker push registry/app",
    }
    deploy_cmd = next(
        (v for k, v in deploy_cmd_map.items() if k.lower() in hosting.lower()),
        f"# deploy to {hosting}",
    )

    content = f"""---
name: deploy
description: Deploys the application to {hosting}. Use when deploying or when the user asks to deploy.
disable-model-invocation: true
---

# Deployment Skill — {hosting}

## ⚠️ Pre-Deployment Checklist (ALL must pass)
- [ ] `{test_cmd}` — all tests green
- [ ] `{build_cmd}` — build succeeds
- [ ] No hardcoded secrets or API keys
- [ ] Environment variables set in {hosting} dashboard
- [ ] Database migrations run (if applicable)
- [ ] Feature flags configured correctly
- [ ] Rollback plan ready

## Deploy Steps

### 1. Final verification
```bash
{test_cmd}
{build_cmd}
```

### 2. Deploy
```bash
{deploy_cmd}
```

### 3. Post-deploy verification
```bash
# Check health endpoint
curl https://your-app.com/health

# Check logs for errors
# Railway: railway logs
# Fly.io: fly logs
# Heroku: heroku logs --tail
# Vercel: vercel logs

# Smoke test critical paths
# - Homepage loads
# - Auth works
# - API responds
```

### 4. If something breaks — ROLLBACK
```bash
# Railway: railway rollback
# Fly.io: fly releases list && fly deploy --image <prev>
# Heroku: heroku rollback
# Vercel: vercel rollback
# Docker: docker service update --rollback <service>
```

## Environment Variables Required
Check `.env.example` for required vars. Verify all are set in {hosting} before deploying.

## Monitoring After Deploy
- Watch error rate for 5 minutes
- Check response times
- Verify no spike in 5xx errors
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
    content = r"""---
name: security-review
description: Reviews code for security vulnerabilities. Use when reviewing code or before merging.
---

# Security Review Skill

Perform a thorough security audit of the specified code.

## OWASP Top 10 Checklist

### A01 — Broken Access Control
- [ ] Authorization checked on every endpoint
- [ ] No direct object references without permission check
- [ ] Admin functions protected from regular users

### A02 — Cryptographic Failures
- [ ] No plaintext passwords stored
- [ ] Sensitive data encrypted at rest and in transit
- [ ] No weak algorithms (MD5, SHA1 for passwords)
- [ ] TLS enforced, no HTTP fallback

### A03 — Injection
- [ ] SQL: parameterized queries / ORM used (no f-strings in queries)
- [ ] Command injection: no `os.system(user_input)` or `exec()`
- [ ] XSS: output properly escaped in templates
- [ ] Path traversal: `../` in file paths sanitized

### A04 — Insecure Design
- [ ] Rate limiting on auth endpoints
- [ ] Brute force protection
- [ ] CSRF protection on state-changing endpoints

### A05 — Security Misconfiguration
- [ ] Debug mode disabled in production
- [ ] Error messages don't expose stack traces to users
- [ ] Default credentials changed
- [ ] Unused endpoints disabled

### A07 — Authentication Failures
- [ ] Passwords hashed with bcrypt/argon2 (not MD5/SHA1)
- [ ] Session tokens: long, random, invalidated on logout
- [ ] "Forgot password" flow doesn't leak user existence

### A09 — Logging Failures
- [ ] Security events logged (login failures, permission denials)
- [ ] No sensitive data in logs (passwords, tokens, PII)

### Secrets Scan
- [ ] No API keys in source code
- [ ] `.env` files in `.gitignore`
- [ ] No credentials in git history

## Process
1. Read all changed/specified files
2. Check each OWASP category
3. For each finding: file:line, severity (CRITICAL/HIGH/MEDIUM/LOW), description, fix
4. Run `git log --all -S "SECRET\|password\|api_key" --oneline` for history scan

## Output Format
```
## Security Review

### CRITICAL
- [file:line] SQL injection via f-string in query → Use parameterized query

### HIGH
- [file:line] Password stored as MD5 → Use bcrypt

### MEDIUM / LOW
- [file:line] Debug mode enabled → Set DEBUG=False in production

### Clean
- No secrets found in code
- Authorization checks present on all endpoints
```
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

Improve code quality while preserving behavior.

## Golden Rules
1. **Never change behavior** — if it does X, it must still do X after refactor
2. **Tests must pass** before and after every change
3. **One thing at a time** — don't mix refactoring with new features
4. **Smallest possible diff** — don't rewrite when extract suffices

## Code Smells to Target

### Complexity
- Functions > 20 lines → extract helper functions
- Nesting > 3 levels → extract or invert conditions
- `if/elif` chains > 5 branches → use dict dispatch or strategy pattern

### Duplication (DRY)
- Identical code blocks → extract shared function
- Repeated magic numbers → named constants
- Copy-paste with slight variation → parameterize

### Naming
- Single-letter variables (except loop counters) → descriptive names
- Misleading names → rename to match actual behavior
- Abbreviations → spell out unless universal (e.g., `url`, `id`)

### Structure
- God class (> 200 lines) → split responsibilities
- Long parameter lists (> 4 params) → introduce data class/dict
- Feature envy (class using another class's data too much) → move method

## Process
1. Read the target code and understand its intent
2. Run existing tests to establish baseline: `{test_cmd}`
3. Identify the most impactful smell to fix
4. Make the smallest change that improves it
5. Run tests: must still pass
6. Repeat for next smell
7. Commit with message: `refactor(<scope>): <what changed>`

## What NOT to Do
- Don't change variable names just because you prefer them
- Don't introduce abstractions "for future flexibility"
- Don't reformat code in the same commit as logic changes
- Don't refactor untested code — add tests first
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
description: Docker container best practices and Dockerfile conventions. Use when containerizing applications or reviewing Dockerfiles.
---

# Docker Conventions

## Dockerfile Checklist

### Base Image
- [ ] Use official images from Docker Hub
- [ ] Pin exact version: `FROM python:3.12-slim` not `FROM python:latest`
- [ ] Use `-slim` or `-alpine` variants to reduce image size

### Layer Optimization
- [ ] Copy dependency files FIRST, then source code (cache layers)
- [ ] Combine RUN commands with `&&` to reduce layers
- [ ] Clean package cache in same RUN command

```dockerfile
# ✅ Good — dependency layer cached separately
COPY requirements.txt .
RUN pip install -r requirements.txt && rm -rf /root/.cache/pip

COPY src/ ./src/

# ❌ Bad — cache invalidated on any source change
COPY . .
RUN pip install -r requirements.txt
```

### Security
- [ ] Never run as root: add `USER appuser`
- [ ] Create non-root user explicitly:
  ```dockerfile
  RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
  USER appuser
  ```
- [ ] No secrets in ENV or ARG (use runtime secrets)
- [ ] `.dockerignore` excludes: `.env`, `.git`, `node_modules`, `__pycache__`

### Multi-Stage Build (for compiled languages)
```dockerfile
FROM node:20 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-slim AS runtime
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
USER node
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Health Check (required for production)
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1
```

### docker-compose Best Practices
```yaml
services:
  app:
    build: .
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}  # from .env, not hardcoded
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
```

## Common Issues to Fix
- `COPY . .` before dependency install → reorder
- Running as root → add USER
- No .dockerignore → create one
- `latest` tag → pin version
- Missing health check → add HEALTHCHECK
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

Systematically identify and fix performance bottlenecks.

## Step 1: Measure First
Never optimize without data. Profile before you fix.

```bash
# Python
python -m cProfile -o profile.out your_script.py
python -m pstats profile.out

# Node.js
node --prof app.js && node --prof-process isolate-*.log

# Go
go test -cpuprofile cpu.prof -memprofile mem.prof -bench .
go tool pprof cpu.prof
```

## Step 2: Find the Hotspot
- 80% of performance issues are in 20% of the code
- Focus on the innermost loop, highest-frequency path
- Check: database queries, network calls, file I/O first

## Common Bottlenecks & Fixes

### Database (most common)
- **N+1 queries**: use eager loading / joins
- **Missing index**: check `EXPLAIN ANALYZE` output
- **Full table scan**: add index on WHERE/ORDER BY columns
- **SELECT ***: only fetch columns you need

```sql
-- Find slow queries (PostgreSQL)
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 10;
```

### Python
- **Slow loops**: use list comprehensions, numpy vectorization
- **Repeated computation**: cache with `functools.lru_cache`
- **I/O bound**: use `asyncio` or `concurrent.futures`
- **Memory**: use generators instead of lists for large datasets

### JavaScript/TypeScript
- **Re-renders**: memo/useMemo/useCallback in React
- **Bundle size**: code splitting, dynamic imports
- **DOM manipulation**: batch updates, use DocumentFragment
- **Memory leaks**: clean up event listeners and timers

### API/Network
- **No pagination**: add `limit/offset` or cursor pagination
- **No caching**: add `Cache-Control` headers, Redis cache
- **Chatty API**: batch requests, use GraphQL or compound endpoints

## Step 3: Fix & Verify
1. Make ONE change at a time
2. Benchmark before and after
3. Document what changed and the measured improvement

## Output Format
```
## Performance Analysis

### Bottleneck Found
[File:line] — Description of the issue
Estimated impact: HIGH/MEDIUM/LOW

### Root Cause
[Explain why it's slow]

### Fix Applied
[Code change + benchmark result]
Before: Xms / Y req/s
After:  Xms / Y req/s (+Z% improvement)
```
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "performance"


def _skill_debt_analyzer(skills_dir: Path) -> str:
    d = skills_dir / "debt-analyzer"
    d.mkdir(parents=True, exist_ok=True)
    content = r"""---
name: debt-analyzer
description: Analyzes code for technical debt and code smells. Use when assessing code quality or planning a refactor sprint.
---

# Technical Debt Analyzer

Audit the codebase for technical debt and produce a prioritized action plan.

## Debt Categories

### 🔴 Critical Debt (fix this sprint)
- Security vulnerabilities
- Tests with `skip` or `xfail` that hide real bugs
- Hardcoded configuration values in production code
- `# TODO: fix before release` comments

### 🟡 High Debt (schedule soon)
- Functions > 50 lines
- Files > 300 lines
- Cyclomatic complexity > 10 (count `if`/`for`/`while`/`try` branches)
- Copy-pasted code blocks (> 10 lines identical)
- Missing tests on critical paths
- Outdated dependencies with known issues

### 🟢 Low Debt (track & address gradually)
- Poor naming
- Missing docstrings on public functions
- Inconsistent code style
- Overly deep nesting (> 4 levels)
- Magic numbers without named constants

## Analysis Process
1. **Grep for known debt markers**:
   ```bash
   grep -rn "TODO\|FIXME\|HACK\|XXX\|NOSONAR" src/
   grep -rn "# type: ignore" src/
   grep -rn "pylint: disable\|noqa" src/
   ```

2. **Find long functions** (Python):
   ```bash
   python3 -c "
   import ast, sys
   from pathlib import Path
   for f in Path('src').rglob('*.py'):
       tree = ast.parse(f.read_text())
       for node in ast.walk(tree):
           if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
               lines = node.end_lineno - node.lineno
               if lines > 30:
                   print(f'{f}:{node.lineno} {node.name}() = {lines} lines')
   "
   ```

3. **Check test coverage**:
   ```bash
   pytest --cov=src --cov-report=term-missing
   ```

4. **Check outdated deps**:
   ```bash
   pip list --outdated   # Python
   npm outdated          # Node
   ```

## Output Format
```
## Technical Debt Report

### Summary
- Critical issues: X
- High priority: Y
- Low priority: Z
- Estimated cleanup effort: N days

### 🔴 Critical
| File | Issue | Effort |
|------|-------|--------|
| src/auth.py:45 | Hardcoded JWT secret | 30min |

### 🟡 High Priority
| File | Issue | Effort |
|------|-------|--------|
| src/api/users.py | 150-line function | 2h |

### Recommended Sprint Plan
1. [Quick wins < 1h]
2. [Medium tasks 1-4h]
3. [Large refactors > 4h — schedule separately]
```
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
# block_destructive.sh — Blocks dangerous commands before execution
# Triggered by Claude Code PreToolUse hook on Bash tool

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null || \
          echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\\(.*\\)"/\\1/')

# Destructive filesystem operations
DESTRUCTIVE_PATTERNS=(
    "rm -rf"
    "rm -r /"
    "rm -fr"
    "sudo rm"
    "find . -delete"
    "find / -delete"
)

# Dangerous git operations
GIT_PATTERNS=(
    "git push --force"
    "git push -f"
    "git push origin main --force"
    "git push origin master --force"
)

# Dangerous database operations
DB_PATTERNS=(
    "DROP TABLE"
    "DROP DATABASE"
    "DROP SCHEMA"
    "DELETE FROM"
    "TRUNCATE TABLE"
    "TRUNCATE "
)

# Dangerous system operations
SYSTEM_PATTERNS=(
    "mkfs"
    "dd if="
    ":(){ :|:& };:"
    "curl.*|.*sh"
    "curl.*|.*bash"
    "wget.*|.*sh"
    "wget.*|.*bash"
    "chmod -R 777 /"
    "chmod 777 /"
)

check_patterns() {
    local cmd="$1"
    shift
    local patterns=("$@")
    for pattern in "${patterns[@]}"; do
        if echo "$cmd" | grep -qi "$pattern"; then
            echo "BLOCKED: Destructive command detected: '$pattern'" >&2
            echo "Command was: $cmd" >&2
            echo "If you intended this, run the command manually." >&2
            exit 2
        fi
    done
}

check_patterns "$COMMAND" "${DESTRUCTIVE_PATTERNS[@]}"
check_patterns "$COMMAND" "${GIT_PATTERNS[@]}"
check_patterns "$COMMAND" "${DB_PATTERNS[@]}"
check_patterns "$COMMAND" "${SYSTEM_PATTERNS[@]}"

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

# Real-world secret patterns used by major providers
PATTERNS=(
    # OpenAI
    "sk-[a-zA-Z0-9]{20,}"
    # Anthropic
    "sk-ant-[a-zA-Z0-9]"
    # AWS
    "AKIA[0-9A-Z]{16}"
    "aws_access_key_id"
    "aws_secret_access_key"
    # GitHub
    "ghp_[a-zA-Z0-9]{36}"
    "github_pat_[a-zA-Z0-9]"
    "gho_[a-zA-Z0-9]{36}"
    # Google
    "AIza[0-9A-Za-z_-]{35}"
    "ya29\.[0-9A-Za-z_-]"
    # Stripe
    "sk_live_[a-zA-Z0-9]{24}"
    "pk_live_[a-zA-Z0-9]{24}"
    # Twilio
    "SK[a-f0-9]{32}"
    "AC[a-f0-9]{32}"
    # Generic patterns
    "BEGIN.*PRIVATE KEY"
    "BEGIN RSA PRIVATE KEY"
    "BEGIN EC PRIVATE KEY"
    # Hardcoded assignment patterns
    "api_key[[:space:]]*=[[:space:]]*['\"][a-zA-Z0-9_-]{16,}"
    "secret[[:space:]]*=[[:space:]]*['\"][a-zA-Z0-9_-]{16,}"
    "password[[:space:]]*=[[:space:]]*['\"][^'\"]{8,}"
    "token[[:space:]]*=[[:space:]]*['\"][a-zA-Z0-9_-]{16,}"
)

BLOCKED=0
for pattern in "${PATTERNS[@]}"; do
    if grep -qE "$pattern" "$FILE" 2>/dev/null; then
        echo "SECRET DETECTED in $FILE — pattern: $pattern" >&2
        echo "Remove or move to .env before committing." >&2
        BLOCKED=1
    fi
done

# Block commit if secret found
[ "$BLOCKED" -eq 1 ] && exit 2

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


def _agent_code_reviewer(agents_dir: Path, ctx: ProjectContext) -> str:
    content = f"""---
name: code-reviewer
description: Reviews code changes for quality, maintainability, and best practices
tools: Read, Grep, Glob, Bash
---

You are a senior software engineer doing a thorough code review.

## Review Checklist
- **Correctness**: Does the code do what it's supposed to?
- **Readability**: Is the code easy to understand?
- **Maintainability**: Will this be easy to modify later?
- **Performance**: Any obvious performance issues?
- **Error handling**: Are edge cases handled?
- **Tests**: Are there adequate tests?
- **Documentation**: Are complex parts documented?

## Language: {ctx.language}
## Framework: {ctx.framework or "None"}

## Process
1. Read the changed files
2. Understand the intent
3. Check each item on the checklist
4. Provide line-specific feedback with concrete suggestions
5. Rate each issue: [BLOCKING] [SUGGESTION] [NITPICK]

## Output Format
```
## Code Review Summary

### Blocking Issues
- [file:line] Issue description → Suggested fix

### Suggestions
- [file:line] Suggestion → Why it matters

### Nitpicks
- [file:line] Minor style/naming issue

### Overall Assessment
[APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION]
```
"""
    p = agents_dir / "code-reviewer.md"
    p.write_text(content, encoding="utf-8")
    return "code-reviewer"


def _agent_debugger(agents_dir: Path, ctx: ProjectContext) -> str:
    content = f"""---
name: debugger
description: Diagnoses and fixes bugs systematically using root cause analysis
tools: Read, Grep, Glob, Bash, Write
---

You are an expert debugger. Find the root cause and fix bugs systematically.

## Language: {ctx.language}
## Test Command: {ctx.test_framework or "pytest" if ctx.language == "python" else "npm test"}

## Debugging Process
1. **Reproduce** — Understand the exact failure condition
2. **Isolate** — Narrow down which component is failing
3. **Hypothesize** — Form a theory about the root cause
4. **Verify** — Test the hypothesis
5. **Fix** — Apply the minimal fix
6. **Validate** — Run tests to confirm the fix

## Rules
- Never fix symptoms, fix root causes
- Minimal diffs only — don't refactor while fixing
- Run tests after every change
- Document what you found and why the fix works

## Output Format
```
## Bug Report

### Root Cause
[Explain exactly what was wrong and why]

### Fix Applied
[Describe the change made]

### Verification
[Test output showing the fix works]
```
"""
    p = agents_dir / "debugger.md"
    p.write_text(content, encoding="utf-8")
    return "debugger"


def _agent_api_designer(agents_dir: Path, ctx: ProjectContext) -> str:
    content = f"""---
name: api-designer
description: Designs RESTful API endpoints following best practices
tools: Read, Grep, Glob, Write
---

You are a senior API architect. Design clean, consistent REST APIs.

## Framework: {ctx.framework or "None"}
## Project: {ctx.project_name or "Project"}

## API Design Principles
- **REST conventions**: GET (read), POST (create), PUT (replace), PATCH (update), DELETE
- **Consistent naming**: plural nouns for collections (`/users`, `/orders`)
- **Versioning**: always version your API (`/v1/users`)
- **Error responses**: consistent shape `{{"error": "...", "message": "...", "code": "..."}}`
- **HTTP status codes**: use them correctly (200/201/400/401/403/404/422/500)

## Process
1. Understand the resource being modeled
2. Define the collection and item endpoints
3. Specify request/response schemas
4. Document error cases
5. Note authentication requirements

## Output Format
```
## API Design: [Resource Name]

### Endpoints
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET    | /v1/resource | List all | Yes |

### Request Schema
[JSON schema]

### Response Schema
[JSON schema]

### Error Cases
[List of error responses]
```
"""
    p = agents_dir / "api-designer.md"
    p.write_text(content, encoding="utf-8")
    return "api-designer"


def _agent_data_analyst(agents_dir: Path, ctx: ProjectContext) -> str:
    content = f"""---
name: data-analyst
description: Analyzes data pipelines, schemas, and data quality issues
tools: Read, Grep, Glob, Bash, Write
---

You are a senior data engineer. Analyze data pipelines and schemas.

## Project Type: {ctx.project_type}
## Language: {ctx.language}

## Analysis Areas
- **Data quality**: nulls, duplicates, outliers, schema violations
- **Pipeline performance**: bottlenecks, chunking, memory usage
- **Schema design**: normalization, indexing, relationships
- **Idempotency**: can the pipeline run twice safely?
- **Error handling**: what happens when upstream data is malformed?

## SQLite Best Practices
```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=OFF;
PRAGMA cache_size=-64000;  -- 64MB cache
PRAGMA temp_store=MEMORY;
```

## Process
1. Read the pipeline/schema files
2. Identify the data flow
3. Check for quality issues
4. Suggest optimizations
5. Verify idempotency

## Output Format
```
## Data Analysis Report

### Data Flow
[Describe the pipeline steps]

### Issues Found
- [CRITICAL/WARNING/INFO] Description

### Recommendations
[Concrete improvements with code examples]
```
"""
    p = agents_dir / "data-analyst.md"
    p.write_text(content, encoding="utf-8")
    return "data-analyst"


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


def _scaffold_claudeignore(output_dir: str, ctx: ProjectContext) -> str:
    """Generate .claudeignore — keeps Claude Code's context window clean.

    Same format as .gitignore. Prevents build artifacts, dependencies,
    and generated files from polluting the LLM context.
    Best practice: keep context token-efficient.
    """
    base = [
        "# .claudeignore — Keeps Claude Code context clean",
        "# Same format as .gitignore",
        "# Reference: https://code.claude.com/docs/en/best-practices",
        "",
        "# Dependencies",
        "node_modules/",
        ".venv/",
        "venv/",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "",
        "# Build output",
        "dist/",
        "build/",
        "out/",
        ".next/",
        ".nuxt/",
        "target/",
        "",
        "# Test & coverage",
        "coverage/",
        ".pytest_cache/",
        ".nyc_output/",
        "htmlcov/",
        "",
        "# Logs & temp",
        "*.log",
        "logs/",
        "tmp/",
        ".tmp/",
        "",
        "# Secrets & env",
        ".env",
        ".env.local",
        ".env.*.local",
        "",
        "# OS & editor",
        ".DS_Store",
        "Thumbs.db",
        ".idea/",
        ".vscode/",
        "",
        "# Lock files (rarely useful for context)",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "Pipfile.lock",
        "",
        "# Generated / compiled",
        "*.d.ts",
        "*.js.map",
        "*.tsbuildinfo",
        "*.egg-info/",
        "*.egg",
        "",
        "# Data & large files",
        "*.csv",
        "*.parquet",
        "*.xlsx",
        "*.sqlite",
        "*.db",
        "",
    ]

    # Language-specific extras
    lang = (ctx.language or "").lower()
    if lang == "python":
        base += [
            "# Python specific",
            "*.so",
            "*.pyd",
            "site-packages/",
            "",
        ]
    elif lang in ("typescript", "javascript"):
        base += [
            "# JS/TS specific",
            ".cache/",
            "storybook-static/",
            "",
        ]
    elif lang == "java":
        base += [
            "# Java specific",
            "*.class",
            "*.jar",
            "*.war",
            "",
        ]
    elif lang == "rust":
        base += [
            "# Rust specific",
            "Cargo.lock",
            "",
        ]

    # Project type extras
    if ctx.project_type == "data-pipeline":
        base += [
            "# Data pipeline",
            "data/raw/",
            "data/processed/",
            "reports/",
            "*.json.gz",
            "",
        ]

    p = Path(output_dir) / ".claudeignore"
    p.write_text("\n".join(base) + "\n", encoding="utf-8")
    return ".claudeignore"


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
