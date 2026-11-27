"""Tournament engine evaluating prompt variants across Pareto fitness criteria."""

from __future__ import annotations
from typing import List, Tuple
from pydantic import BaseModel, Field
from evolution.mutator import PromptChromosome


class FitnessMetrics(BaseModel):
    accuracy: float = Field(ge=0.0, le=1.0)
    avg_tokens: int
    avg_steps: float
    composite_fitness: float


class EvolutionaryTournament:
    """Evaluates population of chromosomes and ranks them by multi-objective fitness."""

    def __init__(self, accuracy_weight: float = 0.7, token_weight: float = 0.2, step_weight: float = 0.1):
        self.accuracy_weight = accuracy_weight
        self.token_weight = token_weight
        self.step_weight = step_weight

    def calculate_fitness(self, accuracy: float, avg_tokens: int, avg_steps: float) -> FitnessMetrics:
        # Token efficiency score: 1.0 at <= 1000 tokens, tapering down
        token_score = max(0.0, min(1.0, 1.0 - (max(0, avg_tokens - 1000) / 10000.0)))
        # Step efficiency score: 1.0 at <= 3 steps, tapering down
        step_score = max(0.0, min(1.0, 1.0 - (max(0.0, avg_steps - 3.0) / 10.0)))

        composite = (
            self.accuracy_weight * accuracy
            + self.token_weight * token_score
            + self.step_weight * step_score
        )

        return FitnessMetrics(
            accuracy=round(accuracy, 4),
            avg_tokens=avg_tokens,
            avg_steps=round(avg_steps, 2),
            composite_fitness=round(composite, 4),
        )

    def rank_population(
        self,
        candidates: List[Tuple[PromptChromosome, FitnessMetrics]],
    ) -> List[Tuple[PromptChromosome, FitnessMetrics]]:
        """Sort candidates by composite fitness descending."""
        return sorted(candidates, key=lambda x: x[1].composite_fitness, reverse=True)
