# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [4.2.0] - 2026-04-03

### Added
- **`vcsx check [path]`**: Analyze project's AI config quality and produce a 0-100% score per tool. Detects core files, quality extras, and gives actionable recommendations. Supports `--json` for CI integration.
- **`vcsx new <name>`**: Scaffold a new project without the full wizard. Flags: `--type`, `--lang`, `--tool` (multi-value). Creates project directory and runs generators automatically.
- **`generators/_shared.py`**: Centralized helper module — `get_setup_cmd`, `get_build_cmd`, `get_dev_cmd`, `get_test_cmd`, `get_lint_cmd`, `get_format_cmd`, `get_style_rules`, `get_commands_block`. Eliminates duplication across 8 generator modules.
- **Multi-tool discovery**: Discovery Phase 0 now supports `all` keyword and comma-separated tool list (e.g., `claude-code, cursor, gemini`).

### Changed
- `ProjectContext`: Added `ai_tools_list: list` field for multi-tool selection tracking.
- `vcsx init`: Uses `ai_tools_list` from discovery context when `--cli` flags not provided.
- `_shared.get_setup_cmd`: pnpm/yarn-aware, pyproject.toml detection.
- `_shared.get_dev_cmd`: FastAPI/Flask/Django-aware dev server commands.

## [4.1.0] - 2026-04-03

### Added
- **Multi-tool `vcsx init`**: `vcsx init -c claude-code -c cursor` sets up multiple AI tools in one pass. New `--all-tools` / `-a` flag generates configs for all 10 tools at once.
- **`vcsx doctor` enhanced**: Now scans the target project directory and shows a full config status table — which AI tools are set up, quality level (complete vs basic), and actionable upgrade tips.
- **`vcsx info` improved**: Now shows generated file list alongside tool description and category.
- **`vcsx list` improved**: Added footer with usage hints for multi-tool setup.
- **28 new tests** (42 → 70): Added full test coverage for Aider, Bolt, and Zed generators. Added `TestMultiToolInit` (all 10 generators can run on same directory without conflicts), `TestDoctorDetection`, and generator property tests.
- **Aider config rewrite**: `.aider.conf.yaml` now uses only valid Aider CLI flags (model, weak-model, auto-commits, dirty-commits, auto-lint, lint-cmd, auto-test, test-cmd, read, map-tokens, cache-prompts). Removed invalid keys (`repo`, `tools`, `command`, `only`, `max-context-characters`).

### Changed
- README: Updated version banner to v4.0.0, corrected repo URLs from `vibe-coding-setup-expert/vcsx` → `barancanercan/vcsx`.
- pyproject.toml: Corrected Homepage/Repository URLs to `barancanercan/vcsx`.
- Bolt: Updated model name from `claude-sonnet-4` → `claude-sonnet-4-5` (correct API identifier).
- `.aider.context.md` now includes Purpose/Problem blocks from discovery context.

### Fixed
- `vcsx update` detection map: added `.zed/` detection.
- README discovery section header: v3.3 → v4.0.

## [4.0.0] - 2026-04-02

### Added
- **Gemini CLI generator** (`gemini`): Generates `GEMINI.md` for Google's Gemini CLI with 1M token context window. Includes project-type-specific guidance and context management tips.
- **AGENTS.md generator** (`agents-md`): Generates the Linux Foundation-stewarded universal `AGENTS.md` standard. Supported by Codex CLI, Claude Code (fallback), Cursor, Gemini CLI, Aider, Continue.dev, and OpenHands.
- **.claudeignore generation**: Claude Code setup now automatically generates `.claudeignore` to keep context windows clean. Includes language-specific and project-type-specific patterns. Based on 2026 best practices ("context engineering").
- **`vcsx update` command**: Detect and add missing AI config files to existing projects. Supports `--dry-run` and `--tool` flags.
- **Windsurf new format**: Added `.windsurf/rules/*.md` scoped rule files (alwaysApply, globs). Core conventions, testing, security, and API rules generated automatically.
- **GitHub Copilot scoped instructions**: Added `.github/instructions/*.instructions.md` files with `applyTo` frontmatter. Generates code-style, testing, and security instruction files.
- **`data-pipeline` project type**: Dedicated structure for scraping/ETL/data science projects (`scrapers/`, `intel/`, `data/`, `reports/`). SQLite best practices, chunked processing rules included.
- **`ml-model` project type**: ML project structure (`src/data/`, `models/`, `experiments/`, `notebooks/`).
- **Improved hook scripts**: `block_destructive.sh` now blocks curl|sh, wget|bash, chmod 777 /, git push --force (various forms). `secret_scan.sh` uses real provider-specific regex patterns (OpenAI sk-, AWS AKIA, GitHub ghp_, Stripe sk_live_, etc.).

### Changed
- `AI_TOOLS` list now includes `gemini` and `agents-md`.
- Tool count: 8 → 10 tools.
- `TOOL_DESCRIPTIONS` updated with 2026-accurate descriptions.
- Windsurf: legacy `.windsurfrules` retained for backward compat + new `.windsurf/rules/` added.

### Fixed
- Existing test for `get_all_generators` count updated to reflect new tools.

## [3.3.0] - 2026-04-02

### Added
- **Purpose-driven discovery**: New questions for purpose, problem, user_stories, success_criteria
- **Rich prompt metadata**: Each question now has description, hint, placeholder, examples, options
- **6-phase discovery flow** (Phase 0-5): Organized discovery with clear sections
- **Smart branching**: Auth question now triggers auth_method question
- **Detailed plan explanations**: Each generated file now includes what it does and how to use it
- **Cursor .mdc format**: Updated Cursor generator to use new frontmatter format (description, globs, alwaysApply)
- **Windsurf conventions.md**: Enhanced with detailed code style rules and best practices
- **Zed hooks.toml**: Added pre-commit and on-save hooks
- **Aider detailed commit-prompt**: Enhanced with conventional commits examples and rules
- **Bolt prompts.md**: Added AI prompt templates (New Feature, Bug Fix, Refactor, Run Tests)
- **Auto-detect AI tool**: Config files are now automatically detected (.cursorrules, .claude/settings.json, etc.)
- **AI tool as first question**: Tool selection is now the first question in discovery

### Changed
- Discovery now prioritizes purpose and problem before technical details
- Plan output now shows what each file does in detail

### Fixed
- Tests now correctly pass with all 8 generators

## [3.2.0] - 2026-04-02

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
