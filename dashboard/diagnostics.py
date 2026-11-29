"""System diagnostics and health probing engine for Nexus autonomous agent subsystems."""

from __future__ import annotations
import time
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class SubsystemProbeResult(BaseModel):
    name: str
    status: str = "HEALTHY"  # HEALTHY, DEGRADED, UNHEALTHY
    latency_ms: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class DiagnosticsReport(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    overall_status: str = "HEALTHY"
    subsystems_probed: int = 0
    healthy_count: int = 0
    results: List[SubsystemProbeResult] = Field(default_factory=list)


class SystemDiagnostics:
    """Probes all operational subsystems and generates an aggregated health score."""

    def __init__(self, server_context: Dict[str, Any]):
        self.ctx = server_context

    def probe_all(self) -> DiagnosticsReport:
        results: List[SubsystemProbeResult] = []

        # 1. Memory Subsystem
        t0 = time.time()
        try:
            orch = self.ctx.get("orchestrator")
            episodes = orch.episodic_memory.get_summary_stats() if orch else {}
            lessons_count = len(orch.semantic_memory.items) if orch else 0
            results.append(SubsystemProbeResult(
                name="memory_hierarchy",
                status="HEALTHY",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"episodes": episodes.get("total_episodes", 0), "lessons": lessons_count},
            ))
        except Exception as e:
            results.append(SubsystemProbeResult(
                name="memory_hierarchy",
                status="DEGRADED",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"error": str(e)},
            ))

        # 2. Virtual Filesystem (VFS)
        t0 = time.time()
        try:
            wm = self.ctx.get("workspace_manager")
            tenants = wm.list_tenants() if wm else []
            results.append(SubsystemProbeResult(
                name="virtual_filesystem",
                status="HEALTHY",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"tenants_count": len(tenants)},
            ))
        except Exception as e:
            results.append(SubsystemProbeResult(
                name="virtual_filesystem",
                status="DEGRADED",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"error": str(e)},
            ))

        # 3. Sandbox Watchdog & Circuit Breakers
        t0 = time.time()
        try:
            wd = self.ctx.get("watchdog")
            status = wd.get_status() if wd else {}
            tripped = [k for k, v in status.get("breakers", {}).items() if v.get("state") == "OPEN"]
            res_status = "DEGRADED" if tripped else "HEALTHY"
            results.append(SubsystemProbeResult(
                name="sandbox_watchdog",
                status=res_status,
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"monitored_tools": status.get("total_monitored_tools", 0), "tripped_breakers": tripped},
            ))
        except Exception as e:
            results.append(SubsystemProbeResult(
                name="sandbox_watchdog",
                status="UNHEALTHY",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"error": str(e)},
            ))

        # 4. Declarative Policy Engine
        t0 = time.time()
        try:
            pe = self.ctx.get("policy_engine")
            policies = pe.list_policies() if pe else []
            results.append(SubsystemProbeResult(
                name="policy_engine",
                status="HEALTHY",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"active_policies": len(policies)},
            ))
        except Exception as e:
            results.append(SubsystemProbeResult(
                name="policy_engine",
                status="DEGRADED",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"error": str(e)},
            ))

        # 5. Semantic Model Router
        t0 = time.time()
        try:
            mr = self.ctx.get("model_router")
            tiers = mr.get_tier_info() if mr else {}
            results.append(SubsystemProbeResult(
                name="model_router",
                status="HEALTHY",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"available_tiers": list(tiers.keys())},
            ))
        except Exception as e:
            results.append(SubsystemProbeResult(
                name="model_router",
                status="DEGRADED",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"error": str(e)},
            ))

        # 6. Swarm Blackboard & Consensus
        t0 = time.time()
        try:
            bb = self.ctx.get("blackboard")
            count = bb.count() if bb else 0
            results.append(SubsystemProbeResult(
                name="swarm_blackboard",
                status="HEALTHY",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"total_messages": count},
            ))
        except Exception as e:
            results.append(SubsystemProbeResult(
                name="swarm_blackboard",
                status="DEGRADED",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"error": str(e)},
            ))

        # 7. Knowledge Graph
        t0 = time.time()
        try:
            kg = self.ctx.get("knowledge_graph")
            triples = kg.count() if kg else 0
            results.append(SubsystemProbeResult(
                name="knowledge_graph",
                status="HEALTHY",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"triples_count": triples},
            ))
        except Exception as e:
            results.append(SubsystemProbeResult(
                name="knowledge_graph",
                status="DEGRADED",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
                details={"error": str(e)},
            ))

        healthy_count = sum(1 for r in results if r.status == "HEALTHY")
        overall = "HEALTHY" if healthy_count == len(results) else ("DEGRADED" if healthy_count >= len(results) // 2 else "UNHEALTHY")

        return DiagnosticsReport(
            timestamp=time.time(),
            overall_status=overall,
            subsystems_probed=len(results),
            healthy_count=healthy_count,
            results=results,
        )
