"""Unit and regression tests for Voyager Skill Library, self-verification, and live promotion."""

import pytest
from memory.skills import SkillLibrary, SkillEntry
from tools.base import ToolRegistry


def test_skill_library_verification_and_promotion():
    registry = ToolRegistry()
    lib = SkillLibrary(tool_registry=registry)

    code = "def fibonacci(n: int) -> int:\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a"
    test_code = "assert fibonacci(0) == 0\nassert fibonacci(6) == 8"

    entry = lib.add_skill(
        name="fibonacci",
        description="Compute the nth Fibonacci number",
        code=code,
        test_code=test_code,
    )
    assert entry.is_verified is False

    # Verify and promote into live ToolRegistry
    promoted = lib.verify_and_promote("fibonacci")
    assert promoted is True
    assert lib.skills["fibonacci"].is_verified is True

    # Ensure dynamic tool is executable through registry
    tool = registry.get("fibonacci")
    assert tool is not None
    res = registry.execute("fibonacci", n=10)
    assert res.ok is True
    assert res.output == 55


def test_skill_library_rejects_failing_tests():
    registry = ToolRegistry()
    lib = SkillLibrary(tool_registry=registry)

    buggy_code = "def add_two(x: int) -> int:\n    return x + 1"
    test_code = "assert add_two(3) == 5"

    lib.add_skill(
        name="add_two",
        description="Adds 2 to integer",
        code=buggy_code,
        test_code=test_code,
    )

    promoted = lib.verify_and_promote("add_two")
    assert promoted is False
    assert lib.skills["add_two"].is_verified is False
    assert registry.get("add_two") is None


def test_skill_library_auto_promotion_and_retrieval():
    registry = ToolRegistry()
    lib = SkillLibrary(tool_registry=registry)

    lib.add_skill(
        name="square_val",
        description="Squares a numeric value",
        code="def square_val(x: float) -> float:\n    return x * x",
        test_code="assert square_val(4) == 16",
    )

    # First success does not promote yet; second success triggers auto-promotion
    lib.record_usage("square_val", success=True)
    assert lib.skills["square_val"].is_verified is False

    lib.record_usage("square_val", success=True)
    assert lib.skills["square_val"].is_verified is True
    assert registry.get("square_val") is not None

    # Retrieval prioritizes verified matching skills
    matches = lib.retrieve_skills("square numeric value", k=1)
    assert len(matches) == 1
    assert matches[0].name == "square_val"
