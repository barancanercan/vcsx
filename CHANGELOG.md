# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [5.1.0] - 2026-04-03

### New Features
- **`vcsx version`**: Show current version with last 3 changelog entries inline
- **`vcsx export --format json`**: Export AI config manifest as structured JSON (with file contents)
- **94% test coverage**: Added tests for `planner.py`, `templates/engine.py`, `utils/prompts.py` (608 tests total)

### Improvements
- `export` command now supports `--format [zip|json]` flag

## [5.0.0] - 2026-04-03

### Major Release — Production Quality

#### New Commands (9 new since v4.0)
- **`vcsx init --scan`**: Auto-detect tech stack from existing project files
- **`vcsx init --fast`**: Minimal wizard (project name + stack only)
- **`vcsx audit [--fix]`**: Comprehensive config audit with auto-fix
- **`vcsx compare <a> <b>`**: Diff AI configs between two projects
- **`vcsx search <query>`**: Search inside skill/hook/agent files
- **`vcsx stats`**: Count skills, hooks, agents, rules per tool
- **`vcsx export [--include-all]`**: ZIP archive of AI configs
- **`vcsx config`**: User settings (~/.vcsx/config.json)
- **`vcsx gemini-global`**: Create ~/.gemini/GEMINI.md global config

#### New Modules
- **`src/vcsx/core/scanner.py`**: Project scanner — auto-detects language, framework, project type from pyproject.toml, package.json, go.mod, Cargo.toml, pubspec.yaml, pom.xml
- **`src/vcsx/generators/_shared.py`**: Centralized command/style helpers (eliminates duplication across 8 generators)

#### Languages (11 total, was 5)
Added: Kotlin, Swift, Dart, C#, PHP, Ruby (each with framework_map, test_fw, formatter, linter)

#### Templates (10 total, was 5)
Added: django-api, flutter-app, saas-nextjs, python-cli, rust-api

#### Generator Quality
- All 22 Claude Code skills rewritten with production content
- Windsurf rules: 4 rich scoped rule files (core, testing, security, api/data)
- Cursor MDC: pr-review severity table, test AAA pattern, api URL table
- Zed: real settings schema, tasks.json, language-aware LSP/formatter
- Bolt: system prompt, port detection, 7 prompt templates, env var detection
- Aider: valid YAML-only (removed invalid keys)

#### Testing
- 42 → **419 tests**
- Coverage: ~50% → **85%**
- Modules at 95%+: inference (100%), gemini (100%), claude_code (98%), codex (98%), _shared (94%), aider (95%), scanner (95%)

## [4.5.0] - 2026-04-03

### Added
- **`vcsx export [path]`**: Export all AI config files to a ZIP archive. Supports `--output` and `--include-all` flags.
- **`vcsx stats [path]`**: Show per-tool statistics — skills, hooks, agents, rules count.
- **`vcsx changelog`**: Show CHANGELOG from installed package. Flags: `--latest`, `--version`.
- **`vcsx update --auto`**: Auto-apply all detected upgrades (.claudeignore, AGENTS.md, .windsurf/rules/) without prompting.
- **`vcsx new --preset`**: Use template presets (fastapi-postgres, react-typescript, nextjs, go-api, rust-cli).
- **7 new languages in inference engine**: Kotlin, Swift, Dart, C#, PHP, Ruby — each with framework_map, test_framework, formatter, linter.
- **4 new Claude Code agents**: code-reviewer, debugger, api-designer (api projects), data-analyst (data projects).

### Changed
- `vcsx new --lang`: extended choices to include kotlin/swift/dart/csharp/php/ruby.
- `vcsx update`: added `--auto` flag for non-interactive upgrades.

## [4.4.0] - 2026-04-03

### Added
- **`vcsx generate <tool>`**: Generate a single tool's config files directly without the wizard. Flags: `--project-name`, `--lang`, `--type`, `--output-dir`. Fast one-liner for adding a specific config.
- **127 tests total** (previously 123): Added TestGenerateCommand (4 tests).

## [4.3.0] - 2026-04-03

### Added
- **`vcsx migrate <tool>`**: Migrate existing configs to latest format. Supports windsurf (→ .windsurf/rules/), cursor (→ .cursor/rules/), claude-code (+ .claudeignore + agents/), copilot (+ scoped instructions/). Includes `--dry-run` flag.
- **`vcsx completion <shell>`**: Print shell completion setup for bash, zsh, fish, powershell.
- **CLI integration tests** (tests/test_cli.py): 26 tests using Click test runner covering all commands.

### Changed
- README: Updated version banner to v4.2.0.
- `vcsx check`: improved JSON output format with path field.

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
