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
        created.append(_agent_dependency_auditor(agents_dir, ctx))
        created.append(_agent_performance_profiler(agents_dir, ctx))
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
        created.append(_scaffold_precommit_config(output_dir, ctx))
        created.append(_scaffold_contributing(output_dir, ctx))
        created.append(_scaffold_changelog(output_dir, ctx))

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
description: Generates conventional commit messages from git diff and changelogs. Use when committing changes, creating a release, or when asked to write a commit message or changelog.
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
1. Run `git diff --cached` to see staged changes (or `git diff HEAD` for uncommitted)
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

## Changelog Generation

When asked to generate a changelog or prepare a release:

1. Determine version range:
   ```bash
   git log <prev-tag>..HEAD --oneline --no-merges
   # or: git log --since="2 weeks ago" --oneline
   ```

2. Group commits by type:
   - **🚀 Features** — all `feat:` commits
   - **🐛 Bug Fixes** — all `fix:` commits
   - **⚡ Performance** — all `perf:` commits
   - **💥 Breaking Changes** — commits with `!` or `BREAKING CHANGE:` footer
   - **🔧 Chores & Internal** — `chore:`, `refactor:`, `ci:`, `style:`
   - **📖 Documentation** — `docs:` commits

3. Output CHANGELOG.md entry:
   ```markdown
   ## [v1.2.0] — YYYY-MM-DD

   ### 🚀 Features
   - Add JWT token refresh endpoint (#42)
   - Support multi-tenant auth flows

   ### 🐛 Bug Fixes
   - Handle null response from payment gateway
   - Fix race condition in session cleanup

   ### 💥 Breaking Changes
   - `POST /auth/login` now returns `access_token` instead of `token`
   ```

4. Suggest semantic version bump:
   - `BREAKING CHANGE` → major bump (1.x.x → 2.0.0)
   - `feat:` → minor bump (1.2.x → 1.3.0)
   - `fix:`/`perf:` only → patch bump (1.2.3 → 1.2.4)
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
    auth_method = ctx.auth_method or "JWT"

    jwt_section = (
        """
## JWT Implementation
```python
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.environ["JWT_SECRET"]  # Never hardcode!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)

def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + ACCESS_TOKEN_EXPIRE,
        "iat": datetime.utcnow(),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload["type"] != "access":
            raise ValueError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.JWTError:
        raise AuthError("Invalid token")
```

## Token Storage
- **Web apps**: httpOnly cookies (not localStorage — XSS vulnerable)
- **Mobile apps**: secure storage (Keychain/Keystore)
- **APIs**: Authorization header: `Bearer <token>`

## Refresh Token Rotation
```python
def refresh_tokens(refresh_token: str) -> tuple[str, str]:
    # Verify refresh token
    payload = verify_refresh_token(refresh_token)
    user_id = payload["sub"]

    # Rotate: invalidate old, issue new
    invalidate_refresh_token(refresh_token)  # Add to blocklist
    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)
    return new_access, new_refresh
```
"""
        if "jwt" in auth_method.lower()
        else ""
    )

    oauth_section = (
        """
## OAuth2 / OIDC Flow
1. Redirect user to provider authorization URL
2. User grants permission
3. Provider redirects back with `code`
4. Exchange `code` for access + refresh tokens
5. Store tokens securely, never expose to client JS

## State Parameter (CSRF protection)
```python
import secrets
state = secrets.token_urlsafe(32)
session["oauth_state"] = state
# Verify state matches on callback
```
"""
        if "oauth" in auth_method.lower()
        else ""
    )

    content = f"""---
name: auth-conventions
description: Authentication patterns and security rules for {auth_method}. Use when working with auth, login, or protected routes.
---

# Auth Conventions — {auth_method}

## Non-Negotiable Security Rules
- [ ] Never log tokens, passwords, or session IDs
- [ ] Never store passwords in plaintext — use bcrypt/argon2
- [ ] Never expose whether an email exists on login failure
- [ ] Rate limit auth endpoints (login: 5/min, password reset: 3/hour)
- [ ] All protected routes verify auth on every request
- [ ] HTTPS only — never allow HTTP for auth endpoints

## Password Hashing
```python
# ✅ bcrypt (recommended)
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
bcrypt.checkpw(password.encode(), hashed)

# ✅ argon2 (more modern)
from argon2 import PasswordHasher
ph = PasswordHasher()
hash = ph.hash(password)
ph.verify(hash, password)

# ❌ NEVER
hashlib.md5(password).hexdigest()  # broken
hashlib.sha256(password).hexdigest()  # broken (no salt)
```

## Login Response
```python
# ✅ Same error for wrong email AND wrong password
raise AuthError("Invalid credentials")  # Don't leak user existence

# ❌ Leaks user existence
if user is None:
    raise AuthError("User not found")
if not verify_password(password, user.hashed_password):
    raise AuthError("Wrong password")
```

{jwt_section}{oauth_section}

## Session Security (web)
```python
SESSION_COOKIE_SECURE = True      # HTTPS only
SESSION_COOKIE_HTTPONLY = True    # No JS access
SESSION_COOKIE_SAMESITE = "Lax"  # CSRF protection
SESSION_COOKIE_MAX_AGE = 3600    # 1 hour
```

## Auth Middleware Pattern
```python
async def require_auth(request):
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(401, "Authentication required")
    try:
        payload = verify_token(token)
        request.user_id = payload["sub"]
    except AuthError as e:
        raise HTTPException(401, str(e))
```

## Security Checklist
- [ ] Passwords hashed with bcrypt/argon2
- [ ] Login doesn't reveal user existence
- [ ] Tokens expire (access: 15min, refresh: 7days)
- [ ] Refresh tokens rotate on use
- [ ] Rate limiting on /login, /register, /reset-password
- [ ] CSRF protection for cookie-based auth
- [ ] Audit log for login attempts
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
| Rule | ✅ Good | ❌ Bad |
|------|---------|--------|
| Plural nouns | `/v1/users` | `/v1/user` |
| kebab-case | `/v1/user-profiles` | `/v1/userProfiles` |
| Nouns not verbs | `/v1/orders` | `/v1/getOrders` |
| Versioned | `/v1/users` | `/users` |
| Nested for relations | `/v1/users/{id}/orders` | `/v1/user-orders?userId=1` |

## HTTP Methods & Status Codes
| Method | Use Case | Success | Error |
|--------|----------|---------|-------|
| GET | Retrieve | 200 | 404 |
| POST | Create | 201 | 400/422 |
| PUT | Replace | 200 | 404/400 |
| PATCH | Update | 200 | 404/400 |
| DELETE | Remove | 204 | 404 |

## Standard Response Envelope
```json
{
  "data": { "id": "123", "name": "Alice" },
  "meta": {
    "page": 1,
    "perPage": 20,
    "total": 150,
    "requestId": "req_abc123"
  }
}
```

## Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is invalid",
    "details": [
      { "field": "email", "message": "Must be a valid email address" }
    ],
    "requestId": "req_abc123"
  }
}
```

## Pagination
Always paginate list endpoints. Use cursor-based for large datasets:
```
GET /v1/users?limit=20&cursor=eyJpZCI6MTIzfQ==
Response: { "data": [...], "nextCursor": "eyJpZCI6MTQzfQ==" }
```

## Filtering & Sorting
```
GET /v1/users?status=active&role=admin
GET /v1/orders?sort=-createdAt,+total   # - = desc, + = asc
GET /v1/products?fields=id,name,price   # sparse fieldsets
```

## Authentication Headers
```
Authorization: Bearer <token>
X-API-Key: <key>
```

## Idempotency
For POST/PATCH, support idempotency keys:
```
Idempotency-Key: a6c2a234-a0c7-4b62-9f4c-14b6b5a31d0b
```

## Common Mistakes to Avoid
- ❌ Returning 200 for errors
- ❌ Different field names in request vs response (`userId` vs `user_id`)
- ❌ No pagination on list endpoints
- ❌ Exposing internal IDs (use UUIDs or encoded IDs)
- ❌ Inconsistent naming across endpoints
- ❌ No request/response documentation
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "api-conventions"


def _skill_test_patterns(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "test-patterns"
    d.mkdir(parents=True, exist_ok=True)
    fw = ctx.test_framework or infer_test_framework(ctx.language)
    lang = (ctx.language or "").lower()

    python_examples = (
        """
