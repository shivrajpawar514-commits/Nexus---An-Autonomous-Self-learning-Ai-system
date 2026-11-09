"""Reflection engine producing structured, actionable rules from task trajectories."""

from __future__ import annotations
import json
from typing import List, Optional
from pydantic import BaseModel, Field

from agent.llm import LLMInterface
from agent.verifier import Verdict


class StructuredLesson(BaseModel):
    situation: str = Field(description="Context and condition when this lesson applies")
    what_happened: str = Field(description="Objective summary of what occurred")
    root_cause: str = Field(description="Root cause of the failure or inefficiency")
    rule: str = Field(description="Concise, actionable rule/heuristic to apply next time")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    trust_weight: float = 1.0


class ReflectionResult(BaseModel):
    goal: str
    passed: bool
    lessons: List[StructuredLesson] = Field(default_factory=list)
    summary: str = ""


class Reflector:
    def __init__(self, llm: LLMInterface):
        self.llm = llm

    def reflect(
        self,
        goal: str,
        trajectory_str: str,
        verdict: Verdict,
    ) -> ReflectionResult:
        """Analyzes a completed task trajectory and generates structured lessons."""
        outcome_str = f"Outcome: {'PASSED' if verdict.passed else 'FAILED'} (Verifier: {verdict.verifier_tier})\nEvidence: {verdict.evidence}"

        prompt = (
            f"You are reviewing a finished autonomous task execution to extract actionable heuristics.\n\n"
            f"Goal: {goal}\n"
            f"Execution Trajectory:\n{trajectory_str}\n\n"
            f"{outcome_str}\n\n"
            f"Formulate a structured lesson to improve future performance.\n"
            f"If it failed, identify the root cause and a preventive rule.\n"
            f"If it succeeded, identify what pattern made it fast, reliable, or optimal."
        )

        class LessonContainer(BaseModel):
            lessons: List[StructuredLesson]
            summary: str

        try:
            container = self.llm.generate_structured(
                prompt=prompt,
                response_model=LessonContainer,
                system_prompt="You are an expert post-mortem reflection and verbal reinforcement learning engine.",
            )
            # Weight confidence by verifier trust
            for l in container.lessons:
                l.trust_weight = round(l.confidence * verdict.trust, 3)

            return ReflectionResult(
                goal=goal,
                passed=verdict.passed,
                lessons=container.lessons,
                summary=container.summary,
            )
        except Exception:
            # Fallback deterministic reflection
            fallback_rule = (
                "Verify variable bounds and check data shapes before running numerical operations."
                if not verdict.passed
                else "Decompose complex multi-step arithmetic into verified sandboxed functions."
            )
            return ReflectionResult(
                goal=goal,
                passed=verdict.passed,
                lessons=[
                    StructuredLesson(
                        situation=f"Tasks involving: {goal[:40]}...",
                        what_happened=f"Task {'passed' if verdict.passed else 'failed'} with verdict evidence: {verdict.evidence}",
                        root_cause="Execution trace variance",
                        rule=fallback_rule,
                        confidence=0.85,
                        trust_weight=round(0.85 * verdict.trust, 3),
                    )
                ],
                summary="Fallback heuristic reflection.",
            )

