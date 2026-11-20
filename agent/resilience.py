"""Resilience primitives: Token-bucket rate limiter and exponential backoff retry executor."""

from __future__ import annotations
import math
import random
import threading
import time
from typing import Any, Callable, Optional, Tuple, TypeVar

T = TypeVar("T")


class TokenBucketRateLimiter:
    """Thread-safe Token Bucket Rate Limiter for LLM calls and tool APIs."""

    def __init__(self, capacity: int = 60, refill_rate: float = 10.0):
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)  # tokens per second
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        start = time.time()
        with self._lock:
            while True:
                now = time.time()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                self.last_refill = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                if timeout is not None and (time.time() - start) >= timeout:
                    return False

                time.sleep(0.02)


def with_exponential_backoff(
    fn: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[type, ...] = (Exception,),
) -> T:
    """Executes a callable with exponential backoff and randomized jitter."""
    delay = initial_delay
    last_err: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            return fn()
        except retryable_exceptions as e:
            last_err = e
            if attempt == max_retries:
                raise e
            sleep_time = delay * (1 + random.random() * 0.2 if jitter else 1)
            time.sleep(sleep_time)
            delay *= backoff_factor

    raise last_err or RuntimeError("Execution failed without explicit exception")
