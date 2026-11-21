# Distributed Tracing & OpenTelemetry Guide

## Overview
Nexus provides distributed tracing across autonomous agent workflows, subagent task delegations, and asynchronous queues. Tracing provides microsecond-accurate waterfall breakdowns of `Plan -> Act -> Observe -> Verify -> Reflect` cycles.

## Core Concepts
- **`Span`**: Represents a single timed operation (e.g. LLM inference, tool execution, memory retrieval).
- **`Trace`**: A directed acyclic graph (DAG) of parent-child spans sharing a common `trace_id`.
- **`TraceExporter`**: Serializes spans into OpenTelemetry (OTLP) waterfall formats.

## Using the `@trace_span` Decorator
```python
from telemetry.context import trace_span

@trace_span("custom_tool_execution")
def execute_my_tool(arg1: str):
    # Span is automatically started, timed, and linked to the active parent span
    # Any uncaught exception marks span status as ERROR with exception metadata
    return perform_work(arg1)
```

## REST API Endpoints
- `GET /api/traces`: List recent trace summaries with duration, span count, and error flags.
- `GET /api/traces/{trace_id}`: Full waterfall breakdown with offset percentages for timeline rendering.
