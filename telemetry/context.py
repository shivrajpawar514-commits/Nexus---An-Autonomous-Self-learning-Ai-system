"""Context propagation and span instrumentation decorator."""

from __future__ import annotations
import functools
import threading
from typing import Callable, Optional
from telemetry.tracer import Span, Tracer

_current_span_storage = threading.local()
_global_tracer: Optional[Tracer] = None


def get_global_tracer() -> Tracer:
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer()
    return _global_tracer


def get_current_span() -> Optional[Span]:
    return getattr(_current_span_storage, "current_span", None)


def set_current_span(span: Optional[Span]) -> None:
    _current_span_storage.current_span = span


def trace_span(name: Optional[str] = None, tracer: Optional[Tracer] = None) -> Callable:
    """Decorator to automatically instrument functions as tracing spans."""

    def decorator(fn: Callable) -> Callable:
        span_name = name or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            t = tracer or get_global_tracer()
            parent = get_current_span()
            span = t.start_span(name=span_name, parent=parent)
            prev_span = parent
            set_current_span(span)
            try:
                with span:
                    result = fn(*args, **kwargs)
                return result
            finally:
                set_current_span(prev_span)

        return wrapper

    return decorator
