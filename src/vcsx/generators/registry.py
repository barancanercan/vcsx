"""CLI tool registry — maps tool names to generators.

To add a new CLI tool:
1. Create generators/new_tool.py implementing BaseGenerator
2. Import it here
3. Add to CLI_TOOLS dict
4. Done.
"""

from vcsx.generators.base import BaseGenerator
from vcsx.generators.aider import AiderGenerator
from vcsx.generators.bolt import BoltGenerator
from vcsx.generators.claude_code import ClaudeCodeGenerator
from vcsx.generators.codex import CodexGenerator
from vcsx.generators.copilot import CopilotGenerator
from vcsx.generators.cursor import CursorGenerator
from vcsx.generators.windsurf import WindsurfGenerator
from vcsx.generators.zed import ZedGenerator

CLI_TOOLS: dict[str, type[BaseGenerator]] = {
    "claude-code": ClaudeCodeGenerator,
    "cursor": CursorGenerator,
    "codex": CodexGenerator,
    "copilot": CopilotGenerator,
    "windsurf": WindsurfGenerator,
    "zed": ZedGenerator,
    "aider": AiderGenerator,
    "bolt": BoltGenerator,
}

ALL_TOOLS = list(CLI_TOOLS.keys())

TOOL_CATEGORIES = {
    "ai_editors": ["claude-code", "cursor", "windsurf", "zed"],
    "terminal_ai": ["aider"],
    "web_ai": ["bolt"],
    "code_assist": ["codex", "copilot"],
}

TOOL_DESCRIPTIONS = {
    "claude-code": "Anthropic's CLI AI assistant",
    "cursor": "AI-first code editor",
    "windsurf": "Windsurf IDE by Codeium",
    "zed": "Zed editor with AI",
    "aider": "Terminal-based AI pair programming",
    "bolt": "Bolt.new web-first AI development",
    "codex": "OpenAI Codex CLI",
    "copilot": "GitHub Copilot CLI",
}


def get_generator(tool_name: str) -> BaseGenerator:
    """Get a generator instance by tool name."""
    if tool_name not in CLI_TOOLS:
        raise ValueError(f"Unknown CLI tool: {tool_name}. Available: {ALL_TOOLS}")
    return CLI_TOOLS[tool_name]()


def get_all_generators() -> list[BaseGenerator]:
    """Get all generator instances."""
    return [cls() for cls in CLI_TOOLS.values()]


def get_tools_by_category(category: str) -> list[str]:
    """Get tools by category."""
    return TOOL_CATEGORIES.get(category, [])
