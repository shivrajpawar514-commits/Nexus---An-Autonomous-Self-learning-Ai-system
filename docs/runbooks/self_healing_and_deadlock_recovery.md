# Incident Response Runbook: Self-Healing & Deadlock Recovery

## Overview
Nexus autonomously detects and mitigates runtime anomalies, infinite reasoning loops, tool flapping, and process deadlocks through automated circuit breakers and proactive deadlock detection.

## Circuit Breakers (`sandbox/watchdog.py`)
- **Tripping Threshold**: 3 consecutive execution errors on any single tool trips that tool's `CircuitBreaker` into `OPEN` state.
- **Cool-Down Period**: Default 30 seconds before probing in `HALF_OPEN` state.
- **Auto-Healing**: 2 consecutive successful executions in `HALF_OPEN` restore normal `CLOSED` operation.
- **Manual Reset**: Admin endpoint `POST /api/watchdog/reset` immediately resets all circuit breakers.

## Deadlock & Reasoning Loop Detection (`agent/deadlock_detector.py`)
- **Action Repetition**: Identical `action_name` and serialized `action_args` across 3 consecutive ReAct steps trigger an immediate system intervention prompt injected into LLM dialogue history.
- **Cyclic Error Detection**: Repeated identical error strings prevent further fruitless tool retries and enforce alternate path exploration or graceful task termination.
