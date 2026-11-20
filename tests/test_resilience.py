"""Unit tests for TokenBucketRateLimiter and exponential backoff retry executor."""

import time
import pytest
from agent.resilience import TokenBucketRateLimiter, with_exponential_backoff


def test_token_bucket_acquire_and_exhaust():
    limiter = TokenBucketRateLimiter(capacity=3, refill_rate=1.0)

    # Acquire 3 immediate tokens
    assert limiter.acquire(1) is True
    assert limiter.acquire(1) is True
    assert limiter.acquire(1) is True

    # 4th immediate acquisition should fail without wait
    assert limiter.acquire(1, timeout=0.01) is False


def test_exponential_backoff_success():
    attempts = 0

    def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("Temporary glitch")
        return "SUCCESS"

    result = with_exponential_backoff(
        flaky_func,
        max_retries=3,
        initial_delay=0.05,
        backoff_factor=1.5,
        retryable_exceptions=(ConnectionError,),
    )
    assert result == "SUCCESS"
    assert attempts == 3


def test_exponential_backoff_exhausted():
    def always_fails():
        raise ValueError("Permanent error")

    with pytest.raises(ValueError) as exc:
        with_exponential_backoff(
            always_fails,
            max_retries=2,
            initial_delay=0.02,
            retryable_exceptions=(ValueError,),
        )
    assert "Permanent error" in str(exc.value)
