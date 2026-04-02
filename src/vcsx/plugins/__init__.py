"""Plugin base classes and loader system for vcsx."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from importlib import import_module, metadata
from typing import Any


@dataclass
class PluginMetadata:
    """Plugin metadata container."""

    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    home_url: str = ""
    repo_url: str = ""


class Plugin(ABC):
    """Base class for all vcsx plugins."""

    def __init__(self):
        self._enabled = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin unique name."""
        ...

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata."""
        ...

    @abstractmethod
    def register(self, registry: "PluginRegistry") -> None:
        """Register plugin with the registry."""
        ...

    @abstractmethod
    def unregister(self, registry: "PluginRegistry") -> None:
        """Unregister plugin from the registry."""
        ...

    def enable(self) -> None:
        """Enable the plugin."""
        self._enabled = True

    def disable(self) -> None:
        """Disable the plugin."""
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._enabled


class PluginRegistry:
    """Central plugin registry for vcsx."""

    def __init__(self):
        self._plugins: dict[str, Plugin] = {}
        self._hooks: dict[str, list[Callable]] = {}

    def register(self, plugin: Plugin) -> None:
        """Register a plugin."""
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin already registered: {plugin.name}")
        plugin.register(self)
        plugin.enable()
        self._plugins[plugin.name] = plugin

    def unregister(self, plugin_name: str) -> None:
        """Unregister a plugin by name."""
        if plugin_name in self._plugins:
            plugin = self._plugins.pop(plugin_name)
            plugin.unregister(self)

    def get(self, name: str) -> Plugin | None:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def list_all(self) -> list[Plugin]:
        """List all registered plugins."""
        return list(self._plugins.values())

    def list_enabled(self) -> list[Plugin]:
        """List all enabled plugins."""
        return [p for p in self._plugins.values() if p.is_enabled]

    def add_hook(self, event: str, callback: Callable) -> None:
        """Add a hook callback for an event."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)

    def remove_hook(self, event: str, callback: Callable) -> None:
        """Remove a hook callback."""
        if event in self._hooks:
            self._hooks[event] = [c for c in self._hooks[event] if c != callback]

    def trigger(self, event: str, *args: Any, **kwargs: Any) -> list[Any]:
        """Trigger all hooks for an event."""
        results = []
        if event in self._hooks:
            for callback in self._hooks[event]:
                result = callback(*args, **kwargs)
                results.append(result)
        return results


_default_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    """Get the default plugin registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = PluginRegistry()
    return _default_registry


def load_default_plugins() -> None:
    """Load all default vcsx plugins."""
    get_registry()

    builtins = [
        "vcsx.generators.claude_code",
        "vcsx.generators.cursor",
        "vcsx.generators.codex",
        "vcsx.generators.copilot",
    ]

    for module_name in builtins:
        try:
            import_module(module_name)
        except ImportError:
            pass


def discover_plugins() -> list[PluginMetadata]:
    """Discover installed vcsx plugins."""
    plugins = []
    for entry_point in metadata.entry_points(group="vcsx.plugins"):
        try:
            version = entry_point.load().version or "1.0.0"
        except Exception:
            version = "1.0.0"
        plugins.append(
            PluginMetadata(
                name=entry_point.name,
                version=version,
            )
        )
    return plugins
