"""Multi-agent voting and consensus engine for distributed decision making."""

from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class VoteType(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ABSTAIN = "ABSTAIN"


class ConsensusVote(BaseModel):
    agent_id: str
    vote: VoteType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: str = ""


class ConsensusResult(BaseModel):
    passed: bool
    approvals: int
    rejections: int
    abstentions: int
    approval_ratio: float
    weighted_approval_ratio: float
    supermajority_required: bool
    votes: List[ConsensusVote] = Field(default_factory=list)


class ConsensusEngine:
    """Calculates quorum and resolves conflicts across multi-agent votes."""

    def __init__(self, default_threshold: float = 0.5):
        self.default_threshold = default_threshold

    def evaluate(
        self,
        votes: List[ConsensusVote],
        agent_weights: Optional[Dict[str, float]] = None,
        threshold: Optional[float] = None,
        require_supermajority: bool = False,
    ) -> ConsensusResult:
        """Evaluate agent votes with reputation weights and optional supermajority requirement."""
        if not votes:
            return ConsensusResult(
                passed=False,
                approvals=0,
                rejections=0,
                abstentions=0,
                approval_ratio=0.0,
                weighted_approval_ratio=0.0,
                supermajority_required=require_supermajority,
                votes=[],
            )

        agent_weights = agent_weights or {}
        cutoff = (2.0 / 3.0) if require_supermajority else (threshold or self.default_threshold)

        approvals = 0
        rejections = 0
        abstentions = 0

        total_weight_active = 0.0
        weighted_approval_sum = 0.0

        for v in votes:
            if v.vote == VoteType.APPROVE:
                approvals += 1
            elif v.vote == VoteType.REJECT:
                rejections += 1
            elif v.vote == VoteType.ABSTAIN:
                abstentions += 1

            if v.vote != VoteType.ABSTAIN:
                weight = agent_weights.get(v.agent_id, 1.0) * max(v.confidence, 0.1)
                total_weight_active += weight
                if v.vote == VoteType.APPROVE:
                    weighted_approval_sum += weight

        active_votes = approvals + rejections
        raw_ratio = (approvals / active_votes) if active_votes > 0 else 0.0
        weighted_ratio = (weighted_approval_sum / total_weight_active) if total_weight_active > 0 else 0.0

        passed = weighted_ratio >= cutoff and approvals > rejections

        return ConsensusResult(
            passed=passed,
            approvals=approvals,
            rejections=rejections,
            abstentions=abstentions,
            approval_ratio=round(raw_ratio, 4),
            weighted_approval_ratio=round(weighted_ratio, 4),
            supermajority_required=require_supermajority,
            votes=votes,
        )
