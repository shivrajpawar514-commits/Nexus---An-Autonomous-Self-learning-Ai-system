"""Objective pass/fail verification functions for the evaluation benchmark."""

import math
from typing import Any, Callable


def exact_number_checker(expected_val: float, tolerance: float = 1e-4) -> Callable[[Any], bool]:
    def check(actual: Any) -> bool:
        try:
            # If actual is string, search for float numbers in it
            if isinstance(actual, str):
                import re
                nums = re.findall(r"[-+]?\d*\.\d+|\d+", actual)
                if not nums:
                    return False
                # Check if any extracted number matches within tolerance
                return any(math.isclose(float(n), expected_val, rel_tol=tolerance, abs_tol=tolerance) for n in nums)
            return math.isclose(float(actual), expected_val, rel_tol=tolerance, abs_tol=tolerance)
        except Exception:
            return False

    return check


def string_contains_checker(required_substring: str) -> Callable[[Any], bool]:
    def check(actual: Any) -> bool:
        return required_substring.lower() in str(actual).lower()

    return check

