"""Safe file system access within a designated sandboxed workspace."""

import os
from pathlib import Path
from tools.base import tool, ToolResult, PermissionTier

WORKSPACE_ROOT = (Path(__file__).resolve().parent.parent / "sandbox_workspace").resolve()
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)


def _resolve_safe_path(rel_path: str) -> Path:
    target = (WORKSPACE_ROOT / rel_path).resolve()
    if not str(target).startswith(str(WORKSPACE_ROOT)):
        raise PermissionError(f"Access denied: Path '{rel_path}' escapes sandbox boundary.")
    return target


@tool(name="read_file", permission=PermissionTier.READ_ONLY, description="Reads contents of a file within the workspace.")
def read_file(path: str) -> ToolResult:
    """Reads a text file inside the workspace."""
    try:
        target = _resolve_safe_path(path)
        if not target.exists():
            return ToolResult(ok=False, error=f"File not found: {path}")
        if not target.is_file():
            return ToolResult(ok=False, error=f"Target is not a file: {path}")
        content = target.read_text(encoding="utf-8")
        return ToolResult(ok=True, output=content)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(name="write_file", permission=PermissionTier.WORKSPACE_WRITE, description="Writes text content to a file within the workspace.")
def write_file(path: str, content: str) -> ToolResult:
    """Writes content to a file inside the workspace."""
    try:
        target = _resolve_safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return ToolResult(ok=True, output=f"Successfully wrote {len(content)} characters to {path}")
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(name="list_files", permission=PermissionTier.READ_ONLY, description="Lists files and directories in the workspace.")
def list_files(directory: str = "") -> ToolResult:
    """Lists entries in a directory relative to workspace root."""
    try:
        target = _resolve_safe_path(directory)
        if not target.exists():
            return ToolResult(ok=False, error=f"Directory not found: {directory}")
        entries = [p.name for p in target.iterdir()]
        return ToolResult(ok=True, output=entries)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

