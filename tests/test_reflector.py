"""Unit and regression tests for Reflexion engine and verbal reinforcement learning."""

import pytest
from agent.llm import MockLLM
from agent.verifier import Verdict
from agent.reflector import Reflector, StructuredLesson, ReflectionResult


def test_reflector_successful_trajectory():
    llm = MockLLM()
    reflector = Reflector(llm=llm)

    verdict = Verdict(
        passed=True,
        trust=1.0,
        verifier_tier="programmatic_assertion",
        evidence="Asserted 70 == 70",
        score=1.0,
    )

    result = reflector.reflect(
        goal="Calculate 15 * 4 + 10",
        trajectory_str="Step 1: Thought: calculate, Action: calculator(expression='15 * 4 + 10')",
        verdict=verdict,
    )

    assert isinstance(result, ReflectionResult)
    assert result.passed is True
    assert len(result.lessons) >= 1
    assert result.lessons[0].trust_weight > 0.0


def test_reflector_failed_trajectory_root_cause():
    llm = MockLLM()
    reflector = Reflector(llm=llm)

    verdict = Verdict(
        passed=False,
        trust=1.0,
        verifier_tier="programmatic_assertion",
        evidence="ZeroDivisionError in line 4",
        score=0.0,
    )

    result = reflector.reflect(
        goal="Compute average rating when count is 0",
        trajectory_str="Step 1: Action: run_python(code='print(sum / 0)')",
        verdict=verdict,
    )

    assert result.passed is False
    assert len(result.lessons) >= 1
    lesson = result.lessons[0]
    assert isinstance(lesson, StructuredLesson)
    assert lesson.rule != ""
    assert lesson.trust_weight <= 1.0


def test_reflector_trust_discounting_with_weak_verifier():
    llm = MockLLM()
    reflector = Reflector(llm=llm)

    # Weak verifier with 0.4 trust
    weak_verdict = Verdict(
        passed=True,
        trust=0.4,
        verifier_tier="heuristic_fallback",
        evidence="Non-empty text",
        score=0.5,
    )

    result = reflector.reflect(
        goal="Draft essay",
        trajectory_str="Step 1: finish(answer='Essay text')",
        verdict=weak_verdict,
    )

    # Trust weight should be discount-scaled by 0.4
    assert result.lessons[0].trust_weight <= 0.4