## Python / pytest Examples

### Basic test structure
```python
def test_create_user_returns_id():
    # Arrange
    db = FakeDatabase()
    service = UserService(db)

    # Act
    user_id = service.create_user(name="Alice", email="alice@example.com")

    # Assert
    assert user_id is not None
    assert db.find_user(user_id).email == "alice@example.com"
```

### Parametrized tests
```python
@pytest.mark.parametrize("email,expected", [
    ("valid@example.com", True),
    ("invalid-email", False),
    ("", False),
    (None, False),
])
def test_validate_email(email, expected):
    assert validate_email(email) == expected
```

### Fixtures
```python
@pytest.fixture
def user():
    return User(id=1, name="Alice", email="alice@example.com")

@pytest.fixture
def mock_db(mocker):
    db = mocker.Mock()
    db.find_user.return_value = None
    return db

def test_user_not_found_raises(mock_db):
    service = UserService(mock_db)
    with pytest.raises(UserNotFoundError):
        service.get_user(99)
```

### Testing exceptions
```python
def test_invalid_input_raises_value_error():
    with pytest.raises(ValueError, match="Email cannot be empty"):
        create_user(name="Bob", email="")
```
"""
        if lang == "python"
        else ""
    )

    ts_examples = (
        """
## TypeScript / Vitest Examples

### Basic test
```typescript
import { describe, it, expect, vi } from 'vitest'
import { createUser } from './user-service'

describe('createUser', () => {
  it('returns user id on success', async () => {
    const db = { insert: vi.fn().mockResolvedValue({ id: '123' }) }
    const result = await createUser(db, { name: 'Alice' })
    expect(result.id).toBe('123')
  })

  it('throws on missing name', async () => {
    await expect(createUser(db, {})).rejects.toThrow('Name is required')
  })
})
```

### Mocking
```typescript
vi.mock('./email-service', () => ({
  sendEmail: vi.fn().mockResolvedValue(true),
}))
```
"""
        if lang in ("typescript", "javascript")
        else ""
    )

    content = f"""---
name: test-patterns
description: Test writing patterns using {fw}. Use when writing tests or asked to add test coverage.
---

# Test Patterns — {fw}

## AAA Structure (non-negotiable)
Every test follows Arrange → Act → Assert:
1. **Arrange**: set up test data and dependencies
2. **Act**: execute the code under test (usually one line)
3. **Assert**: verify the outcome

## Naming Convention
`test_<function>_<scenario>_<expected_outcome>`

Examples:
- `test_create_user_valid_input_returns_id`
- `test_create_user_empty_email_raises_value_error`
- `test_login_wrong_password_returns_401`

## What to Test
- ✅ Happy path (valid input → expected output)
- ✅ Edge cases (empty, null, zero, max values)
- ✅ Error cases (invalid input → exception/error response)
- ✅ Boundary conditions (off-by-one, limits)
- ❌ Implementation details (internal variable names)
- ❌ Third-party library behavior

## Test Isolation Rules
- Tests must be **independent** — no shared mutable state
- Tests must be **deterministic** — same result every run
- **Mock external dependencies**: database, HTTP, file system, time
- Use **factories/fixtures** for test data, not hardcoded values

## Coverage Targets
- Critical business logic: 100%
- API endpoints: 100% (happy + error paths)
- Utilities: 80%+
- UI components: key interactions

{python_examples}{ts_examples}

## Running Tests
```bash
# Run all tests
{fw}

# Run specific file
{"pytest tests/test_users.py -v" if lang == "python" else "npx vitest run src/users.test.ts"}

# With coverage
{"pytest --cov=src --cov-report=term-missing" if lang == "python" else "npx vitest run --coverage"}

# Watch mode (development)
{"pytest-watch" if lang == "python" else "npx vitest"}
```
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
description: Squashes multiple commits into one clean commit before merging. Use when cleaning up commit history.
---

# Squash Skill

## When to Squash
✅ Before merging a feature branch (cleanup "wip", "fix typo" commits)
✅ After code review feedback cycles
✅ When you have > 3 commits for one logical change
❌ Don't squash: shared commits others have branched from
❌ Don't squash: commits that are genuinely separate changes

## Process

### Option 1: Interactive Rebase (most control)
```bash
# Squash last N commits
git log --oneline -10  # count how many to squash
git rebase -i HEAD~4   # to squash last 4

# In editor: change 'pick' → 'squash' (or 's') for commits to fold in
# Keep 'pick' on the FIRST commit
# pick abc1234 feat: add user model
# squash def5678 wip: auth logic
# squash ghi9012 fix: typo
# squash jkl3456 review: apply feedback
```

### Option 2: Soft reset (simpler)
```bash
# Reset to point before your commits, keep changes staged
git reset --soft origin/main

# Now all changes are staged — make one clean commit
git commit -m "feat(auth): add user authentication"
```

### Option 3: Merge with squash (no rebase)
```bash
# From main branch
git merge --squash feature/my-branch
git commit -m "feat: add my feature"
```

## After Squash
```bash
# Force push (only OK on your own feature branch!)
git push --force-with-lease origin feature/my-branch
# --force-with-lease is safer than --force (fails if remote changed)
```

## Writing the Squash Commit Message
Use conventional commit format for the final message:
```
feat(scope): brief description

- Bullet summary of what changed
- Why it was needed
- Any breaking changes

Closes #123
```
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "squash"


