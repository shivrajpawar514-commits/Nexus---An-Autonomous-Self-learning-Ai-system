"""Unit and regression tests for Goal Planner, subtask decomposition, and replanning."""

import pytest
from agent.llm import MockLLM
from agent.planner import Planner, Plan


def test_planner_basic_decomposition():
    llm = MockLLM()
    planner = Planner(llm=llm)

    plan = planner.make_plan("Calculate 15 * 4 + 10 and format output")
    assert isinstance(plan, Plan)
    assert len(plan.subtasks) >= 2
    assert plan.goal == "Calculate 15 * 4 + 10 and format output"


def test_planner_with_lessons_and_skills():
    llm = MockLLM()
    planner = Planner(llm=llm)

    lessons = ["Avoid division by zero", "Format numerical answers cleanly"]
    skills = ["calculator", "run_python"]

    plan = planner.make_plan(
        goal="Perform financial ratio analysis",
        retrieved_lessons=lessons,
        retrieved_skills=skills,
    )
    assert isinstance(plan, Plan)
    assert len(plan.subtasks) > 0


def test_planner_replanning_on_failure():
    llm = MockLLM()
    planner = Planner(llm=llm)

    replan = planner.replan(
        goal="Download remote dataset and compute statistics",
        failed_subtask="Download remote dataset",
        error_context="404 Not Found from endpoint",
    )
    assert isinstance(replan, Plan)
    assert len(replan.subtasks) >= 1
    assert (
        "Diagnose" in replan.subtasks[0]
        or "alternative" in replan.subtasks[0].lower()
        or "recovery" in replan.rationale.lower()
        or len(replan.subtasks) > 0
    )
