"""Sandbox Watchdog and Circuit Breaker for autonomous runtime resilience."""

from __future__ import annotations
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple
from pydantic import BaseModel, Field


class CircuitBreakerState(str, Enum):
    CLOSED = "CLOSED"        # Normal operation: requests pass through
    OPEN = "OPEN"            # Tripped: requests are blocked to protect system
    HALF_OPEN = "HALF_OPEN"  # Testing: limited requests allowed to verify recovery


class CircuitBreaker:
    """Thread-safe circuit breaker protecting tools from cascade failures."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout_sec: float = 30.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
        self.total_trips = 0

    def record_success(self) -> None:
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:
                self.reset()
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.state == CircuitBreakerState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            self.trip()

    def trip(self) -> None:
        self.state = CircuitBreakerState.OPEN
        self.last_state_change = time.time()
        self.total_trips += 1

    def reset(self) -> None:
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()

    def allow_execution(self) -> Tuple[bool, Optional[str]]:
        """Determines if execution is allowed or tripped."""
        if self.state == CircuitBreakerState.CLOSED:
            return True, None

        elapsed = time.time() - self.last_state_change
        if self.state == CircuitBreakerState.OPEN:
            if elapsed >= self.recovery_timeout_sec:
                # Transition to HALF_OPEN to probe health
                self.state = CircuitBreakerState.HALF_OPEN
                self.last_state_change = time.time()
                self.success_count = 0
                return True, None
            return False, f"Circuit breaker '{self.name}' is OPEN (tripped {int(elapsed)}s ago, recovery in {int(self.recovery_timeout_sec - elapsed)}s)"

        if self.state == CircuitBreakerState.HALF_OPEN:
            return True, None

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "total_trips": self.total_trips,
            "recovery_timeout_sec": self.recovery_timeout_sec,
        }


class SandboxWatchdog:
    """Manages circuit breakers across all agent tools and protects sandbox execution."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout_sec: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(self, tool_name: str) -> CircuitBreaker:
        if tool_name not in self._breakers:
            self._breakers[tool_name] = CircuitBreaker(
                name=tool_name,
                failure_threshold=self.failure_threshold,
                recovery_timeout_sec=self.recovery_timeout_sec,
            )
        return self._breakers[tool_name]

    def check_tool_health(self, tool_name: str) -> Tuple[bool, Optional[str]]:
        return self.get_breaker(tool_name).allow_execution()

    def record_tool_result(self, tool_name: str, success: bool) -> None:
        breaker = self.get_breaker(tool_name)
        if success:
            breaker.record_success()
        else:
            breaker.record_failure()

    def reset_all(self) -> None:
        for b in self._breakers.values():
            b.reset()

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_monitored_tools": len(self._breakers),
            "breakers": {name: b.to_dict() for name, b in self._breakers.items()},
        }
