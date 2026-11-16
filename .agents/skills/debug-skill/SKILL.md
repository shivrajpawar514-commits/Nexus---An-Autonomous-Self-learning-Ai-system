---
name: debug-skill
description: Systematic debugging workflows for front-end console errors, network REST endpoints, and sandbox regression monitoring.
---

# Dashboard & System Debugging Procedures

## 1. Network & Endpoint Verification
- Inspect HTTP response status codes for `/api/stats`, `/api/episodes`, `/api/run`, `/api/lessons`, and `/api/skills`.
- Verify JSON response payloads conform to expected schemas and handle null or empty collections gracefully without frontend throwing uncaught exceptions.

## 2. Port Conflict & Socket Binding
- If `OSError: [Errno 48] Address already in use` occurs, execute `lsof -i :<port>` to isolate the binding process ID.
- Ensure automated fallback increments port (`port + 1`) when previous daemon instances have not fully cleared.

## 3. Sandboxing & AST Verification
- Run `pytest tests/ -v` to confirm deterministic AST security checks, path jail protection, and ReAct parsing routines pass without regressions.

