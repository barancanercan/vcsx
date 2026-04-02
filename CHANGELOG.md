# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-04-02

### Added
- Multi-CLI support: Claude Code, Cursor, OpenAI Codex, GitHub Copilot
- Plugin-based generator architecture with registry pattern
- `BaseGenerator` abstract interface for easy extension
- 4 built-in generators (claude-code, cursor, codex, copilot)
- Interactive discovery engine with smart tech stack inference
- Plan generation with user confirmation before setup
- 8 built-in skills: commit-message, pr-review, deploy, test-patterns, auth-conventions, api-conventions, security-review, refactor
- 3 built-in agents: security-reviewer, test-writer, researcher
- 4 hook scripts: block_destructive, auto_format, auto_lint, secret_scan
- Turkish and English language support
- Comprehensive test suite (29+ tests)
- GitHub Actions CI/CD with Python 3.10-3.13 matrix
- Pre-commit hooks configuration
- CONTRIBUTING.md with new CLI tool guide

### Changed
- Complete rewrite from v0.1.0 with modular architecture
- Split into core, generators, and utils packages
- Improved inference engine for language/framework detection

### Removed
- Jinja2 dependency (templates now generated in Python)
- Hardcoded single-CLI design

## [0.1.0] - 2026-04-02

### Added
- Initial Claude Code setup generator
- Basic discovery questionnaire
- Plan generation
- CLAUDE.md, skills, hooks, agents generators
- Project scaffold generation