def _skill_revert(skills_dir: Path) -> str:
    d = skills_dir / "revert"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: revert
description: Safely reverts specific commits or changes using git revert. Use when undoing changes that are already in main/shared branches.
---

# Revert Skill

## Revert vs Reset: Choose Correctly
| | `git revert` | `git reset` |
|---|---|---|
| Creates new commit | ✅ Yes | ❌ No |
| Safe for shared branches | ✅ Yes | ❌ No (rewrites history) |
| Preserves history | ✅ Yes | ❌ No |
| Use when | commit is in main/shared | commit is only in your branch |

**Rule: On `main` or shared branches, ALWAYS use `git revert`.**

## Process

### Revert a single commit
```bash
# Find the commit to revert
git log --oneline -20

# Revert it (creates a new "revert" commit)
git revert abc1234

# Or revert without immediately committing (to edit message)
git revert --no-commit abc1234
git commit -m "revert: undo broken feature X (fixes #456)"
```

### Revert a merge commit
```bash
# Merge commits need -m to specify which parent to revert to
git revert -m 1 abc1234  # -m 1 = revert to first parent (main)
```

### Revert a range of commits
```bash
# Revert commits from abc1234 to def5678 (exclusive..inclusive)
git revert abc1234..def5678
```

### Revert a file to previous state (without new commit)
```bash
# Get file content from specific commit
git checkout abc1234 -- src/broken-file.py
git commit -m "fix: restore broken-file.py from before abc1234"
```

## Revert Commit Message Template
```
revert: <original commit message>

This reverts commit <hash>.

Reason: <why it's being reverted>
Impact: <what this fixes>
```
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "revert"


