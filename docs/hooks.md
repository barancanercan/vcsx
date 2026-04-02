# vcsx Hooks Reference

vcsx generates 13 hooks for Claude Code projects. Hooks are automated scripts that run on specific events.

## Hook Types

### PreToolUse Hooks (Run before tool use)

#### block_destructive.sh
Blocks destructive commands.
- **Trigger**: Before any Bash command
- **Blocked**: rm -rf, git push --force, DROP TABLE, etc.
- **Exit Code**: 2 to block

#### validate_syntax.sh
Validates code syntax.
- **Trigger**: Before Bash commands
- **Languages**: TypeScript, Python, Go, Rust

#### check_permissions.sh
Warns about permission changes.
- **Trigger**: Before chmod/chown commands
- **Action**: Warning only (non-blocking)

### PostToolUse Hooks (Run after tool use)

#### auto_format.sh
Auto-formats files on save.
- **Trigger**: After Write/Edit operations
- **Uses**: Project formatter (prettier, black, etc.)

#### auto_lint.sh
Runs linter after edits.
- **Trigger**: After Write/Edit operations
- **Uses**: Project linter (eslint, ruff, etc.)

#### type_check.sh
Runs type checking.
- **Trigger**: After Write/Edit operations
- **Languages**: TypeScript, Python, Go, Rust

#### secret_scan.sh
Scans for secrets in code.
- **Trigger**: After Write/Edit operations
- **Patterns**: API keys, tokens, passwords

### SessionStart Hooks (Run on session start)

#### check_env.sh
Checks environment variables.
- **Trigger**: On session start
- **Checks**: NODE_ENV, DATABASE_URL

#### check_deps.sh
Checks if dependencies installed.
- **Trigger**: On session start
- **Checks**: node_modules, venv, go.sum

#### git_status.sh
Shows git status.
- **Trigger**: On session start
- **Shows**: Unstaged, untracked files

### Stop Hooks (Run on session end)

#### run_tests.sh
Runs test suite.
- **Trigger**: Before session ends
- **Uses**: pytest, vitest, etc.

#### cleanup_temp.sh
Cleans up temp files.
- **Trigger**: Before session ends
- **Cleans**: *.tmp, __pycache__, .pytest_cache

#### commit_prompt.sh
Prompts for commit.
- **Trigger**: Before session ends
- **Prompts**: If uncommitted changes

## Hook Configuration

Hooks are configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "SessionStart": [...],
    "Stop": [...]
  }
}
```

## Customization

Edit `.claude/settings.json` to add/remove hooks. Each hook needs:
- `matcher`: Regex to match tool use
- `hooks[]`: Array of hook configurations
- `type`: "command"
- `command`: Path to hook script
- `statusMessage`: Status message during execution
