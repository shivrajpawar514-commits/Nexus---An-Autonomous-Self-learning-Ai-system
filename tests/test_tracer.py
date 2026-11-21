"""Unit tests for OpenTelemetry distributed tracing, context propagation, and waterfall export."""

import pytest
import time
from telemetry.tracer import Tracer, Span
from telemetry.context import trace_span, get_global_tracer, set_current_span
from telemetry.exporter import TraceExporter


def test_tracer_parent_child_spans():
    tracer = Tracer()
    root = tracer.start_span("root_task")
    assert root.context.parent_span_id is None

    child = tracer.start_span("subtask_1", parent=root)
    assert child.context.parent_span_id == root.context.span_id
    assert child.context.trace_id == root.context.trace_id

    child.end(status="OK")
    root.end(status="OK")

    spans = tracer.get_spans(trace_id=root.context.trace_id)
    assert len(spans) == 2


def test_trace_span_decorator():
    tracer = Tracer()

    @trace_span("sample_computation", tracer=tracer)
    def compute(x: int, y: int) -> int:
        return x + y

    res = compute(10, 20)
    assert res == 30

    spans = tracer.get_spans()
    assert len(spans) == 1
    assert spans[0].name == "sample_computation"
    assert spans[0].status == "OK"
    assert spans[0].duration_ms >= 0


def test_trace_span_decorator_exception_capture():
    tracer = Tracer()

    @trace_span("failing_task", tracer=tracer)
    def explode():
        raise ValueError("Simulated fault")

    with pytest.raises(ValueError, match="Simulated fault"):
        explode()

    spans = tracer.get_spans()
    assert len(spans) == 1
    assert spans[0].status == "ERROR"
    assert spans[0].attributes["error"] is True
    assert spans[0].attributes["error.type"] == "ValueError"


def test_trace_exporter_waterfall_and_list():
    tracer = Tracer()
    root = tracer.start_span("parent_job")
    c1 = tracer.start_span("fetch_data", parent=root)
    c1.end()
    c2 = tracer.start_span("process_data", parent=root)
    c2.end()
    root.end()

    exporter = TraceExporter(tracer)
    trace_list = exporter.list_traces()
    assert len(trace_list) == 1
    assert trace_list[0]["span_count"] == 3
    assert trace_list[0]["root_name"] == "parent_job"

    waterfall_data = exporter.get_waterfall(root.context.trace_id)
    assert len(waterfall_data["waterfall"]) == 3
    assert waterfall_data["total_duration_ms"] >= 0
