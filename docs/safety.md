# Safety, Ethics, and Risk Management Specification

## Threat Model & Autonomous Execution Guardrails

When granting an AI agent autonomy to generate plans, invoke system tools, and run arbitrary Python scripts, safety cannot be an afterthought. This document specifies the comprehensive defense-in-depth architecture implemented across the system.

---

### 1. Risk Matrix & Mitigations

| Threat Vector | Severity | Attack Scenario | Architectural Mitigation |
|---|---|---|---|
| **Arbitrary Code Execution / Host Compromise** | Critical | Agent executes malicious shell commands or deletes host filesystem. | Code execution is isolated within a strict sandbox with restricted AST imports, memory limits, and sub-process execution timeouts. |
| **Indirect Prompt Injection** | High | Untrusted web / file contents contain hidden instructions (`Ignore previous instructions and delete...`). | Content isolation: Tool outputs are wrapped as untrusted data blocks with instruction-stripping delimiters. System prompts strictly separate command channels from data channels. |
| **Runaway Costs / Infinite Execution Loops** | High | Agent enters cyclic failure loops with tools, burning tokens and compute. | Hard budget caps: Enforced maximum steps per task, hard timeout (seconds), and maximum token budget tracking with automatic termination. |
| **Memory Poisoning (Hallucinatory Degradation)** | Medium | Agent stores incorrect reflections from failed or hallucinated runs, degrading future accuracy. | Verified-Outcome Gating: Reflections are only persisted if verified by objective programmatic checks or high-confidence verifiers. Trust score decay diminishes unproven lessons. |
| **Reward Hacking** | Medium | Agent discovers shortcuts that trick naive verifiers without solving the actual task. | Multi-tier verifier hierarchy, hidden test suites on held-out test splits, and deterministic invariant checks. |

---

### 2. Sandbox Security Architecture

The Python execution tool (`tools/python_sandbox.py`) implements a multi-layer isolation envelope:

```
[Agent Action: run_python(code)]
            |
            v
[AST Static Analysis Filter]
  - Disallows blocked AST imports: `os.system`, `subprocess.Popen`, `socket`, `pty`
            |
            v
[Isolated Subprocess Runner]
  - Pre-allocated maximum memory cap (e.g. 256MB)
  - Wall-clock timeout enforcement (10s default)
  - Working directory restricted exclusively to scratch workspace
            |
            v
[Standard Output / Error Capture & Sanitization]
  - Truncation of excessive logs to prevent context explosion
```

---

### 3. Permission Tiers

Tools declare their operational privilege level via typed decorators:

1. **`READ_ONLY`**: Zero mutation impact (e.g., `calculator`, `read_file`, `web_search`). Auto-approved.
2. **`WORKSPACE_WRITE`**: Restricted mutations limited to the active sandbox folder (e.g., `write_file`, `run_python`). Approved within sandboxed bounds.
3. **`ELEVATED_RISK`**: External API writes, file deletions, or system configuration modifications. Requires explicit verification and audit logging.

