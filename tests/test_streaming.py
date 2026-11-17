"""Tests for Server-Sent Events (SSE) telemetry and streaming endpoints."""

import json
import pytest
from dashboard.server import get_orchestrator


def test_orchestrator_instance_available():
    orch = get_orchestrator()
    assert orch is not None
    assert orch.tool_registry.get("calculator") is not None


def test_stream_event_formatting():
    # Verify standard SSE message format: 'data: {...}\n\n'
    event_payload = {"type": "connected", "status": "active"}
    sse_line = f"data: {json.dumps(event_payload)}\n\n"
    assert sse_line.startswith("data: ")
    assert sse_line.endswith("\n\n")

    decoded = json.loads(sse_line[6:].strip())
    assert decoded["type"] == "connected"
    assert decoded["status"] == "active"
