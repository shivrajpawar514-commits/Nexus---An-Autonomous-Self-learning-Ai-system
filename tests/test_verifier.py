"""Unit and regression tests for 3-tier verifier hierarchy."""

import pytest
from agent.llm import MockLLM
from agent.verifier import Verifier, Verdict
from eval.checkers import exact_number_checker, string_contains_checker


def test_verifier_programmatic_exact_match():
    verifier = Verifier()
    v1 = verifier.check_programmatic(actual_output="70", expected_output="70")
    assert v1.passed is True
    assert v1.trust == 1.0
    assert v1.verifier_tier == "programmatic_exact_match"

    v2 = verifier.check_programmatic(actual_output="68", expected_output="70")
    assert v2.passed is False
    assert v2.trust == 1.0


def test_verifier_programmatic_custom_function():
    verifier = Verifier()
    num_check = exact_number_checker(42.0)

    v1 = verifier.check_programmatic(actual_output="The computed answer is 42.000", test_fn=num_check)
    assert v1.passed is True
    assert v1.trust == 1.0

    v2 = verifier.check_programmatic(actual_output="The computed answer is 99.000", test_fn=num_check)
    assert v2.passed is False


def test_verifier_string_contains():
    verifier = Verifier()
    str_check = string_contains_checker("neural network")

    v1 = verifier.check_programmatic(actual_output="A deep neural network was trained", test_fn=str_check)
    assert v1.passed is True

    v2 = verifier.check_programmatic(actual_output="Random forest classifier", test_fn=str_check)
    assert v2.passed is False


def test_verifier_llm_judge_fallback():
    # Without LLM, should fallback to non-empty heuristic
    verifier_no_llm = Verifier(llm=None)
    v_heur = verifier_no_llm.check_llm_judge(goal="Summarize document", output="Document summary here.")
    assert v_heur.passed is True
    assert v_heur.trust == 0.4
    assert v_heur.verifier_tier == "heuristic_fallback"

    # With MockLLM
    llm = MockLLM()
    verifier_llm = Verifier(llm=llm)
    v_judge = verifier_llm.check_llm_judge(goal="Compute sum", output="Result is 15")
    assert v_judge.trust == 0.5 or v_judge.trust == 0.4
