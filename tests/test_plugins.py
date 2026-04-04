"""Tests for vcsx plugin system."""

import pytest

from vcsx.plugins import (
    Plugin,
    PluginMetadata,
    PluginRegistry,
    discover_plugins,
    get_registry,
    load_default_plugins,
)


# --- Fixtures / helpers ---


class ConcretePlugin(Plugin):
    """Minimal concrete plugin for testing."""

    def __init__(self, name: str = "test-plugin"):
        super().__init__()
        self._name = name
        self.registered = False
        self.unregistered = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self._name,
            version="1.2.3",
            author="Tester",
            description="A test plugin",
            keywords=["test"],
            home_url="https://example.com",
            repo_url="https://github.com/example/test",
        )

    def register(self, registry: PluginRegistry) -> None:
        self.registered = True

    def unregister(self, registry: PluginRegistry) -> None:
        self.unregistered = True


# --- PluginMetadata ---


class TestPluginMetadata:
    def test_defaults(self):
        meta = PluginMetadata(name="foo")
        assert meta.name == "foo"
        assert meta.version == "1.0.0"
        assert meta.author == ""
        assert meta.description == ""
        assert meta.keywords == []
        assert meta.home_url == ""
        assert meta.repo_url == ""

    def test_custom_values(self):
        meta = PluginMetadata(
            name="bar",
            version="2.0.0",
            author="Baran",
            description="Cool plugin",
            keywords=["cool", "plugin"],
            home_url="https://bar.dev",
            repo_url="https://github.com/bar/bar",
        )
        assert meta.version == "2.0.0"
        assert meta.author == "Baran"
        assert meta.keywords == ["cool", "plugin"]


# --- Plugin base ---


class TestPlugin:
    def test_initial_state(self):
        p = ConcretePlugin()
        assert not p.is_enabled

    def test_enable_disable(self):
        p = ConcretePlugin()
        p.enable()
        assert p.is_enabled
        p.disable()
        assert not p.is_enabled

    def test_name(self):
        p = ConcretePlugin("my-plugin")
        assert p.name == "my-plugin"

    def test_metadata(self):
        p = ConcretePlugin()
        assert p.metadata.version == "1.2.3"
        assert p.metadata.author == "Tester"

    def test_register_called(self):
        p = ConcretePlugin()
        registry = PluginRegistry()
        registry.register(p)
        assert p.registered

    def test_unregister_called(self):
        p = ConcretePlugin()
        registry = PluginRegistry()
        registry.register(p)
        registry.unregister(p.name)
        assert p.unregistered


# --- PluginRegistry ---


class TestPluginRegistry:
    def test_register_and_get(self):
        registry = PluginRegistry()
        p = ConcretePlugin("alpha")
        registry.register(p)
        assert registry.get("alpha") is p

    def test_get_missing_returns_none(self):
        registry = PluginRegistry()
        assert registry.get("nonexistent") is None

    def test_duplicate_registration_raises(self):
        registry = PluginRegistry()
        registry.register(ConcretePlugin("dupe"))
        with pytest.raises(ValueError, match="already registered"):
            registry.register(ConcretePlugin("dupe"))

    def test_list_all(self):
        registry = PluginRegistry()
        registry.register(ConcretePlugin("a"))
        registry.register(ConcretePlugin("b"))
        names = [p.name for p in registry.list_all()]
        assert "a" in names
        assert "b" in names

    def test_list_enabled(self):
        registry = PluginRegistry()
        p1 = ConcretePlugin("enabled")
        p2 = ConcretePlugin("disabled")
        registry.register(p1)
        registry.register(p2)
        p2.disable()
        enabled = registry.list_enabled()
        assert p1 in enabled
        assert p2 not in enabled

    def test_unregister_removes_plugin(self):
        registry = PluginRegistry()
        registry.register(ConcretePlugin("removeme"))
        registry.unregister("removeme")
        assert registry.get("removeme") is None

    def test_unregister_nonexistent_is_noop(self):
        registry = PluginRegistry()
        registry.unregister("ghost")  # should not raise

    def test_plugin_enabled_after_register(self):
        registry = PluginRegistry()
        p = ConcretePlugin("auto-enable")
        registry.register(p)
        assert p.is_enabled


# --- Hooks ---


class TestHooks:
    def test_add_and_trigger_hook(self):
        registry = PluginRegistry()
        results = []
        registry.add_hook("build", lambda x: results.append(x))
        registry.trigger("build", "payload")
        assert results == ["payload"]

    def test_trigger_returns_results(self):
        registry = PluginRegistry()
        registry.add_hook("event", lambda: 42)
        out = registry.trigger("event")
        assert out == [42]

    def test_trigger_no_hooks_returns_empty(self):
        registry = PluginRegistry()
        assert registry.trigger("no-such-event") == []

    def test_multiple_hooks_same_event(self):
        registry = PluginRegistry()
        calls = []
        registry.add_hook("evt", lambda: calls.append(1))
        registry.add_hook("evt", lambda: calls.append(2))
        registry.trigger("evt")
        assert calls == [1, 2]

    def test_remove_hook(self):
        registry = PluginRegistry()
        calls = []
        cb = lambda: calls.append("x")  # noqa: E731
        registry.add_hook("evt", cb)
        registry.remove_hook("evt", cb)
        registry.trigger("evt")
        assert calls == []

    def test_remove_hook_nonexistent_event_is_noop(self):
        registry = PluginRegistry()
        registry.remove_hook("ghost", lambda: None)  # should not raise

    def test_hook_with_kwargs(self):
        registry = PluginRegistry()
        received = {}
        registry.add_hook("kw", lambda **kw: received.update(kw))
        registry.trigger("kw", key="value")
        assert received == {"key": "value"}


# --- Global registry ---


class TestGlobalRegistry:
    def test_get_registry_returns_same_instance(self):
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2

    def test_get_registry_is_plugin_registry(self):
        assert isinstance(get_registry(), PluginRegistry)


# --- load_default_plugins ---


class TestLoadDefaultPlugins:
    def test_runs_without_error(self):
        load_default_plugins()  # should not raise


# --- discover_plugins ---


class TestDiscoverPlugins:
    def test_returns_list(self):
        result = discover_plugins()
        assert isinstance(result, list)

    def test_items_are_plugin_metadata(self):
        result = discover_plugins()
        for item in result:
            assert isinstance(item, PluginMetadata)
