"""Unit and integration tests for SubagentDelegator and budget partitioning."""

import pytest
from agent.llm import MockLLM
from agent.delegator import SubagentDelegator, DelegationTask, DelegationResult
from tools.base import get_default_registry


def test_delegator_single_subtask():
    llm = MockLLM()
    registry = get_default_registry()
    delegator = SubagentDelegator(llm=llm, tool_registry=registry)

    task = DelegationTask(
        subgoal="Calculate 15 * 4 + 10",
        allowed_tools=["calculator"],
        token_budget=5000,
        max_steps=3,
    )

    result = delegator.delegate(task)

    assert isinstance(result, DelegationResult)
    assert result.ok is True
    assert "70" in str(result.answer)
    assert result.total_steps >= 1
    assert result.tokens_used > 0


def test_delegator_tool_isolation():
    llm = MockLLM()
    registry = get_default_registry()
    delegator = SubagentDelegator(llm=llm, tool_registry=registry)

    # Disallow calculator tool
    task = DelegationTask(
        subgoal="What is 15 * 4 + 10?",
        allowed_tools=["run_python"],
        token_budget=5000,
        max_steps=2,
    )

    # Isolated registry should NOT have calculator
    isolated = delegator._create_isolated_registry(task.allowed_tools)
    assert isolated.get("calculator") is None
    assert isolated.get("run_python") is not None


def test_delegator_batch_execution():
    llm = MockLLM()
    delegator = SubagentDelegator(llm=llm)

    tasks = [
        DelegationTask(subgoal="Task A: compute 10 + 20", allowed_tools=["calculator"]),
        DelegationTask(subgoal="Task B: compute 30 + 40", allowed_tools=["calculator"]),
    ]

    results = delegator.delegate_batch(tasks)
    assert len(results) == 2
    assert all(r.ok for r in results)
