"""Context condensation engine for long-running multi-turn agent dialogues."""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel

from agent.llm import LLMInterface
from agent.executor import ReActStep


class SummaryResult(BaseModel):
    summary: str
    tokens_saved: int = 0
    preserved_facts: List[str] = []


class ContextSummarizer:
    """Summarizes conversational trajectories and observations to stay within context budgets."""

    def __init__(self, llm: LLMInterface, token_threshold: int = 4000):
        self.llm = llm
        self.token_threshold = token_threshold

    def condense_trajectory(self, trajectory: List[ReActStep]) -> str:
        """Condenses an execution trace into an information-dense markdown summary."""
        if not trajectory:
            return "No previous steps executed."

        lines = ["### Execution Summary:"]
        for step in trajectory:
            status = "Completed" if step.action_name == "finish" else "Executed"
            obs_preview = (step.observation[:80] + "...") if step.observation and len(step.observation) > 80 else step.observation
            lines.append(f"- Step {step.step_index}: {step.thought} -> {status} `{step.action_name}` with obs: {obs_preview}")

        return "\n".join(lines)

    def summarize_context(self, full_dialogue: str) -> str:
        """Generates an LLM-backed summary preserving key constraints and intermediate values."""
        if len(full_dialogue.split()) < self.token_threshold:
            return full_dialogue

        prompt = (
            f"Condense the following multi-turn execution trace while preserving all computed numbers, "
            f"variable assignments, and explicit constraint rules:\n\n{full_dialogue}\n\nSummary:"
        )
        resp = self.llm.generate(prompt)
        return resp.content.strip()
