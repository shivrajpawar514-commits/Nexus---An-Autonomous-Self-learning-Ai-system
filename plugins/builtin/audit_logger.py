"""Built-in compliance and security audit logging plugin."""

from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Tuple
from plugins.base import PluginInterface, PluginManifest, PluginContext


class AuditEntry:
    def __init__(self, action_name: str, args: Dict[str, Any], result_str: str, duration_sec: float):
        self.timestamp = time.time()
        self.action_name = action_name
        self.args = args
        self.result_str = result_str
        self.duration_sec = duration_sec

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action_name": self.action_name,
            "args": self.args,
            "result_str": self.result_str[:120],
            "duration_sec": round(self.duration_sec, 4),
        }


class AuditLoggerPlugin(PluginInterface):
    """Logs tool execution requests and results for enterprise compliance."""

    def __init__(self, max_entries: int = 500):
        manifest = PluginManifest(
            name="audit_logger",
            version="1.0.0",
            description="Compliance and security audit trail for all agent tool executions",
            author="Nexus Core Team",
            hooks=["on_pre_execute", "on_post_execute"],
        )
        super().__init__(manifest)
        self.max_entries = max_entries
        self.entries: List[AuditEntry] = []

    def on_load(self, context: PluginContext) -> None:
        self.entries.clear()

    def on_post_execute(
        self,
        action_name: str,
        args: Dict[str, Any],
        result: Any,
        duration_sec: float,
    ) -> None:
        entry = AuditEntry(action_name, args, str(result), duration_sec)
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)

    def get_entries(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.entries]
