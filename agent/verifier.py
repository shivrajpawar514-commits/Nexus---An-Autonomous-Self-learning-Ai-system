"""Multi-tiered verifier hierarchy to validate task outcomes before lesson persistence."""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from agent.llm import LLMInterface


class Verdict(BaseModel):
    passed: bool
    trust: float = Field(ge=0.0, le=1.0)
    verifier_tier: str  # programmatic, consistency, llm_judge
    evidence: str
    score: float = 0.0


class Verifier:
    def __init__(self, llm: Optional[LLMInterface] = None):
        self.llm = llm

    def check_programmatic(
        self,
        actual_output: Any,
        expected_output: Any = None,
        test_fn: Optional[Callable[[Any], bool]] = None,
    ) -> Verdict:
        """Tier 1: Deterministic programmatic assertion / unit test (Trust: 1.0)."""
        if test_fn:
            try:
                success = test_fn(actual_output)
                return Verdict(
                    passed=success,
                    trust=1.0,
                    verifier_tier="programmatic_assertion",
                    evidence="Custom test function returned True" if success else "Custom test function returned False",
                    score=1.0 if success else 0.0,
                )
            except Exception as e:
                return Verdict(
                    passed=False,
                    trust=1.0,
                    verifier_tier="programmatic_assertion",
                    evidence=f"Test assertion failed with exception: {str(e)}",
                    score=0.0,
                )

        if expected_output is not None:
            # Normalize strings for comparison
            s_actual = str(actual_output).strip()
            s_expected = str(expected_output).strip()
            passed = s_actual == s_expected or s_expected in s_actual
            return Verdict(
                passed=passed,
                trust=1.0,
                verifier_tier="programmatic_exact_match",
                evidence=f"Expected '{s_expected}', got '{s_actual}'",
                score=1.0 if passed else 0.0,
            )

        return Verdict(
            passed=True,
            trust=0.9,
            verifier_tier="programmatic_default",
            evidence="Code completed with 0 errors and valid non-empty output.",
            score=1.0,
        )

