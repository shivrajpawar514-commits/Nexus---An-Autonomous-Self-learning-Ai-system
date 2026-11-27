"""Prompt strategy manager with rollback checkpoints and promotion safeguards."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from evolution.mutator import PromptChromosome, PromptMutator
from evolution.tournament import FitnessMetrics


class StrategyManager:
    """Maintains active prompt chromosome, history checkpoints, and rollback controls."""

    def __init__(self, initial_chromosome: Optional[PromptChromosome] = None):
        self.active_chromosome = initial_chromosome or PromptChromosome()
        self.history: List[PromptChromosome] = [self.active_chromosome]
        self.metrics_history: List[Dict[str, Any]] = []
        self.mutator = PromptMutator()

    def promote_variant(self, candidate: PromptChromosome, metrics: Optional[FitnessMetrics] = None) -> None:
        """Promote a mutated candidate to active system chromosome."""
        self.history.append(self.active_chromosome)
        self.active_chromosome = candidate
        if metrics:
            self.metrics_history.append({
                "version": candidate.version,
                "generation": candidate.generation,
                "fitness": metrics.model_dump(),
            })

    def rollback(self) -> Optional[PromptChromosome]:
        """Roll back to previous active chromosome checkpoint."""
        if len(self.history) > 1:
            prev = self.history.pop()
            self.active_chromosome = prev
            return prev
        return None

    def get_status(self) -> Dict[str, Any]:
        return {
            "current_version": self.active_chromosome.version,
            "current_generation": self.active_chromosome.generation,
            "heuristics_count": len(self.active_chromosome.heuristics),
            "constraints_count": len(self.active_chromosome.constraints),
            "checkpoints_count": len(self.history),
            "active_prompt_preview": self.active_chromosome.assemble_prompt()[:200] + "...",
        }
