"""Base classes and interfaces for Nexus autonomous agent plugins."""

from __future__ import annotations
import abc
import time
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from tools.base import ToolRegistry


class PluginManifest(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = "Nexus Community"
    enabled: bool = True
    hooks: List[str] = Field(default_factory=list)


class PluginContext(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    tool_registry: Optional[ToolRegistry] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class PluginInterface(abc.ABC):
    """Abstract base class that all Nexus plugins must implement."""

    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest
        self._enabled = manifest.enabled

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def on_load(self, context: PluginContext) -> None:
        """Called when plugin is loaded into the plugin manager."""
        pass

    def on_unload(self, context: PluginContext) -> None:
        """Called when plugin is unloaded or uninstalled."""
        pass

    def on_pre_execute(self, action_name: str, args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Hook called before a tool executes. Return (True, None) to allow, or (False, reason) to block."""
        return True, None

    def on_post_execute(
        self,
        action_name: str,
        args: Dict[str, Any],
        result: Any,
        duration_sec: float,
    ) -> None:
        """Hook called immediately after a tool finishes execution."""
        pass
