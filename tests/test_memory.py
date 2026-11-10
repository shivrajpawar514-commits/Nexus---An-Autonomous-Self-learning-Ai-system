"""Unit and regression tests for Episodic and Semantic Memory subsystems."""

import os
import pytest
from pathlib import Path
from memory.episodic import EpisodicMemory, EpisodeRecord
from memory.semantic import SemanticMemory, MemoryItem
from agent.reflector import StructuredLesson


def test_episodic_memory_storage_and_retrieval(tmp_path):
    db_file = tmp_path / "test_episodes.db"
    mem = EpisodicMemory(db_path=db_file)

    ep_id = mem.record_episode(
        goal="Calculate 15 * 4 + 10",
        plan={"subtasks": ["compute"]},
        trajectory=[{"step": 1, "action": "calculator"}],
        passed=True,
        score=1.0,
        total_steps=1,
        total_tokens=150,
        duration_sec=0.25,
    )

    assert ep_id is not None
    assert ep_id > 0

    recent = mem.get_recent_episodes(limit=5)
    assert len(recent) == 1
    assert recent[0].goal == "Calculate 15 * 4 + 10"
    assert recent[0].passed is True
    assert recent[0].score == 1.0


def test_episodic_summary_stats(tmp_path):
    db_file = tmp_path / "test_stats.db"
    mem = EpisodicMemory(db_path=db_file)

    mem.record_episode("Task 1", {}, [], True, 1.0, 2, 100, 0.5)
    mem.record_episode("Task 2", {}, [], False, 0.0, 3, 200, 0.8)

    stats = mem.get_summary_stats()
    assert stats["total_episodes"] == 2
    assert stats["success_rate"] == 0.5


def test_semantic_memory_scoring_and_retrieval():
    sem_mem = SemanticMemory()

    l1 = StructuredLesson(
        situation="Mathematical expressions with exponentiation",
        what_happened="Calculated safely",
        root_cause="None",
        rule="Use ** instead of ^ for powers in Python expressions",
        confidence=0.9,
    )
    l2 = StructuredLesson(
        situation="Web scraping and html parsing",
        what_happened="Encountered injection",
        root_cause="Raw input not filtered",
        rule="Sanitize user inputs before regex match",
        confidence=0.7,
    )

    id1 = sem_mem.add_lesson(l1)
    id2 = sem_mem.add_lesson(l2)

    # Query for mathematical powers
    results = sem_mem.query_lessons("How to calculate exponents in Python", top_k=1)
    assert len(results) == 1
    assert "**" in results[0].rule

    # Verify reinforcement feedback updates usefulness
    sem_mem.record_outcome(id1, success=True)
    item = sem_mem.items[id1]
    assert item.success_count == 1
    assert item.usefulness > 0.5
