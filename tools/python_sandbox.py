"""Sandboxed Python execution engine with AST inspection and subprocess timeout."""

import ast
import subprocess
import sys
import tempfile
from pathlib import Path
from tools.base import tool, ToolResult, PermissionTier
from tools.files import WORKSPACE_ROOT

# Restricted imports and builtins to prevent host sandbox escape
BLOCKED_MODULES = {"pty", "subprocess", "socket", "telnetlib", "posix"}
BLOCKED_CALLS = {"fork", "kill", "system", "spawn"}


class CodeSafetyInspector(ast.NodeVisitor):
    def __init__(self):
        self.violations = []

    def visit_Import(self, node):
        for alias in node.names:
            base_module = alias.name.split(".")[0]
            if base_module in BLOCKED_MODULES:
                self.violations.append(f"Blocked import: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            base_module = node.module.split(".")[0]
            if base_module in BLOCKED_MODULES:
                self.violations.append(f"Blocked import from: '{node.module}'")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_CALLS:
                self.violations.append(f"Blocked system call: '{node.func.id}'")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in BLOCKED_CALLS:
                self.violations.append(f"Blocked attribute call: '{node.func.attr}'")
        self.generic_visit(node)


@tool(name="run_python", permission=PermissionTier.WORKSPACE_WRITE, description="Executes Python code in a sandboxed runner and returns stdout/stderr.")
def run_python(code: str, timeout: int = 10) -> ToolResult:
    """Executes Python code within the sandboxed environment with static AST safety checks."""
    # 1. AST Safety check
    try:
        tree = ast.parse(code)
        inspector = CodeSafetyInspector()
        inspector.visit(tree)
        if inspector.violations:
            return ToolResult(
                ok=False,
                error=f"Safety violation(s) detected: {', '.join(inspector.violations)}",
            )
    except SyntaxError as e:
        return ToolResult(ok=False, error=f"SyntaxError: {str(e)}")

    # 2. Write to temporary script in workspace
    script_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", dir=WORKSPACE_ROOT, delete=False) as f:
            f.write(code)
            script_path = Path(f.name)

        # 3. Execute with Python subprocess
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        out = proc.stdout.strip()
        err = proc.stderr.strip()

        if proc.returncode != 0:
            return ToolResult(
                ok=False,
                output=out,
                error=f"Exit code {proc.returncode}. Stderr: {err}",
            )

        return ToolResult(
            ok=True,
            output=out if out else "[Code executed successfully with no stdout output]",
            metadata={"returncode": 0},
        )
    except subprocess.TimeoutExpired:
        return ToolResult(ok=False, error=f"Execution timed out after {timeout} seconds.")
    except Exception as e:
        return ToolResult(ok=False, error=f"Execution error: {str(e)}")
    finally:
        if script_path and script_path.exists():
            try:
                script_path.unlink()
            except Exception:
                pass

