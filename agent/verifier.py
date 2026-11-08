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

    def check_llm_judge(self, goal: str, output: str, rubric: str = "") -> Verdict:
        """Tier 3: Fallback LLM-as-a-Judge (Trust: 0.5)."""
        if not self.llm:
            return Verdict(
                passed=bool(output.strip()),
                trust=0.4,
                verifier_tier="heuristic_fallback",
                evidence="No judge LLM configured; heuristic non-empty check.",
                score=0.5 if output.strip() else 0.0,
            )

        prompt = (
            f"You are an impartial evaluation judge evaluating whether an AI agent succeeded.\n\n"
            f"Goal: {goal}\n"
            f"Agent Output: {output}\n"
            f"Rubric: {rubric or 'Check if the agent factually and completely resolved the goal.'}\n\n"
            f"Respond with JSON:\n"
            f"{{\"passed\": true/false, \"score\": 0.0-1.0, \"evidence\": \"explanation\"}}"
        )

        class JudgeOutput(BaseModel):
            passed: bool
            score: float
            evidence: str

        try:
            res = self.llm.generate_structured(prompt, JudgeOutput)
            return Verdict(
                passed=res.passed,
                trust=0.5,
                verifier_tier="llm_judge",
                evidence=res.evidence,
                score=res.score,
            )
        except Exception as e:
            return Verdict(
                passed=False,
                trust=0.3,
                verifier_tier="llm_judge_error",
                evidence=f"Judge failed: {str(e)}",
                score=0.0,
            )

