"""Unit and regression tests for evaluation benchmark runner and dataset splits."""

import pytest
from agent.llm import MockLLM
from agent.orchestrator import Orchestrator
from eval.tasks.data_tasks import BENCHMARK_TASKS, get_tasks_by_split
from eval.run import evaluate_split


def test_benchmark_task_splits_integrity():
    train_tasks = get_tasks_by_split("train")
    val_tasks = get_tasks_by_split("val")
    test_tasks = get_tasks_by_split("test")

    assert len(train_tasks) >= 3
    assert len(val_tasks) >= 2
    assert len(test_tasks) >= 3
    assert len(BENCHMARK_TASKS) == len(train_tasks) + len(val_tasks) + len(test_tasks)

    # Ensure no ID collisions across splits
    all_ids = [t.id for t in BENCHMARK_TASKS]
    assert len(all_ids) == len(set(all_ids))


def test_evaluate_split_execution():
    llm = MockLLM()
    orchestrator = Orchestrator(llm=llm)

    metrics = evaluate_split(orchestrator, split="test", use_memory=True, use_reflection=False)

    assert metrics["total_tasks"] == 3
    assert metrics["success_rate"] == 100.0
    assert metrics["avg_steps"] > 0.0
    assert metrics["avg_tokens"] > 0.0
