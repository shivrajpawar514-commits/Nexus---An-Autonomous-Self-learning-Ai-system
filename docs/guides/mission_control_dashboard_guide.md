# Nexus Mission Control Dashboard: Operator Guide & Subsystem Diagnostics

## 1. Overview
The **Nexus Mission Control Dashboard** is a unified, high-density operations HUD designed for real-time monitoring, telemetry analysis, multi-agent coordination, and security enforcement across autonomous agent subsystems.

Running over a lightweight asynchronous HTTP server (`dashboard/server.py`), the dashboard combines client-side glassmorphism and streaming WebSockets/Server-Sent Events with automated subsystem diagnostics.

---

## 2. Navigation Panels & Capabilities

### Tab 1: Live Console (`/api/run`, `/api/stream_task`)
- **Target Specification**: High-level goal submission with automated prompt templates.
- **Trace Visualization**: Live step-by-step thought-action-observation cycles.
- **Real-Time Latency & Token Usage**: Micro-cost and token burn calculations per execution step.

### Tab 2: Sandbox Lab (`/api/sandbox/run`)
- **Deterministic Python AST Guard**: Pre-execution AST traversal ensuring no blacklisted syscalls or network operations.
- **Dry-run Evaluation**: Direct isolated code snippet testing without polluting episodic memory.

### Tab 3: Telemetry & Tracing (`/api/traces`)
- **Distributed Spans**: OpenTelemetry-compliant hierarchical span visualization.
- **Span Metadata**: Step status, error traces, token counts, and parent-child execution lineages.

### Tab 4: Memory & Policy Engine (`/api/lessons`, `/api/policies`)
- **Episodic Memory**: Query past execution episodes, outcomes, and failure post-mortems.
- **Semantic Lessons**: View synthesized operational rules extracted via reflection.
- **Declarative Policies**: Audit active RBAC roles and tool access restrictions.

### Tab 5: Skill Synthesizer (`/api/skills`, `/api/skills/add`)
- **Autonomous Skill Extraction**: Dynamic conversion of proven multi-step solution patterns into reusable skills.
- **Automated Verification**: Sandbox unit testing of newly authored skills prior to production deployment.

### Tab 6: Benchmark Suite (`/api/eval`)
- **Dataset Partitioning**: Evaluation across train, validation, and held-out test splits.
- **Comparative Metrics**: Accuracy percentage, average step count, and token overhead.

### Tab 7: Swarm Blackboard (`/api/blackboard/messages`, `/api/consensus/status`)
- **Shared Memory Blackboard**: Inter-agent asynchronous message exchange tagged by `HYPOTHESIS`, `EVIDENCE`, `CRITIQUE`, and `SYNTHESIS`.
- **Consensus Ballot Protocol**: Quorum-based voting mechanism enabling agents to vote `APPROVE` or `REJECT` on candidate plans before execution.

### Tab 8: Semantic Model Router & Genetic Evolution (`/api/routing/models`, `/api/evolution/status`)
- **Tier Arbitration**: FAST (heuristic/small), STANDARD (balanced), and REASONING (deep chain-of-thought) tier routing.
- **Query Complexity Classifier**: Real-time evaluation of prompt complexity, fallback triggers, and estimated token costs.
- **Evolutionary Prompt Tournaments**: Genetic crossover, mutation, and Pareto fitness tournament tracking.

### Tab 9: Virtual Filesystem (VFS) & Watchdog Security (`/api/vfs/status`, `/api/watchdog/status`)
- **Copy-on-Write (CoW) Workspace**: Multi-tenant workspace isolation with uncommitted dirty layer tracking and one-click commit/rollback.
- **Sandbox Watchdog**: Real-time circuit breaker status monitoring (`CLOSED`, `OPEN`, `HALF-OPEN`) and deadlock watchdog recovery.

### Tab 10: System Diagnostics Probes (`/api/diagnostics`)
- **Sub-millisecond Health Probes**: Unified probing across all 7 operational subsystems:
  1. `memory_hierarchy`: Episodic memory and semantic lesson stores.
  2. `virtual_filesystem`: Tenant mount integrity and CoW layer health.
  3. `sandbox_watchdog`: Circuit breaker trip checks and monitoring daemon status.
  4. `policy_engine`: Rule integrity and RBAC policy binding.
  5. `model_router`: Model tier availability and provider fallback channels.
  6. `swarm_blackboard`: Message queue latency and consensus quorum readiness.
  7. `knowledge_graph`: Triples count and entity relation graph connectivity.
- **Health Aggregation**: Computed overall state (`HEALTHY`, `DEGRADED`, `UNHEALTHY`) based on probe results.

---

## 3. Subsystem Health Probe Specification (`dashboard/diagnostics.py`)

### Schema: `SubsystemProbeResult`
```python
class SubsystemProbeResult(BaseModel):
    name: str              # Unique subsystem identifier
    status: str            # "HEALTHY" | "DEGRADED" | "UNHEALTHY"
    latency_ms: float      # Round-trip probe execution latency in milliseconds
    details: Dict[str, Any]# Subsystem-specific diagnostic metrics or error messages
```

### Schema: `DiagnosticsReport`
```python
class DiagnosticsReport(BaseModel):
    timestamp: float       # Epoch seconds of probe execution
    overall_status: str    # Aggregate status across all subsystems
    subsystems_probed: int # Total number of probed subsystems (7)
    healthy_count: int     # Number of subsystems reporting HEALTHY
    results: List[SubsystemProbeResult]
```

### Health Aggregation Rule
$$\text{Status} = \begin{cases} 
\text{HEALTHY} & \text{if } \text{healthy\_count} = N \\
\text{DEGRADED} & \text{if } N/2 \le \text{healthy\_count} < N \\
\text{UNHEALTHY} & \text{if } \text{healthy\_count} < N/2
\end{cases}$$

---

## 4. Operator Runbook: Common Incidents & Remediation

| Symptom | Root Cause | Remediation Action |
|---|---|---|
| `sandbox_watchdog` status is `DEGRADED` | Circuit breaker tripped due to excessive tool failures | Navigate to **VFS & Security** tab; click **Reset All Breakers** or call `POST /api/watchdog/reset`. |
| `virtual_filesystem` has uncommitted changes | Agent crashed during active transaction | Click **Commit CoW Layer** to land changes, or inspect tenant mounts. |
| `model_router` reports missing tiers | Provider API key missing or rate-limited | Check environment variables and verify fallback models in **Model Router** panel. |
| `consensus_state` stuck on `PENDING` | Insufficient agent quorum votes | Broadcast `SYNTHESIS` message or manually cast approval ballot in **Swarm Blackboard**. |
