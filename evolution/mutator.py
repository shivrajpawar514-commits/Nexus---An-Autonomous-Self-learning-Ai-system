"""Genetic prompt chromosome representation and mutation operators."""

from __future__ import annotations
import copy
import random
from typing import List, Optional
from pydantic import BaseModel, Field


class PromptChromosome(BaseModel):
    version: int = 1
    generation: int = 0
    persona: str = "You are an autonomous AI problem-solving agent running a ReAct loop."
    heuristics: List[str] = Field(default_factory=lambda: [
        "Plan before taking external tool actions.",
        "Check intermediate calculations carefully.",
        "Use finish tool immediately when the goal is satisfied.",
    ])
    constraints: List[str] = Field(default_factory=lambda: [
        "Never execute unverified shell commands without permission.",
        "Ensure all tool arguments are formatted strictly as valid JSON/kwargs.",
    ])

    def assemble_prompt(self) -> str:
        h_str = "\n".join(f"- {h}" for h in self.heuristics)
        c_str = "\n".join(f"- {c}" for c in self.constraints)
        return (
            f"{self.persona}\n\n"
            f"Core Heuristics:\n{h_str}\n\n"
            f"Strict Constraints:\n{c_str}\n"
        )


class PromptMutator:
    """Applies genetic operators to prompt chromosomes."""

    MUTATION_CANDIDATE_HEURISTICS = [
        "Synthesize tool observations concisely before formulating the next step.",
        "Prefer AST-safe calculators over executing full python scripts for pure math.",
        "If a tool call produces an error, introspect parameters instead of blindly retrying.",
        "Decompose compound questions into explicit sub-goals.",
    ]

    MUTATION_CANDIDATE_CONSTRAINTS = [
        "Verify file existence prior to attempting read operations.",
        "Bound search queries to 3-5 high-signal keywords.",
        "Never output speculative responses when exact programmatic verification is available.",
    ]

    def mutate(self, chromosome: PromptChromosome) -> PromptChromosome:
        """Create a mutated clone of the chromosome."""
        mutated = copy.deepcopy(chromosome)
        mutated.version += 1
        mutated.generation += 1

        operator = random.choice(["add_heuristic", "sharpen_constraint", "prune_heuristic", "enhance_persona"])

        if operator == "add_heuristic":
            available = [h for h in self.MUTATION_CANDIDATE_HEURISTICS if h not in mutated.heuristics]
            if available:
                mutated.heuristics.append(random.choice(available))
        elif operator == "sharpen_constraint":
            available = [c for c in self.MUTATION_CANDIDATE_CONSTRAINTS if c not in mutated.constraints]
            if available:
                mutated.constraints.append(random.choice(available))
        elif operator == "prune_heuristic" and len(mutated.heuristics) > 2:
            mutated.heuristics.pop(random.randint(0, len(mutated.heuristics) - 1))
        elif operator == "enhance_persona":
            mutated.persona += " You prioritize precision, token efficiency, and verifiable facts."

        return mutated
