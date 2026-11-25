"""Deadlock and reasoning loop detector for autonomous agents."""

from __future__ import annotations
import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DeadlockType(str, Enum):
    NONE = "NONE"
    IDENTICAL_ACTION_LOOP = "IDENTICAL_ACTION_LOOP"
    CYCLIC_OBSERVATION_LOOP = "CYCLIC_OBSERVATION_LOOP"


class DeadlockIntervention(BaseModel):
    detected: bool
    deadlock_type: DeadlockType = DeadlockType.NONE
    message: str = ""
    suggested_strategy: str = ""
    intervention_prompt: str = ""


class DeadlockDetector:
    """Analyzes recent ReAct trajectory steps to catch infinite repetition loops early."""

    def __init__(self, repetition_threshold: int = 3):
        self.repetition_threshold = repetition_threshold

    @staticmethod
    def _hash_action(action_name: Optional[str], action_args: Dict[str, Any]) -> str:
        s = f"{action_name}:{json.dumps(action_args, sort_keys=True)}"
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    def analyze(self, trajectory: List[Any]) -> DeadlockIntervention:
        """Inspects the last N steps in the trajectory for pathological repeating patterns."""
        if len(trajectory) < self.repetition_threshold:
            return DeadlockIntervention(detected=False)

        recent_steps = trajectory[-self.repetition_threshold :]

        # 1. Check for identical action + argument repetition
        action_hashes = [
            self._hash_action(s.action_name, getattr(s, "action_args", {}))
            for s in recent_steps
        ]
        if len(set(action_hashes)) == 1 and recent_steps[0].action_name not in ["finish", None]:
            tool_name = recent_steps[0].action_name
            return DeadlockIntervention(
                detected=True,
                deadlock_type=DeadlockType.IDENTICAL_ACTION_LOOP,
                message=f"Agent stuck calling '{tool_name}' {self.repetition_threshold} times consecutively with identical parameters.",
                suggested_strategy="MUTATE_APPROACH",
                intervention_prompt=(
                    f"CRITICAL SYSTEM INTERVENTION: You have called '{tool_name}' {self.repetition_threshold} times in a row with the exact same inputs without making progress. "
                    "DO NOT repeat this action again. Formulate an alternate plan, synthesize existing data, or use 'finish' to state current findings."
                ),
            )

        # 2. Check for identical observation error loops
        obs_list = [getattr(s, "observation", "") for s in recent_steps]
        if len(set(obs_list)) == 1 and "error" in obs_list[0].lower():
            return DeadlockIntervention(
                detected=True,
                deadlock_type=DeadlockType.CYCLIC_OBSERVATION_LOOP,
                message="Agent received the identical error observation repeatedly across multiple attempts.",
                suggested_strategy="FALLBACK_REPLAN",
                intervention_prompt=(
                    f"SYSTEM WARNING: The last {self.repetition_threshold} actions all failed with the same error. "
                    "You must switch to an alternative tool or report inability to proceed directly."
                ),
            )

        return DeadlockIntervention(detected=False)
