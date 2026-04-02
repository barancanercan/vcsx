---
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

## Examples
- `feat(auth): add OAuth2 login flow`
- `fix(api): handle null response in user endpoint`
- `refactor(db): extract query builder to separate module`
- `chore(deps): update dependencies to latest versions`
