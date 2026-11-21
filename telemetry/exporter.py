"""Trace aggregation and OpenTelemetry hierarchical waterfall exporter."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from telemetry.tracer import Tracer, Span


class TraceExporter:
    """Serializes spans into waterfall traces and OpenTelemetry formats."""

    def __init__(self, tracer: Tracer):
        self.tracer = tracer

    def list_traces(self) -> List[Dict[str, Any]]:
        """List distinct traces with duration, root span name, and error flags."""
        spans = self.tracer.get_spans()
        trace_map: Dict[str, List[Span]] = {}
        for s in spans:
            trace_map.setdefault(s.context.trace_id, []).append(s)

        summaries = []
        for trace_id, t_spans in trace_map.items():
            roots = [s for s in t_spans if s.context.parent_span_id is None]
            root_name = roots[0].name if roots else t_spans[0].name
            min_start = min(s.start_time for s in t_spans)
            max_end = max((s.end_time or s.start_time) for s in t_spans)
            has_error = any(s.status == "ERROR" for s in t_spans)

            summaries.append({
                "trace_id": trace_id,
                "root_name": root_name,
                "span_count": len(t_spans),
                "duration_ms": round((max_end - min_start) * 1000.0, 2),
                "has_error": has_error,
                "start_time": min_start,
            })

        return sorted(summaries, key=lambda x: x["start_time"], reverse=True)

    def get_waterfall(self, trace_id: str) -> Dict[str, Any]:
        """Build hierarchical waterfall tree of spans for a specific trace."""
        spans = self.tracer.get_spans(trace_id=trace_id)
        if not spans:
            return {"trace_id": trace_id, "spans": [], "waterfall": []}

        min_start = min(s.start_time for s in spans)
        max_end = max((s.end_time or s.start_time) for s in spans)
        total_duration = max(0.001, (max_end - min_start) * 1000.0)

        waterfall = []
        for s in spans:
            offset_ms = (s.start_time - min_start) * 1000.0
            dur_ms = s.duration_ms
            waterfall.append({
                "span_id": s.context.span_id,
                "parent_span_id": s.context.parent_span_id,
                "name": s.name,
                "status": s.status,
                "offset_ms": round(offset_ms, 2),
                "duration_ms": round(dur_ms, 2),
                "relative_offset_pct": round((offset_ms / total_duration) * 100.0, 2),
                "relative_width_pct": max(1.0, round((dur_ms / total_duration) * 100.0, 2)),
                "attributes": s.attributes,
            })

        return {
            "trace_id": trace_id,
            "total_duration_ms": round(total_duration, 2),
            "span_count": len(spans),
            "waterfall": waterfall,
        }
