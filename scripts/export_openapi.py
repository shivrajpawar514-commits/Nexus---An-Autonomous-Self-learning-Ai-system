"""OpenAPI 3.0 specification generator for the Nexus Mission Control REST API."""

import json
from pathlib import Path


OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Nexus Autonomous Agent Mission Control API",
        "version": "1.0.0",
        "description": "REST and Server-Sent Events API for autonomous task execution, telemetry, and self-learning inspection.",
    },
    "paths": {
        "/api/stats": {
            "get": {
                "summary": "Retrieve system telemetry and run aggregates",
                "responses": {
                    "200": {
                        "description": "Summary statistics",
                        "content": {"application/json": {}},
                    }
                },
            }
        },
        "/api/run": {
            "post": {
                "summary": "Execute an autonomous goal synchronously",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "goal": {"type": "string"},
                                    "use_memory": {"type": "boolean", "default": True},
                                    "use_reflection": {"type": "boolean", "default": True},
                                },
                                "required": ["goal"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Task execution report",
                        "content": {"application/json": {}},
                    }
                },
            }
        },
        "/api/stream": {
            "get": {
                "summary": "Real-time Server-Sent Events (SSE) telemetry connection",
                "responses": {
                    "200": {
                        "description": "Event stream",
                        "content": {"text/event-stream": {}},
                    }
                },
            }
        },
        "/api/stream_task": {
            "post": {
                "summary": "Execute a task with streaming Thought-Action-Observation SSE events",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {"goal": {"type": "string"}},
                                "required": ["goal"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Streaming execution events",
                        "content": {"text/event-stream": {}},
                    }
                },
            }
        },
        "/api/episodes": {
            "get": {
                "summary": "List historical episodic execution records",
                "responses": {"200": {"description": "List of episodes"}},
            }
        },
        "/api/tools": {
            "get": {
                "summary": "List registered tools in the agent sandbox",
                "responses": {"200": {"description": "List of available tools"}},
            }
        },
        "/api/skills": {
            "get": {
                "summary": "List synthesized and verified skills in library",
                "responses": {"200": {"description": "Skill library entries"}},
            }
        },
        "/api/export": {
            "get": {
                "summary": "Export complete database traces as JSON",
                "responses": {"200": {"description": "Complete telemetry dataset"}},
            }
        },
    },
}


def export_schema(output_path: str = "docs/openapi.json"):
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(OPENAPI_SPEC, indent=2), encoding="utf-8")
    print(f"OpenAPI 3.0 specification successfully exported to {output_path}")


if __name__ == "__main__":
    export_schema()
