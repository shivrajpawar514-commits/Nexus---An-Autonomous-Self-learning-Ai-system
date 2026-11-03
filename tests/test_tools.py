"""Unit and regression tests for safe tools: Calculator & Python Sandbox."""

import pytest
from tools.calculator import calculate
from tools.python_sandbox import run_python


def test_calculator_basic_and_safety():
    res = calculate("15 * 4 + 10")
    assert res.ok is True
    assert res.output == 70

    # Test unsafe input blocked
    unsafe_res = calculate("__import__('os').system('ls')")
    assert unsafe_res.ok is False
    assert "Identifier" in unsafe_res.error or "Unsupported" in unsafe_res.error


def test_calculator_advanced_functions():
    # Square root, powers, and trigonometric functions
    res = calculate("sqrt(144) + pow(2, 5) - abs(-10)")
    assert res.ok is True
    assert res.output == 12 + 32 - 10  # 34.0

    # Division by zero protection
    div_zero = calculate("100 / 0")
    assert div_zero.ok is False
    assert "Division by zero" in div_zero.error

    # Excessive exponent limit protection
    exp_overflow = calculate("2 ** 1001")
    assert exp_overflow.ok is False
    assert "Exponent too large" in exp_overflow.error


def test_python_sandbox_and_ast_block():
    # Safe computation
    safe_code = "print(sum([1, 2, 3, 4, 5]))"
    res = run_python(safe_code)
    assert res.ok is True
    assert "15" in res.output

    # Malicious subprocess / os.system attempt blocked by AST inspector
    unsafe_code = "import os\nos.system('echo hacked')"
    blocked_res = run_python(unsafe_code)
    assert blocked_res.ok is False
    assert "Safety violation" in blocked_res.error or "Blocked" in blocked_res.error


def test_python_sandbox_syntax_error():
    syntax_error_code = "def broken(:"
    res = run_python(syntax_error_code)
    assert res.ok is False
    assert "SyntaxError" in res.error
