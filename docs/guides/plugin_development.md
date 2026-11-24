# Nexus Plugin Developer Guide

## Overview
Nexus provides a hot-reloadable, sandboxed plugin system allowing developers and enterprise teams to extend agent capabilities without modifying core system logic.

## Lifecycle Hooks
Plugins can intercept and observe execution at multiple lifecycle stages:

| Hook | Signature | Purpose |
|---|---|---|
| `on_load` | `(context: PluginContext) -> None` | Initialize dependencies, load configs, register tools |
| `on_unload` | `(context: PluginContext) -> None` | Cleanup resources, flush buffers, deregister tools |
| `on_pre_execute` | `(action_name: str, args: dict) -> (bool, str?)` | Veto or validate actions before tool invocation |
| `on_post_execute` | `(action_name: str, args: dict, result: Any, duration: float)` | Audit logging, metric tracking, state updates |

## Example: Authoring a Rate Limiting Plugin
```python
from plugins.base import PluginInterface, PluginManifest
import time

class RateLimiterPlugin(PluginInterface):
    def __init__(self, max_per_minute: int = 30):
        manifest = PluginManifest(
            name="rate_limiter",
            version="1.0.0",
            description="Enforces per-minute tool execution velocity bounds",
        )
        super().__init__(manifest)
        self.max_per_minute = max_per_minute
        self.call_timestamps = []

    def on_pre_execute(self, action_name: str, args: dict):
        now = time.time()
        self.call_timestamps = [t for t in self.call_timestamps if now - t < 60.0]
        if len(self.call_timestamps) >= self.max_per_minute:
            return False, f"Rate limit exceeded ({self.max_per_minute} calls/min)"
        self.call_timestamps.append(now)
        return True, None
```

## Management via REST API
- `GET /api/plugins`: List all installed plugins and their active states.
- `POST /api/plugins/toggle`: Enable or disable a plugin dynamically (`{"name": "...", "enabled": true/false}`).
- `POST /api/plugins/reload`: Hot-reload plugin state without restarting the daemon (`{"name": "..."}`).
