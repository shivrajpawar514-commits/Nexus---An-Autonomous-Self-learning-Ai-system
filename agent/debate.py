"""Multi-agent debate and reflexive refinement coordinator."""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from agent.llm import LLMInterface


class DebateRound(BaseModel):
    round_number: int
    proposal: str
    critique: str
    revised_proposal: str


class DebateResult(BaseModel):
    topic: str
    final_proposal: str
    converged: bool
    rounds: List[DebateRound] = Field(default_factory=list)
    total_rounds: int = 0


class DebateCoordinator:
    """Coordinates iterative debate between Proposer and Critic agent personas."""

    def __init__(self, llm: LLMInterface):
        self.llm = llm

    def coordinate_debate(
        self,
        topic: str,
        initial_proposal: str,
        max_rounds: int = 3,
        convergence_similarity: float = 0.9,
    ) -> DebateResult:
        """Runs iterative Proposer vs. Critic debate rounds until consensus or max rounds reached."""
        current_proposal = initial_proposal
        rounds: List[DebateRound] = []
        converged = False

        for r in range(1, max_rounds + 1):
            # Critic phase
            critic_prompt = (
                f"You are a rigorous code & safety critic. Analyze this proposal for topic: '{topic}'.\n"
                f"Proposal: {current_proposal}\n"
                f"Point out potential edge-case failures, safety risks, or algorithmic flaws. Be concise."
            )
            critic_res = self.llm.generate(critic_prompt)
            critique = critic_res.content if hasattr(critic_res, "content") else str(critic_res)

            # Check if critic raises no serious flaws
            if "no flaws" in critique.lower() or "looks good" in critique.lower() or "acceptable" in critique.lower():
                rounds.append(
                    DebateRound(
                        round_number=r,
                        proposal=current_proposal,
                        critique=critique,
                        revised_proposal=current_proposal,
                    )
                )
                converged = True
                break

            # Proposer revision phase
            proposer_prompt = (
                f"You are the solution designer. Incorporate the following critique into an improved proposal.\n"
                f"Topic: {topic}\n"
                f"Previous Proposal: {current_proposal}\n"
                f"Critique: {critique}\n"
                f"Output the revised proposal addressing the points."
            )
            proposer_res = self.llm.generate(proposer_prompt)
            revised = proposer_res.content if hasattr(proposer_res, "content") else str(proposer_res)

            rounds.append(
                DebateRound(
                    round_number=r,
                    proposal=current_proposal,
                    critique=critique,
                    revised_proposal=revised,
                )
            )

            # Check convergence
            if revised.strip() == current_proposal.strip():
                converged = True
                break

            current_proposal = revised

        return DebateResult(
            topic=topic,
            final_proposal=current_proposal,
            converged=converged,
            rounds=rounds,
            total_rounds=len(rounds),
        )
