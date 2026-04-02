"""CLI tool registry — maps tool names to generators.

To add a new CLI tool:
1. Create generators/new_tool.py implementing BaseGenerator
2. Import it here
3. Add to CLI_TOOLS dict
4. Done.
"""

from vcsx.generators.base import BaseGenerator
from vcsx.generators.claude_code import ClaudeCodeGenerator
from vcsx.generators.codex import CodexGenerator
from vcsx.generators.copilot import CopilotGenerator
from vcsx.generators.cursor import CursorGenerator

CLI_TOOLS: dict[str, type[BaseGenerator]] = {
    "claude-code": ClaudeCodeGenerator,
    "cursor": CursorGenerator,
    "codex": CodexGenerator,
    "copilot": CopilotGenerator,
}

ALL_TOOLS = list(CLI_TOOLS.keys())


def get_generator(tool_name: str) -> BaseGenerator:
    """Get a generator instance by tool name."""
    if tool_name not in CLI_TOOLS:
        raise ValueError(f"Unknown CLI tool: {tool_name}. Available: {ALL_TOOLS}")
    return CLI_TOOLS[tool_name]()


def get_all_generators() -> list[BaseGenerator]:
    """Get all generator instances."""
    return [cls() for cls in CLI_TOOLS.values()]
