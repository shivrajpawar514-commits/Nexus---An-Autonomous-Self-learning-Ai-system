"""Planner module for goal decomposition and replanning upon step failure."""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

from agent.llm import LLMInterface


class Plan(BaseModel):
    goal: str
    subtasks: List[str] = Field(default_factory=list)
    rationale: str = ""


class Planner:
    def __init__(self, llm: LLMInterface):
        self.llm = llm

    def make_plan(
        self,
        goal: str,
        retrieved_lessons: Optional[List[str]] = None,
        retrieved_skills: Optional[List[str]] = None,
    ) -> Plan:
        """Decomposes a high-level goal into an ordered sequence of actionable subtasks."""
        lessons_context = ""
        if retrieved_lessons:
            lessons_context = "Relevant Lessons from Previous Failures/Successes:\n" + "\n".join(
                f"- {l}" for l in retrieved_lessons
            )

        skills_context = ""
        if retrieved_skills:
            skills_context = "Available Skills:\n" + "\n".join(f"- {s}" for s in retrieved_skills)

        prompt = (
            f"Goal: {goal}\n\n"
            f"{lessons_context}\n"
            f"{skills_context}\n"
            f"Break this goal into ordered, minimal subtasks required to achieve the objective."
        )

        try:
            return self.llm.generate_structured(
                prompt=prompt,
                response_model=Plan,
                system_prompt="You are an expert strategic task planner for an autonomous AI agent.",
            )
        except Exception:
            # Fallback deterministic decomposition
            return Plan(
                goal=goal,
                subtasks=[
                    f"Analyze inputs and data for: {goal}",
                    f"Execute core computational operations for: {goal}",
                    f"Verify and format result for: {goal}",
                ],
                rationale="Fallback structural plan",
            )

    def replan(
        self,
        goal: str,
        failed_subtask: str,
        error_context: str,
        lessons: Optional[List[str]] = None,
    ) -> Plan:
        """Re-plans execution when a step fails."""
        prompt = (
            f"Original Goal: {goal}\n"
            f"Failed Subtask: {failed_subtask}\n"
            f"Error / Failure Context: {error_context}\n"
            f"Produce an alternative recovery plan to overcome this roadblock."
        )
        try:
            return self.llm.generate_structured(
                prompt=prompt,
                response_model=Plan,
                system_prompt="You are an expert replanning agent specializing in error recovery.",
            )
        except Exception:
            return Plan(
                goal=goal,
                subtasks=[
                    f"Diagnose failure in: {failed_subtask}",
                    f"Execute alternative resolution for: {goal}",
                ],
                rationale="Fallback replanning sequence",
            )

