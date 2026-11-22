"""Unit and regression tests for memory compaction and skill versioning."""

import time
import pytest
from memory.skills import SkillLibrary, SkillEntry
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from agent.reflector import StructuredLesson


def test_skill_versioning_and_deprecation():
    lib = SkillLibrary()
    lib.add_skill(
        name="multiplier",
        description="Multiplies number by 2",
        code="def multiplier(x: int) -> int:\n    return x * 2",
        test_code="assert multiplier(5) == 10",
    )
    lib.verify_and_promote("multiplier")

    assert lib.skills["multiplier"].version == "1.0.0"
    assert lib.skills["multiplier"].is_deprecated is False

    # Upgrade skill
    upgraded = lib.upgrade_skill(
        name="multiplier",
        new_code="def multiplier(x: int) -> int:\n    return x * 2  # optimized",
        new_test_code="assert multiplier(10) == 20",
    )
    assert upgraded is not None
    assert upgraded.version == "1.0.1"

    # Deprecate skill
    deprecate_res = lib.deprecate_skill("multiplier", reason="Replaced by specialized GPU kernel")
    assert deprecate_res is True
    assert lib.skills["multiplier"].is_deprecated is True
    assert lib.skills["multiplier"].deprecation_reason == "Replaced by specialized GPU kernel"
    assert lib.tool_registry.get("multiplier") is None


def test_semantic_memory_compaction():
    mem = SemanticMemory()
    # Add a high-importance lesson
    l_high = StructuredLesson(
        situation="Situation A",
        what_happened="Happened A",
        root_cause="None",
        rule="High trust rule",
        confidence=0.9,
        trust_weight=1.0,
    )
    # Add a low-importance lesson
    l_low = StructuredLesson(
        situation="Situation B",
        what_happened="Happened B",
        root_cause="None",
        rule="Low trust rule",
        confidence=0.1,
        trust_weight=0.1,
    )

    id_high = mem.add_lesson(l_high)
    id_low = mem.add_lesson(l_low)

    # Force low usefulness on id_low
    mem.items[id_low].failure_count = 10
    mem.items[id_low].success_count = 0

    assert len(mem.items) == 2
    pruned_count = mem.compact_memory(min_importance=0.20)
    assert pruned_count == 1
    assert id_high in mem.items
    assert id_low not in mem.items


def test_episodic_memory_pruning(tmp_path):
    mem = EpisodicMemory(db_path=tmp_path / "prune_test.db")
    for i in range(10):
        mem.record_episode(f"Goal {i}", {}, [], True, 1.0, 2, 100, 0.5)

    assert mem.get_summary_stats()["total_episodes"] == 10
    # Prune keeping at least 5
    pruned = mem.prune_old_episodes(max_age_seconds=0.001, keep_minimum=5)
    # Retains minimum 5
    assert mem.get_summary_stats()["total_episodes"] == 5
