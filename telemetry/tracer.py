"""OpenTelemetry-compatible distributed tracer and span primitives."""

from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SpanContext(BaseModel):
    trace_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    span_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_span_id: Optional[str] = None


class Span:
    """Represents a single timed unit of work in a distributed trace."""

    def __init__(
        self,
        name: str,
        context: Optional[SpanContext] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.context = context or SpanContext()
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = "OK"
        self.attributes: Dict[str, Any] = attributes or {}
        self.events: List[Dict[str, Any]] = []

    def set_attribute(self, key: str, value: Any) -> Span:
        self.attributes[key] = value
        return self

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Span:
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })
        return self

    def end(self, status: str = "OK") -> None:
        self.end_time = time.time()
        self.status = status

    @property
    def duration_ms(self) -> float:
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000.0
        return (self.end_time - self.start_time) * 1000.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "trace_id": self.context.trace_id,
            "span_id": self.context.span_id,
            "parent_span_id": self.context.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
        }

    def __enter__(self) -> Span:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.set_attribute("error", True)
            self.set_attribute("error.type", exc_type.__name__)
            self.set_attribute("error.message", str(exc_val))
            self.end(status="ERROR")
        else:
            self.end(status="OK")


class Tracer:
    """Thread-safe tracer collecting completed execution spans."""

    def __init__(self, service_name: str = "nexus-agent", max_spans: int = 1000):
        self.service_name = service_name
        self.max_spans = max_spans
        self._spans: List[Span] = []
        self._lock = threading.Lock()

    def start_span(
        self,
        name: str,
        parent: Optional[Span] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Create and start a new span, linking to parent if provided."""
        attrs = {"service.name": self.service_name}
        if attributes:
            attrs.update(attributes)

        if parent:
            ctx = SpanContext(
                trace_id=parent.context.trace_id,
                span_id=uuid.uuid4().hex[:16],
                parent_span_id=parent.context.span_id,
            )
        else:
            ctx = SpanContext()

        span = Span(name=name, context=ctx, attributes=attrs)
        with self._lock:
            self._spans.append(span)
            if len(self._spans) > self.max_spans:
                self._spans.pop(0)
        return span

    def get_spans(self, trace_id: Optional[str] = None) -> List[Span]:
        with self._lock:
            if trace_id:
                return [s for s in self._spans if s.context.trace_id == trace_id]
            return list(self._spans)

    def clear(self) -> None:
        with self._lock:
            self._spans.clear()
