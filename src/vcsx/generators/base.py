"""Base generator interface — all CLI tool generators must implement this."""

from abc import ABC, abstractmethod
from typing import Any

from vcsx.core.context import ProjectContext


class BaseGenerator(ABC):
    """Abstract base class for CLI tool generators."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the CLI tool name (e.g., 'claude-code', 'cursor')."""
        ...

    @property
    @abstractmethod
    def output_files(self) -> list[str]:
        """Return list of files this generator creates."""
        ...

    @abstractmethod
    def generate_config(self, ctx: ProjectContext, output_dir: str) -> Any:
        """Generate main config file (CLAUDE.md, .cursorrules, etc.)."""
        ...

    @abstractmethod
    def generate_skills(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate skill/rule files."""
        ...

    @abstractmethod
    def generate_hooks(self, ctx: ProjectContext, output_dir: str) -> Any:
        """Generate hook/automation configuration."""
        ...

    @abstractmethod
    def generate_agents(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate agent/worker definitions."""
        ...

    @abstractmethod
    def generate_scaffold(self, ctx: ProjectContext, output_dir: str) -> list[str]:
        """Generate project scaffold (gitignore, README, config files)."""
        ...

    def generate_all(self, ctx: ProjectContext, output_dir: str) -> dict:
        """Run all generators and return summary."""
        return {
            "config": self.generate_config(ctx, output_dir),
            "skills": self.generate_skills(ctx, output_dir),
            "hooks": self.generate_hooks(ctx, output_dir),
            "agents": self.generate_agents(ctx, output_dir),
            "scaffold": self.generate_scaffold(ctx, output_dir),
        }
