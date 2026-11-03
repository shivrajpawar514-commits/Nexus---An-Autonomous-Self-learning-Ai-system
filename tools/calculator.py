"""Safe arithmetic calculator tool."""

import math
import ast
from tools.base import tool, ToolResult, PermissionTier


class SafeMathEvaluator(ast.NodeVisitor):
    ALLOWED_NAMES = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "sqrt": math.sqrt,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
        "pow": math.pow,
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
    }

    def evaluate(self, expr_str: str) -> float:
        parsed = ast.parse(expr_str.strip(), mode="eval")
        return self.visit(parsed.body)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.Pow):
            if abs(right) > 1000:
                raise ValueError("Exponent too large")
            return left ** right
        raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    def visit_Name(self, node):
        if node.id in self.ALLOWED_NAMES:
            return self.ALLOWED_NAMES[node.id]
        raise ValueError(f"Identifier '{node.id}' is not allowed in safe math")

    def visit_Call(self, node):
        func = self.visit(node.func)
        args = [self.visit(arg) for arg in node.args]
        return func(*args)

    def generic_visit(self, node):
        raise ValueError(f"Unsupported AST node in math expression: {type(node).__name__}")


@tool(name="calculator", permission=PermissionTier.READ_ONLY, description="Evaluates mathematical expressions safely.")
def calculate(expression: str) -> ToolResult:
    """Evaluates mathematical expressions safely using an AST-limited parser."""
    try:
        evaluator = SafeMathEvaluator()
        result = evaluator.evaluate(expression)
        return ToolResult(ok=True, output=result)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

