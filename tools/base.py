"""Base classes and decorators for typed, sandboxed agent tools."""

from __future__ import annotations
import inspect
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class PermissionTier(str, Enum):
    READ_ONLY = "read_only"
    WORKSPACE_WRITE = "workspace_write"
    ELEVATED_RISK = "elevated_risk"


class ToolResult(BaseModel):
    ok: bool = True
    output: Any = None
    error: Optional[str] = None
    cost_tokens: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_observation_str(self) -> str:
        if self.ok:
            return str(self.output)
        return f"Error: {self.error}"


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        permission: PermissionTier = PermissionTier.READ_ONLY,
        parameters_schema: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.permission = permission
        self.parameters_schema = parameters_schema or self._generate_schema()

    def _generate_schema(self) -> Dict[str, Any]:
        sig = inspect.signature(self.func)
        properties = {}
        required = []
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue
            param_type = "string"
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == dict:
                param_type = "object"
            elif param.annotation == list:
                param_type = "array"

            properties[param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}",
            }
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def execute(self, **kwargs) -> ToolResult:
        try:
            res = self.func(**kwargs)
            if isinstance(res, ToolResult):
                return res
            return ToolResult(ok=True, output=res)
        except Exception as e:
            return ToolResult(ok=False, error=f"{type(e).__name__}: {str(e)}")


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "permission": t.permission.value,
                "parameters": t.parameters_schema,
            }
            for t in self._tools.values()
        ]

    def execute(self, name: str, **kwargs) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(ok=False, error=f"Tool '{name}' not found.")
        return tool.execute(**kwargs)


_DEFAULT_REGISTRY = ToolRegistry()


def tool(
    name: Optional[str] = None,
    permission: PermissionTier = PermissionTier.READ_ONLY,
    description: Optional[str] = None,
    registry: Optional[ToolRegistry] = None,
):
    """Decorator to register functions as tools."""
    target_registry = registry or _DEFAULT_REGISTRY

    def decorator(fn: Callable[..., Any]):
        tool_name = name or fn.__name__
        tool_desc = description or (fn.__doc__.strip() if fn.__doc__ else f"Executes {tool_name}")
        t = Tool(
            name=tool_name,
            description=tool_desc,
            func=fn,
            permission=permission,
        )
        target_registry.register(t)
        return fn

    return decorator


def get_default_registry() -> ToolRegistry:
    return _DEFAULT_REGISTRY

