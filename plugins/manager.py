"""Plugin lifecycle manager for dynamic hot-reloading and hook dispatch."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from plugins.base import PluginInterface, PluginContext, PluginManifest
from tools.base import ToolRegistry


class PluginManager:
    """Manages plugin discovery, lifecycle hooks, and hot reload."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None, config: Optional[Dict[str, Any]] = None):
        self.tool_registry = tool_registry
        self.config = config or {}
        self.context = PluginContext(tool_registry=self.tool_registry, config=self.config)
        self._plugins: Dict[str, PluginInterface] = {}

    def register(self, plugin: PluginInterface) -> None:
        """Register and initialize a plugin."""
        name = plugin.name
        self._plugins[name] = plugin
        plugin.on_load(self.context)

    def unregister(self, name: str) -> bool:
        """Unload and remove a plugin."""
        if name in self._plugins:
            plugin = self._plugins[name]
            plugin.on_unload(self.context)
            del self._plugins[name]
            return True
        return False

    def enable(self, name: str) -> bool:
        if name in self._plugins:
            self._plugins[name].enable()
            return True
        return False

    def disable(self, name: str) -> bool:
        if name in self._plugins:
            self._plugins[name].disable()
            return True
        return False

    def reload(self, name: str) -> bool:
        """Hot-reload an active plugin without restarting the agent."""
        if name in self._plugins:
            plugin = self._plugins[name]
            plugin.on_unload(self.context)
            plugin.on_load(self.context)
            return True
        return False

    def trigger_pre_execute(self, action_name: str, args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Dispatch pre-execute hooks. If any enabled plugin vetos, execution is blocked."""
        for plugin in self._plugins.values():
            if plugin.is_enabled:
                allowed, reason = plugin.on_pre_execute(action_name, args)
                if not allowed:
                    return False, f"Blocked by plugin '{plugin.name}': {reason}"
        return True, None

    def trigger_post_execute(
        self,
        action_name: str,
        args: Dict[str, Any],
        result: Any,
        duration_sec: float,
    ) -> None:
        """Dispatch post-execute hooks across all enabled plugins."""
        for plugin in self._plugins.values():
            if plugin.is_enabled:
                try:
                    plugin.on_post_execute(action_name, args, result, duration_sec)
                except Exception:
                    pass

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Return status and manifests of all registered plugins."""
        return [
            {
                "name": p.name,
                "version": p.manifest.version,
                "description": p.manifest.description,
                "author": p.manifest.author,
                "enabled": p.is_enabled,
                "hooks": p.manifest.hooks,
            }
            for p in self._plugins.values()
        ]

    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        return self._plugins.get(name)
