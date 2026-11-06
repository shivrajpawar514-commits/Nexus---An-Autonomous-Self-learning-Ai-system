"""Unit and regression tests for ReAct Executor, budget controls, and parser resilience."""

import pytest
from agent.llm import MockLLM
from agent.executor import Executor, ReActStep, ExecutionResult
from tools.base import ToolRegistry, tool, ToolResult, PermissionTier


def test_executor_react_loop():
    llm = MockLLM()
    executor = Executor(llm=llm, max_steps=5)

    result = executor.run(goal="What is 15 * 4 + 10?")
    assert result.ok is True
    assert "70" in result.answer
    assert len(result.trajectory) >= 1
    assert result.trajectory[0].action_name == "calculator"


def test_executor_budget_enforcement():
    llm = MockLLM()
    # Enforce strict 1-step max limit
    executor = Executor(llm=llm, max_steps=1)
    result = executor.run(goal="Calculate 100 * 200 and format output")
    # Step limit reached
    assert result.total_steps == 1
    assert result.ok is False
    assert "maximum step limit" in result.error.lower()


def test_executor_token_budget_exceeded():
    llm = MockLLM()
    # Enforce unrealistically low token budget
    executor = Executor(llm=llm, token_budget=5)
    result = executor.run(goal="What is 10 + 20?")
    assert result.ok is False
    assert "token budget" in result.error.lower()


def test_executor_parenthesis_parsing():
    llm = MockLLM()
    executor = Executor(llm=llm)

    # Complex nested function call string
    test_str = "Thought: I will compute.\nAction: calculator(expression='pow(2, 3) + sqrt(16)')"
    thought, action_name, action_args = executor._parse_action_call(test_str)

    assert thought == "I will compute."
    assert action_name == "calculator"
    assert action_args.get("expression") == "pow(2, 3) + sqrt(16)"
