"""Unit tests for CircuitBreaker, SandboxWatchdog, and DeadlockDetector."""

import pytest
import time
from sandbox.watchdog import CircuitBreaker, CircuitBreakerState, SandboxWatchdog
from agent.deadlock_detector import DeadlockDetector, DeadlockType
from agent.executor import ReActStep


def test_circuit_breaker_transitions():
    cb = CircuitBreaker("test_tool", failure_threshold=2, recovery_timeout_sec=0.1)
    assert cb.state == CircuitBreakerState.CLOSED

    # 1 failure: stays CLOSED
    cb.record_failure()
    assert cb.state == CircuitBreakerState.CLOSED

    # 2 failures: trips OPEN
    cb.record_failure()
    assert cb.state == CircuitBreakerState.OPEN
    allowed, reason = cb.allow_execution()
    assert allowed is False
    assert "is OPEN" in reason

    # Wait for recovery timeout
    time.sleep(0.12)
    allowed, _ = cb.allow_execution()
    assert allowed is True
    assert cb.state == CircuitBreakerState.HALF_OPEN

    # Two consecutive successes reset to CLOSED
    cb.record_success()
    assert cb.state == CircuitBreakerState.HALF_OPEN
    cb.record_success()
    assert cb.state == CircuitBreakerState.CLOSED


def test_sandbox_watchdog_monitoring():
    wd = SandboxWatchdog(failure_threshold=2)
    allowed, _ = wd.check_tool_health("python_sandbox")
    assert allowed is True

    wd.record_tool_result("python_sandbox", success=False)
    wd.record_tool_result("python_sandbox", success=False)

    allowed, reason = wd.check_tool_health("python_sandbox")
    assert allowed is False
    assert "OPEN" in reason

    # Reset
    wd.reset_all()
    allowed, _ = wd.check_tool_health("python_sandbox")
    assert allowed is True


def test_deadlock_detector_identical_action_loop():
    detector = DeadlockDetector(repetition_threshold=3)
    steps = [
        ReActStep(step_index=1, thought="Run search", action_name="search_web", action_args={"q": "AI"}, observation="No result"),
        ReActStep(step_index=2, thought="Run search again", action_name="search_web", action_args={"q": "AI"}, observation="No result"),
        ReActStep(step_index=3, thought="Run search again", action_name="search_web", action_args={"q": "AI"}, observation="No result"),
    ]

    intervention = detector.analyze(steps)
    assert intervention.detected is True
    assert intervention.deadlock_type == DeadlockType.IDENTICAL_ACTION_LOOP
    assert "search_web" in intervention.message
    assert "CRITICAL SYSTEM INTERVENTION" in intervention.intervention_prompt


def test_deadlock_detector_clean_trajectory():
    detector = DeadlockDetector(repetition_threshold=3)
    steps = [
        ReActStep(step_index=1, thought="Step 1", action_name="calculator", action_args={"expr": "1+1"}, observation="2"),
        ReActStep(step_index=2, thought="Step 2", action_name="files", action_args={"path": "test.txt"}, observation="content"),
    ]
    intervention = detector.analyze(steps)
    assert intervention.detected is False
