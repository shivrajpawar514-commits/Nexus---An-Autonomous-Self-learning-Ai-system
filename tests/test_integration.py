"""End-to-end integration tests for the Master Orchestrator Pipeline and CLI."""

import pytest
from pathlib import Path
from agent.llm import MockLLM
from agent.orchestrator import Orchestrator, TaskRunReport
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.skills import SkillLibrary
from tools.base import get_default_registry


def test_orchestrator_end_to_end(tmp_path):
    llm = MockLLM()
    ep_mem = EpisodicMemory(db_path=tmp_path / "int_episodes.db")
    sem_mem = SemanticMemory()
    registry = get_default_registry()
    skill_lib = SkillLibrary(tool_registry=registry)

    orchestrator = Orchestrator(
        llm=llm,
        tool_registry=registry,
        episodic_memory=ep_mem,
        semantic_memory=sem_mem,
        skill_library=skill_lib,
    )

    report = orchestrator.run_task(
        goal="Calculate 15 * 4 + 10",
        expected_output=70,
        use_memory=True,
        use_reflection=True,
    )

    assert isinstance(report, TaskRunReport)
    assert report.passed is True
    assert "70" in str(report.execution.answer)
    assert report.verdict.trust == 1.0
    assert report.reflection is not None
    assert len(report.reflection.lessons) >= 1

    # Verify episode was persisted
    recent = ep_mem.get_recent_episodes(limit=1)
    assert len(recent) == 1
    assert recent[0].passed is True

    # Verify lesson was stored in semantic memory
    assert len(sem_mem.items) >= 1


def test_orchestrator_memory_reuse_across_runs(tmp_path):
    llm = MockLLM()
    ep_mem = EpisodicMemory(db_path=tmp_path / "reuse_episodes.db")
    sem_mem = SemanticMemory()
    orchestrator = Orchestrator(llm=llm, episodic_memory=ep_mem, semantic_memory=sem_mem)

    # Run 1
    orchestrator.run_task(goal="What is 10 + 20?", expected_output=30, use_memory=True, use_reflection=True)
    # Run 2 on similar domain should retrieve the lesson from Run 1
    report2 = orchestrator.run_task(goal="What is 5 + 15?", expected_output=20, use_memory=True, use_reflection=True)

    assert len(report2.retrieved_lessons) >= 1
    stats = ep_mem.get_summary_stats()
    assert stats["total_runs"] == 2
