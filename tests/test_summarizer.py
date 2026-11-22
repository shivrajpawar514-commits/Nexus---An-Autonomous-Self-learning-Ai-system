"""Unit tests for ContextSummarizer trajectory condensation."""

import pytest
from agent.llm import MockLLM
from agent.executor import ReActStep
from agent.summarizer import ContextSummarizer


def test_trajectory_condensation():
    llm = MockLLM()
    summarizer = ContextSummarizer(llm=llm, token_threshold=500)

    trajectory = [
        ReActStep(step_index=1, thought="Find prime numbers", action_name="run_python", observation="[2, 3, 5, 7]"),
        ReActStep(step_index=2, thought="Sum primes", action_name="calculator", observation="17"),
        ReActStep(step_index=3, thought="Finish execution", action_name="finish", observation="Task completed."),
    ]

    summary_str = summarizer.condense_trajectory(trajectory)
    assert "Execution Summary:" in summary_str
    assert "Step 1" in summary_str
    assert "Step 2" in summary_str
    assert "Step 3" in summary_str


def test_summarize_context_below_threshold():
    llm = MockLLM()
    summarizer = ContextSummarizer(llm=llm, token_threshold=100)

    short_dialogue = "Goal: Calculate 15 * 4. Result: 60."
    condensed = summarizer.summarize_context(short_dialogue)
    # Below threshold returns raw dialogue unchanged
    assert condensed == short_dialogue