def _skill_rollback(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "rollback"
    d.mkdir(parents=True, exist_ok=True)
    hosting = ctx.hosting or "your hosting platform"

    rollback_cmds = {
        "railway": "railway rollback",
        "fly.io": "fly releases list\nfly deploy --image <prev-image>",
        "vercel": "vercel rollback",
        "heroku": "heroku releases\nheroku rollback v<N>",
        "netlify": "netlify deploy --prod --dir=<prev-build>",
        "aws": "aws ecs update-service --task-definition <prev-arn> ...",
        "kubernetes": "kubectl rollout undo deployment/<name>\nkubectl rollout status deployment/<name>",
    }

    rollback_cmd = next(
        (v for k, v in rollback_cmds.items() if k.lower() in hosting.lower()),
        f"# Check {hosting} docs for rollback command",
    )

    content = f"""---
name: rollback
description: Emergency rollback procedure for {hosting}. Use when deployment causes critical issues.
---

# Rollback Skill — {hosting}

## ⚠️ When to Roll Back
- Error rate spiked after deploy
- Critical feature is broken
- Performance severely degraded
- Security vulnerability deployed

## Pre-Rollback Checklist
- [ ] Confirm the issue is deployment-related (not data/external)
- [ ] Check error logs to confirm timing matches deploy
- [ ] Notify team before rolling back
- [ ] Check if a database migration was applied (see below)

## Rollback Command
```bash
{rollback_cmd}
```

## Post-Rollback
```bash
# 1. Verify the rollback worked
curl https://your-app.com/health

# 2. Check error rate dropped
# (check your monitoring dashboard)

# 3. Confirm the bad version is no longer running
```

## Database Migration Warning ⚠️
If the deploy included database migrations:
- Rolling back the code WITHOUT rolling back the migration will likely break things
- Options:
  1. Write a DOWN migration and apply it first
  2. Deploy a hotfix instead of rolling back
  3. Accept the migration and fix the code instead

## Incident Template
After rollback, document:
```
## Incident Report

**Date:** <date>
**Duration:** <how long the issue lasted>
**Impact:** <users affected, features broken>

**Root Cause:**
<what caused the deployment issue>

**Timeline:**
- HH:MM — Deploy started
- HH:MM — Issue detected
- HH:MM — Rollback initiated
- HH:MM — Service restored

**Prevention:**
<what will prevent this next time>
```
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "rollback"


def _skill_migration(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "migration"
    d.mkdir(parents=True, exist_ok=True)
    lang = (ctx.language or "").lower()
    framework = (ctx.framework or "").lower()

    if lang == "python" and "django" in framework:
        migration_cmds = "python manage.py makemigrations\npython manage.py migrate"
        rollback_cmd = "python manage.py migrate <app> <prev_migration>"
        show_cmd = "python manage.py showmigrations"
    else:
        migration_cmds = "alembic revision --autogenerate -m 'description'\nalembic upgrade head"
        rollback_cmd = "alembic downgrade -1"
        show_cmd = "alembic history --verbose"

    content = f"""---
name: migration
description: Creates and applies database migrations safely. Use when changing database schema.
---

# Database Migration Skill

## ⚠️ Golden Rules
1. **Never modify already-applied migrations** — create a new one instead
2. **Always include a down migration** (rollback)
3. **Test rollback BEFORE merging** — verify it actually works
4. **One concern per migration** — don't combine unrelated schema changes
5. **Coordinate with team** — migrations in main branch require communication

## Create Migration
```bash
{migration_cmds}
```

## Review Before Applying
Check the generated migration for:
- [ ] Correct table/column names
- [ ] No accidental DROP TABLE or DROP COLUMN
- [ ] Data migrations included if needed (backfill)
- [ ] Indexes added for new foreign keys
- [ ] Nullable vs NOT NULL is intentional

## Apply & Verify
```bash
# Check pending migrations
{show_cmd}

# Apply
{"python manage.py migrate" if "django" in framework else "alembic upgrade head"}

# Verify
{"python manage.py showmigrations" if "django" in framework else "alembic current"}
```

## Rollback (if something goes wrong)
```bash
{rollback_cmd}
```

## Dangerous Operations (handle with care)
- **DROP COLUMN**: data is lost forever — backup first
- **NOT NULL without default**: will fail if existing rows don't have data
- **Rename column**: breaks all code using old name — do it in 3 migrations:
  1. Add new column
  2. Backfill data, update code
  3. Drop old column (separate PR)

## Data Migrations
When migrating data (not just schema):
```python
# Do in batches to avoid locking
BATCH_SIZE = 1000
offset = 0
while True:
    rows = db.query(f"SELECT id FROM users LIMIT {{BATCH_SIZE}} OFFSET {{offset}}")
    if not rows:
        break
    # process rows...
    offset += BATCH_SIZE
```

## Pre-Production Checklist
- [ ] Migration runs in < 5 minutes on production data size
- [ ] Rollback tested on local copy of production data
- [ ] No table locks during peak hours (use `LOCK TIMEOUT`)
- [ ] Communicated to team before running
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "migration"


def _skill_orm_conventions(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "orm-conventions"
    d.mkdir(parents=True, exist_ok=True)
    lang = (ctx.language or "").lower()
    (ctx.framework or "").lower()

    python_orm = (
        """
## SQLAlchemy Patterns
```python
# Model definition
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

# Efficient querying — avoid N+1
users = session.scalars(
    select(User).options(selectinload(User.orders))
).all()

# Bulk operations
session.execute(insert(User), [{"email": e} for e in emails])
```

## Django ORM Patterns
```python
# Good: select_related for ForeignKey
orders = Order.objects.select_related("user").filter(status="pending")

# Good: prefetch_related for ManyToMany
users = User.objects.prefetch_related("groups").all()

# Good: only() to limit fields
users = User.objects.only("id", "email").filter(active=True)

# Avoid: evaluating querysets in loops
# ❌ for user in User.objects.all(): order = user.orders.first()
# ✅ Use select_related or prefetch_related
```
"""
        if lang == "python"
        else ""
    )

    content = f"""---
name: orm-conventions
description: Database ORM patterns and conventions for {ctx.language}. Use when defining models or querying data.
---

# ORM Conventions — {ctx.language}

## Model Design Rules
- **Index foreign keys** — always add index on FK columns
- **Index query columns** — add index on columns used in WHERE/ORDER BY
- **Explicit relationships** — define all relations explicitly, don't rely on implicit
- **Soft deletes** — use `deleted_at` timestamp instead of hard delete where audit matters
- **Timestamps** — always include `created_at` and `updated_at`
- **UUID or ULID** — prefer over sequential integer IDs for public-facing endpoints

## N+1 Query Problem (most common ORM mistake)
```
# Problem: 1 query for users + N queries for each user's orders
users = User.query.all()
for user in users:
    print(user.orders)  # N+1 queries!

# Solution: eager loading — 2 queries total
users = User.query.options(joinedload(User.orders)).all()
```

## Connection Pooling
- Development: pool_size=5
- Production: pool_size=20, max_overflow=10, pool_timeout=30
- Always use `pool_pre_ping=True` to detect stale connections

## Query Optimization Checklist
- [ ] No `SELECT *` — only fetch needed columns
- [ ] Eager loading for relations accessed in loops
- [ ] Pagination on all list queries
- [ ] Indexes on frequently filtered columns
- [ ] Bulk insert instead of row-by-row for large datasets
- [ ] Count queries use `COUNT(*)` not `len(list_all())`

{python_orm}

## Transactions
```python
# Always use context managers for transactions
with session.begin():
    user = User(email="alice@example.com")
    session.add(user)
    # auto-commit on exit, auto-rollback on exception
```

## What NOT to Do
- ❌ Raw SQL with f-strings (SQL injection risk)
- ❌ Queries inside template rendering
- ❌ Loading entire table to filter in Python
- ❌ Ignoring transaction boundaries
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
description: Kubernetes deployment conventions and YAML patterns. Use when deploying to or reviewing Kubernetes configs.
---

# Kubernetes Conventions

## Deployment Template (production-ready)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    app: my-app
    version: "1.0.0"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: registry/my-app:1.0.0  # NEVER use :latest
        ports:
        - containerPort: 8080
        # Resource limits REQUIRED
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        # Probes REQUIRED
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        # Environment from ConfigMap/Secret, not hardcoded
        envFrom:
        - configMapRef:
            name: my-app-config
        - secretRef:
            name: my-app-secrets
        # Security context
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
```

## Checklist Before Deploying to K8s
- [ ] Image tag is specific version, not `latest`
- [ ] Resource requests AND limits set
- [ ] Liveness + readiness probes configured
- [ ] Secrets in `Secret` object, not `ConfigMap` or env vars
- [ ] `runAsNonRoot: true` in securityContext
- [ ] Horizontal Pod Autoscaler (HPA) for production
- [ ] PodDisruptionBudget for high-availability

## Common Mistakes
| ❌ Mistake | ✅ Fix |
|-----------|--------|
| `image: myapp:latest` | `image: myapp:1.2.3` |
| No resource limits | Always set requests+limits |
| No health checks | Add liveness + readiness probes |
| Secrets in ConfigMap | Use `kind: Secret` |
| Running as root | `runAsNonRoot: true` |
| Single replica | `replicas: 3` minimum in prod |

## Useful Commands
```bash
# Apply changes
kubectl apply -f k8s/

# Check rollout status
kubectl rollout status deployment/my-app

# Rollback
kubectl rollout undo deployment/my-app

# Check logs
kubectl logs -l app=my-app --tail=100 -f

# Debug a pod
kubectl exec -it <pod-name> -- /bin/sh

# Check events (for debugging)
kubectl get events --sort-by='.lastTimestamp'
```
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "k8s-conventions"


def _skill_ci_cd_builder(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "ci-cd-builder"
    d.mkdir(parents=True, exist_ok=True)
    lang = (ctx.language or "").lower()
    test_cmd = _get_test_cmd(ctx)
    build_cmd = _get_build_cmd(ctx)
    lint_cmd = ctx.linter or ("ruff check ." if lang == "python" else "eslint .")
    hosting = ctx.hosting or "your hosting provider"

    if lang == "python":
        lang_setup = (
            "      - uses: actions/setup-python@v5\n"
            "        with:\n"
            "          python-version: '3.12'\n"
            "          cache: pip\n\n"
            "      - name: Install\n"
            "        run: pip install -e '.[dev]'"
        )
        matrix_block = "    strategy:\n      matrix:\n        python-version: ['3.11', '3.12']\n"
    else:
        lang_setup = (
            "      - uses: actions/setup-node@v4\n"
            "        with:\n"
            "          node-version: 20\n"
            "          cache: npm\n\n"
            "      - name: Install\n"
            "        run: npm ci"
        )
        matrix_block = ""

    content = f"""---
name: ci-cd-builder
description: Builds GitHub Actions CI/CD pipeline configuration. Use when setting up or fixing automated pipelines.
---

# CI/CD Builder — GitHub Actions

## Standard Pipeline (.github/workflows/ci.yml)
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
{matrix_block}
    steps:
      - uses: actions/checkout@v4

{lang_setup}

      - name: Lint
        run: {lint_cmd}

      - name: Test
        run: {test_cmd}

      - name: Build
        run: {build_cmd}
```

## CD Pipeline (.github/workflows/deploy.yml)
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to {hosting}
        env:
          DEPLOY_TOKEN: ${{{{ secrets.DEPLOY_TOKEN }}}}
        run: |
          echo "Deploy to {hosting}"
```

## Pipeline Best Practices
- **Cache dependencies** — saves 30-60s per run
- **Fail fast** — lint before test, test before build
- **Secrets in GitHub Secrets** — never hardcode in YAML
- **Environment protection rules** — require approval for production
- **Branch protection** — require CI to pass before merge
- **Notifications** — Slack/email on failure

## Useful Actions
```yaml
# Cache pip
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{{{ runner.os }}}}-pip-${{{{ hashFiles('**/requirements*.txt') }}}}

# Upload test coverage
- uses: codecov/codecov-action@v4
  with:
    file: coverage.xml

# Auto-merge dependabot PRs
- uses: fastify/github-action-merge-dependabot@v3
```
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "ci-cd-builder"


def _skill_mutation_testing(skills_dir: Path, ctx: ProjectContext) -> str:
    d = skills_dir / "mutation-testing"
    d.mkdir(parents=True, exist_ok=True)
    lang = (ctx.language or "").lower()

    if lang == "python":
        tool = "mutmut"
        install = "pip install mutmut"
        run_cmd = "mutmut run"
        results_cmd = "mutmut results\nmutmut show <id>"
    elif lang in ("typescript", "javascript"):
        tool = "Stryker"
        install = "npm install -D @stryker-mutator/core @stryker-mutator/vitest-runner"
        run_cmd = "npx stryker run"
        results_cmd = "# Open reports/mutation/index.html"
    else:
        tool = "generic"
        install = "# Install your language's mutation testing tool"
        run_cmd = "# Run mutation tests"
        results_cmd = "# View results"

    content = f"""---
name: mutation-testing
description: Mutation testing to verify test quality. Use when coverage is high but bugs still slip through.
---

# Mutation Testing — {tool}

## What is Mutation Testing?
Code coverage tells you which lines are executed by tests.
Mutation testing tells you if your tests actually *catch bugs*.

A "mutant" is a small code change (e.g., `>` → `>=`, `True` → `False`).
If your tests don't catch the mutant, they're weak.

## Setup
```bash
{install}
```

## Run
```bash
{run_cmd}
```

## Analyze Results
```bash
{results_cmd}
```

## Mutation Score
- **> 80%**: Good — tests catch most mutations
- **60-80%**: Acceptable — some gaps to fill
- **< 60%**: Tests are too weak — improve assertions

## Common Surviving Mutants & Fixes

### Boundary mutations (`>` → `>=`)
```python
# Surviving mutant: if x > 0 → if x >= 0
# Fix: add boundary test
def test_zero_not_positive():
    assert not is_positive(0)  # catches >= mutation

def test_one_is_positive():
    assert is_positive(1)
```

### Boolean mutations
```python
# Surviving mutant: return True → return False
# Fix: test both branches
def test_is_active_when_status_active():
    assert user.is_active() is True

def test_not_active_when_status_inactive():
    assert user.is_active() is False  # don't just test truthy
```

### String mutations
```python
# Fix: assert exact strings, not just `in`
assert error_message == "Email is required"  # not just "assert 'Email' in msg"
```

## Focus Areas
Mutation testing is expensive. Focus on:
- Critical business logic (payment, auth, calculations)
- Functions with complex conditionals
- Areas with recent bug reports
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "mutation-testing"


def _skill_e2e_patterns(skills_dir: Path) -> str:
    d = skills_dir / "e2e-patterns"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: e2e-patterns
description: End-to-end testing patterns with Playwright. Use when writing E2E tests or setting up browser automation.
---

# E2E Patterns — Playwright

## What to Test with E2E
✅ Critical user journeys (signup, login, checkout, core feature)
✅ Cross-browser behavior (Chrome, Firefox, Safari)
✅ Authentication flows end-to-end
❌ Unit-testable logic (use unit tests instead)
❌ Every UI element (too brittle)

## Playwright Setup
```bash
npm install -D @playwright/test
npx playwright install
```

## Test Structure
```typescript
import { test, expect } from '@playwright/test'

test.describe('User authentication', () => {
  test('user can sign up and log in', async ({ page }) => {
    // Navigate
    await page.goto('/signup')

    // Fill form
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'SecurePass123!')
    await page.click('[data-testid="submit"]')

    // Assert redirect to dashboard
    await expect(page).toHaveURL('/dashboard')
    await expect(page.getByText('Welcome')).toBeVisible()
  })
})
```

## Page Object Pattern (for larger suites)
```typescript
class LoginPage {
  constructor(private page: Page) {}

  async login(email: string, password: string) {
    await this.page.goto('/login')
    await this.page.fill('#email', email)
    await this.page.fill('#password', password)
    await this.page.click('#submit')
  }

  async expectDashboard() {
    await expect(this.page).toHaveURL('/dashboard')
  }
}

test('user can login', async ({ page }) => {
  const loginPage = new LoginPage(page)
  await loginPage.login('user@example.com', 'password')
  await loginPage.expectDashboard()
})
```

## Test Data Strategy
- Use `data-testid` attributes (never CSS classes or text content)
- Create/cleanup test data via API calls in `beforeEach`/`afterEach`
- Use separate test database or test user accounts
- Seed data deterministically

## Flaky Test Prevention
```typescript
// ✅ Wait for element to be ready
await page.waitForLoadState('networkidle')
await expect(button).toBeEnabled()

// ❌ Arbitrary sleep (brittle)
await page.waitForTimeout(2000)
```

## Running Tests
```bash
# All tests
npx playwright test

# Specific file
npx playwright test auth.spec.ts

# With UI (debug mode)
npx playwright test --ui

# Generate report
npx playwright show-report
```

## CI Configuration
```yaml
- name: Install Playwright
  run: npx playwright install --with-deps chromium

- name: Run E2E tests
  run: npx playwright test
  env:
    BASE_URL: http://localhost:3000

- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-report
    path: playwright-report/
```
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
description: Generates OpenAPI spec and API documentation. Use when documenting or designing APIs.
---

# OpenAPI Generator

Generate a complete OpenAPI 3.1 spec for the current API.

## Minimal OpenAPI Spec Template
```yaml
openapi: 3.1.0
info:
  title: My API
  version: 1.0.0
  description: API description

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: http://localhost:8000/v1
    description: Development

paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: limit
          in: query
          schema: { type: integer, default: 20, maximum: 100 }
        - name: cursor
          in: query
          schema: { type: string }
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  nextCursor:
                    type: string

components:
  schemas:
    User:
      type: object
      required: [id, email]
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        name:
          type: string
        createdAt:
          type: string
          format: date-time

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer

security:
  - BearerAuth: []
```

## Process
1. Read the existing route/controller files
2. Identify all endpoints, params, and response shapes
3. Generate the OpenAPI YAML
4. Save to `openapi.yaml` or `docs/openapi.yaml`
5. Validate: `npx @redocly/cli lint openapi.yaml`

## Documentation Options
```bash
# Swagger UI (development)
npx @stoplight/prism-cli mock openapi.yaml

# ReDoc static HTML
npx @redocly/cli build-docs openapi.yaml

# Scalar (modern alternative)
npx @scalar/cli serve openapi.yaml
```

## Auto-generate from code
```bash
# FastAPI — auto-generated at /docs and /openapi.json
# NestJS — @nestjs/swagger
# Express — swagger-jsdoc
```
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

## Proto3 Service Template
```proto
syntax = "proto3";
package myservice.v1;

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

// Always version your package: myservice.v1
service UserService {
  rpc GetUser (GetUserRequest) returns (User);
  rpc ListUsers (ListUsersRequest) returns (ListUsersResponse);
  rpc CreateUser (CreateUserRequest) returns (User);
  rpc DeleteUser (DeleteUserRequest) returns (google.protobuf.Empty);
  // Server streaming for real-time updates
  rpc WatchUsers (WatchUsersRequest) returns (stream User);
}

message User {
  string id = 1;
  string email = 2;
  string name = 3;
  google.protobuf.Timestamp created_at = 4;
}

message GetUserRequest {
  string id = 1;
}

message ListUsersRequest {
  int32 page_size = 1;    // max 100
  string page_token = 2;  // cursor
}

message ListUsersResponse {
  repeated User users = 1;
  string next_page_token = 2;
}
```

## Field Number Rules
- 1-15: most frequently used fields (1-byte encoding)
- 16-2047: less frequent fields (2-byte encoding)
- Never reuse field numbers (breaks backward compat)
- Use `reserved` to prevent reuse of deleted fields:
  ```proto
  reserved 5, 6;
  reserved "old_field_name";
  ```

## Error Handling
Use Google's standard status codes:
```
OK, CANCELLED, UNKNOWN, INVALID_ARGUMENT, NOT_FOUND,
ALREADY_EXISTS, PERMISSION_DENIED, UNAUTHENTICATED,
RESOURCE_EXHAUSTED, FAILED_PRECONDITION, ABORTED,
INTERNAL, UNAVAILABLE, DEADLINE_EXCEEDED
```

## Versioning
- Package: `myservice.v1`, `myservice.v2`
- Breaking changes require a new version
- Backward compatible: adding optional fields, adding methods

## Generate Code
```bash
# Python
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. service.proto

# Node.js
npx grpc-tools node_modules/.bin/grpc_tools_node_protoc \\
  --js_out=. --grpc_out=grpc_js:. service.proto

# Go
protoc --go_out=. --go-grpc_out=. service.proto
```
"""
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return "grpc-conventions"


def _skill_query_optimization(skills_dir: Path) -> str:
    d = skills_dir / "query-optimization"
    d.mkdir(parents=True, exist_ok=True)
    content = """---
name: query-optimization
description: Database query optimization — indexing, EXPLAIN analysis, common anti-patterns. Use when queries are slow.
---

# Query Optimization

## Step 1: Find the Slow Queries
```sql
-- PostgreSQL: queries taking > 100ms
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;

-- MySQL: slow query log
SET GLOBAL slow_query_log = 1;
SET GLOBAL long_query_time = 0.1;
```

## Step 2: Analyze with EXPLAIN
```sql
-- PostgreSQL
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE user_id = 123 ORDER BY created_at DESC;

-- Look for:
-- Seq Scan on large tables → needs index
-- Nested Loop with high rows → missing index
-- Sort with high cost → add index on ORDER BY column
-- Hash Join → often OK but check row estimates
```

## Common Issues & Fixes

### Missing Index (most common)
```sql
-- Seq Scan detected → add index
CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders(user_id);
CREATE INDEX CONCURRENTLY idx_orders_created_at ON orders(created_at DESC);

-- Composite index for common WHERE + ORDER BY
CREATE INDEX CONCURRENTLY idx_orders_user_created
ON orders(user_id, created_at DESC);
```

### N+1 Queries
```python
# Problem
orders = Order.query.all()
for order in orders:
    print(order.user.email)  # 1 query per order!

# Fix: eager load
orders = Order.query.options(joinedload(Order.user)).all()
```

### SELECT * on Wide Tables
```sql
-- Bad: fetches all 50 columns
SELECT * FROM users WHERE email = 'alice@example.com';

-- Good: only needed columns
SELECT id, name, email FROM users WHERE email = 'alice@example.com';
```

### Missing Pagination
```sql
-- Bad: full table scan
SELECT * FROM events ORDER BY created_at DESC;

-- Good: cursor-based pagination
SELECT * FROM events
WHERE created_at < $cursor
ORDER BY created_at DESC
LIMIT 20;
```

### Inefficient COUNT
```sql
-- Slow on large tables
SELECT COUNT(*) FROM huge_table WHERE status = 'active';

-- Better: use approximate count or pre-aggregate
-- PostgreSQL: use pg_stat_user_tables for estimates
SELECT reltuples::bigint FROM pg_class WHERE relname = 'huge_table';
```

## Index Types
| Type | Use Case |
|------|----------|
| B-tree (default) | Equality, range, sorting |
| Hash | Equality only (fast) |
| GIN | Full-text search, JSONB |
| GiST | Geometric, full-text |
| Partial | `WHERE status = 'active'` |
| Covering | `INCLUDE (email)` to avoid table lookup |

## Checklist
- [ ] EXPLAIN shows no Seq Scan on large tables
- [ ] All foreign keys indexed
- [ ] All WHERE columns in queries have indexes
- [ ] ORDER BY columns indexed (DESC if needed)
- [ ] No SELECT * on tables > 10 columns
- [ ] All list queries have LIMIT
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


def _agent_dependency_auditor(agents_dir: Path, ctx: ProjectContext) -> str:
    lang = (ctx.language or "").lower()

    if lang == "python":
        audit_cmds = """```bash
# Check for known vulnerabilities
pip-audit                     # pip install pip-audit
safety check                  # pip install safety

# List outdated packages
pip list --outdated

# Check for unused dependencies
pip-check                     # pip install pip-check
```"""
        lock_file = "requirements.txt / pyproject.toml"
        update_note = "Use `pip install --upgrade <pkg>` after reviewing the changelog."
    elif lang in ("typescript", "javascript"):
        audit_cmds = """```bash
# Built-in audit
npm audit
npm audit --json              # machine-readable output
npm audit fix                 # auto-fix compatible issues
npm audit fix --force         # fix all (may break semver)

# Check outdated
npm outdated

# Interactive upgrade (install first: npm i -g npm-check-updates)
ncu                           # preview upgrades
ncu -u && npm install         # apply all
```"""
        lock_file = "package-lock.json / yarn.lock"
        update_note = "Check breaking changes in CHANGELOG before major version bumps."
    elif lang == "go":
        audit_cmds = """```bash
# Check for known vulnerabilities
govulncheck ./...             # go install golang.org/x/vuln/cmd/govulncheck@latest

# List outdated modules
go list -u -m all

# Update a specific module
go get module@latest
go mod tidy
```"""
        lock_file = "go.mod / go.sum"
        update_note = "Run `go mod tidy` after any dependency changes."
    elif lang == "rust":
        audit_cmds = """```bash
# Check for known vulnerabilities
cargo audit                   # cargo install cargo-audit

# Check outdated crates
cargo outdated                # cargo install cargo-outdated

# Update dependencies
cargo update                  # update within semver constraints
```"""
        lock_file = "Cargo.toml / Cargo.lock"
        update_note = "Commit Cargo.lock for binaries; .gitignore it for libraries."
    else:
        audit_cmds = """```bash
# Run your package manager's audit command
# npm audit / pip-audit / cargo audit / govulncheck
```"""
        lock_file = "dependency manifest"
        update_note = "Always review changelogs before upgrading major versions."

    content = f"""---
name: dependency-auditor
description: Audits project dependencies for security vulnerabilities and outdated packages. Use when asked to audit deps, check vulnerabilities, or update packages.
tools: Read, Bash
---

You are a dependency security auditor. Your job is to find vulnerable, outdated,
and unnecessary dependencies and recommend safe upgrade paths.

## Language: {ctx.language or "auto-detect"}
## Lock File: {lock_file}

## Audit Process

### 1. Check for Known Vulnerabilities
{audit_cmds}

### 2. Categorize Findings

**🔴 Critical / High** — must fix before next release
- Known CVEs with CVSS score ≥ 7.0
- Remote code execution, injection, auth bypass risks

**🟡 Medium** — fix in next sprint
- CVSS 4.0–6.9
- Denial of service, information disclosure

**🟢 Low / Info** — track but don't rush
- Minor version drift
- Deprecation warnings

### 3. Upgrade Recommendations
- For each vulnerable package: check if a patched version exists
- If yes: provide exact upgrade command
- If no patch: suggest alternative package or mitigation
- {update_note}

### 4. Unused Dependencies
- Identify packages in the manifest that aren't imported anywhere
- Recommend removal if safe

## Output Format
```
## Dependency Audit Report

### 🔴 Critical (fix now)
| Package | Current | Safe Version | CVE | Command |
|---------|---------|--------------|-----|---------|
| lodash  | 4.17.15 | 4.17.21      | CVE-2021-23337 | npm install lodash@4.17.21 |

### 🟡 Medium
...

### 🟢 Outdated (not vulnerable)
...

### 🗑️ Potentially Unused
...

### Summary
- X critical, Y medium, Z low issues
- Estimated fix time: N minutes
```
"""
    p = agents_dir / "dependency-auditor.md"
    p.write_text(content, encoding="utf-8")
    return "dependency-auditor"


def _agent_performance_profiler(agents_dir: Path, ctx: ProjectContext) -> str:
    lang = (ctx.language or "").lower()

    if lang == "python":
        profile_cmds = """```bash
# CPU profiling
python -m cProfile -s cumtime your_script.py
python -m cProfile -o profile.stats your_script.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

# Memory profiling
pip install memory-profiler
python -m memory_profiler your_script.py

# Line-level profiling
pip install line-profiler
kernprof -l -v your_script.py

# Flamegraph (visual)
pip install py-spy
py-spy record -o profile.svg -- python your_script.py
```"""
    elif lang in ("typescript", "javascript"):
        profile_cmds = """```bash
# Node.js CPU profiling
node --prof your_script.js
node --prof-process isolate-*.log > profile.txt

# Clinic.js (visual profiling)
npm install -g clinic
clinic doctor -- node your_script.js
clinic flame -- node your_script.js

# Browser: Chrome DevTools Performance tab
# React: React DevTools Profiler (built-in)

# Bundle size analysis
npm run build
npx vite-bundle-visualizer     # for Vite
npx webpack-bundle-analyzer    # for webpack
```"""
    elif lang == "go":
        profile_cmds = """```bash
# CPU profiling
go test -cpuprofile=cpu.prof -bench=.
go tool pprof cpu.prof

# Memory profiling
go test -memprofile=mem.prof -bench=.
go tool pprof mem.prof

# Flamegraph (visual)
go install github.com/google/pprof@latest
pprof -http=:8080 cpu.prof

# HTTP profiling endpoint (add to main.go for live profiling)
import _ "net/http/pprof"
go tool pprof http://localhost:6060/debug/pprof/profile
```"""
    elif lang == "rust":
        profile_cmds = """```bash
# Criterion benchmarks
cargo bench

# Flamegraph
cargo install flamegraph
cargo flamegraph --bin your_binary

# Perf (Linux)
cargo build --release
perf record target/release/your_binary
perf report

# Heaptrack (memory)
heaptrack target/release/your_binary
heaptrack_gui heaptrack.your_binary.*.zst
```"""
    else:
        profile_cmds = """```bash
# Use your language's profiling tools:
# Python: cProfile, py-spy
# Node.js: --prof, clinic.js
# Go: pprof
# Rust: flamegraph, criterion
```"""

    content = f"""---
name: performance-profiler
description: Profiles application performance to find bottlenecks. Use when asked to profile, optimize performance, or investigate slowness.
tools: Read, Bash, Grep
---

You are a performance engineer. Find real bottlenecks with data, then optimize.

## Language: {ctx.language or "auto-detect"}

## Golden Rule
**Never optimize without profiling first.** Intuition is wrong 80% of the time.
Measure → Find real bottleneck → Optimize → Measure again.

## Step 1: Profile
{profile_cmds}

## Step 2: Identify the Real Bottleneck
Look for:
- Functions with highest **cumulative time** (hot paths)
- Functions called **millions of times** with tiny individual cost
- **Memory allocation pressure** (GC pauses, frequent allocs)
- **I/O waits** (DB queries, network calls, disk reads)
- **N+1 query patterns** (DB call inside a loop)

## Step 3: Optimize (in order of impact)
1. **Algorithm**: O(n²) → O(n log n) gives 1000x at scale
2. **I/O batching**: 1 query for 100 items vs 100 queries
3. **Caching**: avoid recomputing identical results
4. **Data structures**: wrong choice → 10-100x slowdown
5. **Parallelism**: CPU-bound work → worker pool / threads
6. **Memory**: excessive copies → borrow/reuse

## Step 4: Verify Improvement
```bash
# Benchmark BEFORE
# Make change
# Benchmark AFTER
# Confirm: Xms → Yms improvement (Z% faster)
```

## Output Format
```
## Performance Analysis

### Profiling Results
- Top hotspot: `function_name` — X% of total time
- Called N times, avg Xms per call

### Root Cause
[Explain exactly why it's slow]

### Optimization Applied
[What was changed and why]

### Results
Before: Xms / Xrps
After:  Yms / Yrps (+Z% improvement)
```
"""
    p = agents_dir / "performance-profiler.md"
    p.write_text(content, encoding="utf-8")
    return "performance-profiler"


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


def _scaffold_contributing(output_dir: str, ctx: ProjectContext) -> str:
    """Generate CONTRIBUTING.md — contribution guide for the project."""
    lang = (ctx.language or "").lower()
    test_cmd = ctx.test_framework or ("pytest" if lang == "python" else "npm test")
    lint_cmd = ctx.linter or ("ruff check ." if lang == "python" else "eslint .")
    fmt_cmd = ctx.formatter or ("ruff format ." if lang == "python" else "prettier --write .")
    setup_cmd = "pip install -r requirements.txt" if lang == "python" else "npm install"
    if lang == "go":
        setup_cmd = "go mod tidy"
    elif lang == "rust":
        setup_cmd = "cargo build"

    content = f"""# Contributing to {ctx.project_name}

Thank you for your interest in contributing! This guide covers everything you need to get started.

## Getting Started

### Prerequisites
- Git
- {ctx.language or "The project's language runtime"}{f" / {ctx.framework}" if ctx.framework else ""}

### Setup
```bash
git clone <repo-url>
cd {ctx.project_name}
{setup_cmd}
```

### Verify everything works
```bash
{test_cmd}
```

## Development Workflow

### 1. Create a branch
```bash
git checkout -b feat/your-feature-name
# or: fix/bug-name, docs/topic, refactor/module-name
```

### 2. Make your changes
- Write code following the project's conventions (see `CLAUDE.md` or `AGENTS.md`)
- Add tests for new functionality
- Keep changes focused — one logical change per PR

### 3. Run checks before committing
```bash
{fmt_cmd}       # Format
{lint_cmd}      # Lint
{test_cmd}      # Tests — all must pass
```

### 4. Commit with conventional commits
```
feat(scope): add new feature
fix(scope): fix bug description
docs: update README
test: add tests for X
refactor: simplify Y
chore: update dependencies
```

### 5. Open a Pull Request
- Fill in the PR template
- Ensure CI is green
- Request a review

## Pull Request Guidelines

- **Keep PRs small** — easier to review and less likely to conflict
- **Write a clear description** — what, why, and how
- **One feature per PR** — don't bundle unrelated changes
- **Tests required** — new features need tests; bug fixes ideally include a regression test
- **No secrets** — never commit API keys, tokens, or passwords

## Code Style

This project uses:
- **Formatter**: `{fmt_cmd}` — run before every commit
- **Linter**: `{lint_cmd}` — fix all warnings

If you've installed pre-commit hooks (`pre-commit install`), these run automatically.

## Reporting Issues

- **Bugs**: include steps to reproduce, expected behavior, actual behavior
- **Features**: describe the use case and why it's valuable
- **Security**: email the maintainers directly — do not open a public issue

## Questions?

Open a Discussion or reach out to the maintainers.

---
*Generated by [vcsx](https://github.com/barancanercan/vcsx)*
"""
    p = Path(output_dir) / "CONTRIBUTING.md"
    p.write_text(content, encoding="utf-8")
    return "CONTRIBUTING.md"


def _scaffold_changelog(output_dir: str, ctx: ProjectContext) -> str:
    """Generate CHANGELOG.md — Keep a Changelog format."""
    content = f"""# Changelog

All notable changes to {ctx.project_name} will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup

### Changed

### Deprecated

### Removed

### Fixed

### Security

---

## How to update this file

When making changes, add an entry under `[Unreleased]`:
- **Added** — for new features
- **Changed** — for changes in existing functionality
- **Deprecated** — for soon-to-be removed features
- **Removed** — for now removed features
- **Fixed** — for bug fixes
- **Security** — for vulnerability fixes

When releasing a new version, rename `[Unreleased]` to `[x.y.z] — YYYY-MM-DD`
and add a new empty `[Unreleased]` section above it.

Example:
```markdown
## [1.2.0] — 2026-04-04

### Added
- New feature X

### Fixed
- Bug in module Y
```
"""
    p = Path(output_dir) / "CHANGELOG.md"
    if not p.exists():  # Don't overwrite existing CHANGELOG
        p.write_text(content, encoding="utf-8")
    return "CHANGELOG.md"


def _scaffold_precommit_config(output_dir: str, ctx: ProjectContext) -> str:
    """Generate .pre-commit-config.yaml — language-aware pre-commit hooks."""
    lang = (ctx.language or "").lower()
    fmt = ctx.formatter or ""
    lint = ctx.linter or ""
    test_cmd = ctx.test_framework or ""

    # Base hooks (language-agnostic)
    base_hooks = """  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-merge-conflict
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: detect-private-key
      - id: no-commit-to-branch
        args: ["--branch", "main", "--branch", "develop"]"""

    if lang == "python":
        ruff_rev = "v0.4.0"
        formatter_id = "ruff-format" if "ruff" in fmt else "black"
        linter_id = "ruff" if "ruff" in lint else "flake8"
        lang_hooks = f"""
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: {ruff_rev}
    hooks:
      - id: {linter_id}
        args: ["--fix"]
      - id: {formatter_id}

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: ["types-requests", "types-PyYAML"]
        args: ["--ignore-missing-imports"]"""

        test_hook = f"""
  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest (fast)
        entry: {test_cmd or "pytest"}
        language: system
        pass_filenames: false
        always_run: false
        stages: [pre-push]""" if test_cmd or lang == "python" else ""

    elif lang in ("typescript", "javascript"):
        lang_hooks = """
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.57.0
    hooks:
      - id: eslint
        files: \\.(js|ts|jsx|tsx)$
        additional_dependencies:
          - eslint
          - "@typescript-eslint/parser"
          - "@typescript-eslint/eslint-plugin"

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        files: \\.(js|ts|jsx|tsx|json|md|yaml|css)$"""

        test_hook = """
  - repo: local
    hooks:
      - id: vitest
        name: vitest
        entry: npx vitest run
        language: system
        pass_filenames: false
        always_run: false
        stages: [pre-push]"""

    elif lang == "go":
        lang_hooks = """
  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:
      - id: go-fmt
      - id: go-vet
      - id: go-lint
      - id: go-unit-tests
        args: ["-race"]"""
        test_hook = ""

    elif lang == "rust":
        lang_hooks = """
  - repo: local
    hooks:
      - id: cargo-fmt
        name: cargo fmt
        entry: cargo fmt --all -- --check
        language: system
        pass_filenames: false

      - id: cargo-clippy
        name: cargo clippy
        entry: cargo clippy -- -D warnings
        language: system
        pass_filenames: false
        stages: [pre-push]"""
        test_hook = ""

    else:
        lang_hooks = ""
        test_hook = ""

    content = f"""# .pre-commit-config.yaml
# Install: pip install pre-commit && pre-commit install
# Run all: pre-commit run --all-files
# Update hooks: pre-commit autoupdate

repos:
{base_hooks}{lang_hooks}{test_hook}

# CI integration: add `pre-commit run --all-files` to your CI pipeline
# or use: https://pre-commit.ci (free for open source)
"""

    p = Path(output_dir) / ".pre-commit-config.yaml"
    p.write_text(content, encoding="utf-8")
    return ".pre-commit-config.yaml"


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
