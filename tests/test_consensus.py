"""Unit tests for multi-agent consensus engine and debate coordinator."""

import pytest
from agent.consensus import ConsensusEngine, ConsensusVote, VoteType
from agent.debate import DebateCoordinator
from agent.llm import MockLLM


def test_consensus_simple_majority():
    engine = ConsensusEngine()
    votes = [
        ConsensusVote(agent_id="agent_1", vote=VoteType.APPROVE, confidence=1.0),
        ConsensusVote(agent_id="agent_2", vote=VoteType.APPROVE, confidence=0.8),
        ConsensusVote(agent_id="agent_3", vote=VoteType.REJECT, confidence=0.9),
    ]
    res = engine.evaluate(votes)
    assert res.passed is True
    assert res.approvals == 2
    assert res.rejections == 1
    assert res.approval_ratio == round(2 / 3, 4)


def test_consensus_supermajority_requirement():
    engine = ConsensusEngine()
    # 2 approves, 1 reject = 66.67%
    votes = [
        ConsensusVote(agent_id="a1", vote=VoteType.APPROVE, confidence=1.0),
        ConsensusVote(agent_id="a2", vote=VoteType.APPROVE, confidence=1.0),
        ConsensusVote(agent_id="a3", vote=VoteType.REJECT, confidence=1.0),
    ]
    # Simple majority passes
    res_simple = engine.evaluate(votes, require_supermajority=False)
    assert res_simple.passed is True

    # 1 approve, 1 reject: 50% fails supermajority
    votes_split = [
        ConsensusVote(agent_id="a1", vote=VoteType.APPROVE, confidence=1.0),
        ConsensusVote(agent_id="a2", vote=VoteType.REJECT, confidence=1.0),
    ]
    res_split = engine.evaluate(votes_split, require_supermajority=True)
    assert res_split.passed is False


def test_consensus_weighted_reputation_swing():
    engine = ConsensusEngine()
    # 2 junior agents reject, but 1 senior high-reputation agent approves
    votes = [
        ConsensusVote(agent_id="senior", vote=VoteType.APPROVE, confidence=1.0),
        ConsensusVote(agent_id="junior_1", vote=VoteType.REJECT, confidence=0.5),
        ConsensusVote(agent_id="junior_2", vote=VoteType.REJECT, confidence=0.5),
    ]
    weights = {"senior": 5.0, "junior_1": 1.0, "junior_2": 1.0}
    # Weighted approval: senior=5.0, junior_1=0.5, junior_2=0.5 -> 5.0 / 6.0 = 83.3%
    # However approvals (1) < rejections (2), so passed is False when raw count check is applied
    res = engine.evaluate(votes, agent_weights=weights)
    assert res.weighted_approval_ratio > 0.8
    assert res.passed is False  # Must also have approvals > rejections


def test_debate_coordinator():
    llm = MockLLM()
    coordinator = DebateCoordinator(llm=llm)
    res = coordinator.coordinate_debate(
        topic="Refactor database connection pool",
        initial_proposal="Create 50 connections upfront",
        max_rounds=2,
    )
    assert res.topic == "Refactor database connection pool"
    assert len(res.rounds) > 0
    assert res.final_proposal is not None
