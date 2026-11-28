"""Live Web Dashboard Server for Autonomous Self-Learning Agent System."""

from __future__ import annotations
import json
import os
import sys
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Any, Dict, List, Optional

from agent.llm import MockLLM
from agent.orchestrator import Orchestrator
from agent.blackboard import Blackboard, BlackboardMessage, MessageType
from agent.consensus import ConsensusEngine, ConsensusVote, VoteType
from plugins.manager import PluginManager
from plugins.builtin.audit_logger import AuditLoggerPlugin
from plugins.builtin.cost_tracker import CostTrackerPlugin
from eval.run import evaluate_split, run_learning_cycle
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.skills import SkillLibrary
from memory.knowledge_graph import KnowledgeGraph
from safety.policy_engine import PolicyEngine, ActionPolicy, EffectType
from sandbox.watchdog import SandboxWatchdog
from sandbox.tenant import TenantWorkspaceManager, TenantConfig
from routing import ModelRouter, ComplexityClassifier
from evolution import StrategyManager, EvolutionaryTournament
from telemetry.context import get_global_tracer
from telemetry.exporter import TraceExporter
from tools.base import get_default_registry
from tools.python_sandbox import run_python
from tools.calculator import calculate


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


# Global shared instances
global_orchestrator: Optional[Orchestrator] = None
global_blackboard: Optional[Blackboard] = None
global_consensus: Optional[ConsensusEngine] = None
global_plugin_manager: Optional[PluginManager] = None
global_knowledge_graph: Optional[KnowledgeGraph] = None
global_policy_engine: Optional[PolicyEngine] = None
global_watchdog: Optional[SandboxWatchdog] = None
global_model_router: Optional[ModelRouter] = None
global_strategy_manager: Optional[StrategyManager] = None
global_workspace_manager: Optional[TenantWorkspaceManager] = None


def get_workspace_manager() -> TenantWorkspaceManager:
    global global_workspace_manager
    if global_workspace_manager is None:
        root = Path(__file__).resolve().parent.parent / "sandbox_workspace"
        global_workspace_manager = TenantWorkspaceManager(root_dir=root)
        global_workspace_manager.register_tenant(TenantConfig(tenant_id="default"))
    return global_workspace_manager


def get_strategy_manager() -> StrategyManager:
    global global_strategy_manager
    if global_strategy_manager is None:
        global_strategy_manager = StrategyManager()
    return global_strategy_manager


def get_model_router() -> ModelRouter:
    global global_model_router
    if global_model_router is None:
        global_model_router = ModelRouter()
    return global_model_router


def get_watchdog() -> SandboxWatchdog:
    global global_watchdog
    if global_watchdog is None:
        global_watchdog = SandboxWatchdog(failure_threshold=3, recovery_timeout_sec=30.0)
    return global_watchdog


def get_policy_engine() -> PolicyEngine:
    global global_policy_engine
    if global_policy_engine is None:
        global_policy_engine = PolicyEngine()
        # Seed default protection policy
        global_policy_engine.add_policy(
            ActionPolicy(
                id="default_protection",
                name="Block System Shutdown",
                effect=EffectType.DENY,
                actions=["system_shutdown", "wipe_database"],
            )
        )
    return global_policy_engine


def get_knowledge_graph() -> KnowledgeGraph:
    global global_knowledge_graph
    if global_knowledge_graph is None:
        global_knowledge_graph = KnowledgeGraph()
        # Seed core architecture relationships
        global_knowledge_graph.add_triple("ReActExecutor", "USES", "ToolRegistry", 1.0)
        global_knowledge_graph.add_triple("PythonSandbox", "PREVENTS", "FilesystemEscape", 0.95)
        global_knowledge_graph.add_triple("SemanticMemory", "PROVIDES", "ReflectedLessons", 0.9)
    return global_knowledge_graph


def get_plugin_manager() -> PluginManager:
    global global_plugin_manager
    if global_plugin_manager is None:
        global_plugin_manager = PluginManager(tool_registry=get_default_registry())
        global_plugin_manager.register(AuditLoggerPlugin())
        global_plugin_manager.register(CostTrackerPlugin())
    return global_plugin_manager


def get_orchestrator() -> Orchestrator:
    global global_orchestrator
    if global_orchestrator is None:
        llm = MockLLM()
        pm = get_plugin_manager()
        wd = get_watchdog()
        global_orchestrator = Orchestrator(llm=llm, plugin_manager=pm, watchdog=wd)
    return global_orchestrator


def get_blackboard() -> Blackboard:
    global global_blackboard
    if global_blackboard is None:
        global_blackboard = Blackboard()
    return global_blackboard


def get_consensus() -> ConsensusEngine:
    global global_consensus
    if global_consensus is None:
        global_consensus = ConsensusEngine()
    return global_consensus


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "AutonomousAgentDashboard/1.0"

    def log_message(self, format, *args):
        # Quiet standard HTTP access logs
        sys.stderr.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {args[0]} {args[1]} -> {args[2]}\n")

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_content: str, status: int = 200):
        body = html_content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        orch = get_orchestrator()

        if path == "/" or path == "/index.html":
            static_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
            if os.path.exists(static_file):
                with open(static_file, "r", encoding="utf-8") as f:
                    self._send_html(f.read())
            else:
                self._send_html("<h1>Autonomous Agent Dashboard - index.html not found</h1>", status=404)
            return

        if path == "/privacy" or path == "/privacy.html":
            static_file = os.path.join(os.path.dirname(__file__), "static", "privacy.html")
            if os.path.exists(static_file):
                with open(static_file, "r", encoding="utf-8") as f:
                    self._send_html(f.read())
            else:
                self._send_html("<h1>Privacy Policy not found</h1>", status=404)
            return

        if path == "/terms" or path == "/terms.html":
            static_file = os.path.join(os.path.dirname(__file__), "static", "terms.html")
            if os.path.exists(static_file):
                with open(static_file, "r", encoding="utf-8") as f:
                    self._send_html(f.read())
            else:
                self._send_html("<h1>Terms of Service not found</h1>", status=404)
            return

        if path == "/favicon.ico":
            svg = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='#2563eb'><path d='M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5'/></svg>"""
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(svg)))
            self.end_headers()
            self.wfile.write(svg.encode("utf-8"))
            return

        # API: Real-time SSE Stream Heartbeat & Event Channel
        if path == "/api/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                init_data = json.dumps({"type": "connected", "timestamp": time.time(), "status": "active"})
                self.wfile.write(f"data: {init_data}\n\n".encode("utf-8"))
                self.wfile.flush()
            except Exception:
                pass
            return

        # API: Prometheus-compatible Metrics Scraper
        if path == "/metrics":
            stats = orch.episodic_memory.get_summary_stats()
            conn = orch.episodic_memory._get_connection()
            c = conn.cursor()
            c.execute("SELECT passed, count(*) FROM episodes GROUP BY passed")
            passed_dist = {bool(row[0]): row[1] for row in c.fetchall()}
            c.execute("SELECT SUM(total_tokens), SUM(duration_sec) FROM episodes")
            totals = c.fetchone()
            total_tokens = totals[0] or 0
            total_duration = totals[1] or 0.0
            conn.close()

            passed_count = passed_dist.get(True, 0)
            failed_count = passed_dist.get(False, 0)
            total_episodes = passed_count + failed_count

            prom_text = (
                "# HELP nexus_tasks_total Total tasks processed\n"
                "# TYPE nexus_tasks_total counter\n"
                f"nexus_tasks_total {total_episodes}\n\n"
                "# HELP nexus_tasks_passed_total Total successfully verified tasks\n"
                "# TYPE nexus_tasks_passed_total counter\n"
                f"nexus_tasks_passed_total {passed_count}\n\n"
                "# HELP nexus_tasks_failed_total Total failed tasks\n"
                "# TYPE nexus_tasks_failed_total counter\n"
                f"nexus_tasks_failed_total {failed_count}\n\n"
                "# HELP nexus_token_usage_total Total LLM tokens consumed\n"
                "# TYPE nexus_token_usage_total counter\n"
                f"nexus_token_usage_total {total_tokens}\n\n"
                "# HELP nexus_execution_duration_seconds Total execution time in seconds\n"
                "# TYPE nexus_execution_duration_seconds counter\n"
                f"nexus_execution_duration_seconds {round(total_duration, 3)}\n\n"
                "# HELP nexus_skills_verified_total Total verified Voyager skills\n"
                "# TYPE nexus_skills_verified_total gauge\n"
                f"nexus_skills_verified_total {len(orch.skill_library.skills)}\n"
            )
            body = prom_text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            return

        # API: Telemetry Stats
        if path == "/api/stats":
            stats = orch.episodic_memory.get_summary_stats()
            # Also get distribution of passes and tools
            conn = orch.episodic_memory._get_connection()
            c = conn.cursor()
            c.execute("SELECT passed, count(*) FROM episodes GROUP BY passed")
            passed_dist = {bool(row[0]): row[1] for row in c.fetchall()}
            
            c.execute("SELECT count(*) FROM episodes")
            total_count = c.fetchone()[0] or 0

            # Estimate total token count
            c.execute("SELECT SUM(total_tokens), SUM(duration_sec) FROM episodes")
            totals = c.fetchone()
            total_tokens = totals[0] or 0
            total_duration = totals[1] or 0.0
            conn.close()

            resp = {
                "summary": stats,
                "passed_count": passed_dist.get(True, 0),
                "failed_count": passed_dist.get(False, 0),
                "total_episodes": total_count,
                "total_tokens": total_tokens,
                "total_duration_sec": round(total_duration, 2),
                "skills_count": len(orch.skill_library.skills),
                "lessons_count": len(orch.semantic_memory.lessons),
            }
            self._send_json(resp)
            return

        # API: Episodes List
        if path == "/api/episodes":
            limit = int(query.get("limit", [50])[0])
            status_filter = query.get("status", ["all"])[0]

            conn = orch.episodic_memory._get_connection()
            c = conn.cursor()
            
            if status_filter == "passed":
                c.execute("SELECT id, goal, passed, total_steps, total_tokens, duration_sec, timestamp FROM episodes WHERE passed = 1 ORDER BY id DESC LIMIT ?", (limit,))
            elif status_filter == "failed":
                c.execute("SELECT id, goal, passed, total_steps, total_tokens, duration_sec, timestamp FROM episodes WHERE passed = 0 ORDER BY id DESC LIMIT ?", (limit,))
            else:
                c.execute("SELECT id, goal, passed, total_steps, total_tokens, duration_sec, timestamp FROM episodes ORDER BY id DESC LIMIT ?", (limit,))

            rows = c.fetchall()
            conn.close()

            episodes = [
                {
                    "id": r[0],
                    "goal": r[1],
                    "passed": bool(r[2]),
                    "total_steps": r[3],
                    "total_tokens": r[4],
                    "duration_sec": r[5],
                    "timestamp": r[6],
                }
                for r in rows
            ]
            self._send_json({"episodes": episodes})
            return

        # API: Memory Clusters for 2D Visualization
        if path == "/api/clusters":
            items = list(orch.semantic_memory.items.values())
            nodes = []
            for idx, item in enumerate(items):
                # Deterministic pseudo-coordinates from item hash for 2D embedding space
                h = hash(item.rule)
                x = ((h % 1000) / 1000.0) * 100
                y = (((h // 1000) % 1000) / 1000.0) * 100
                nodes.append({
                    "id": item.id,
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "label": item.rule[:35] + "...",
                    "importance": item.importance,
                    "usefulness": round(item.usefulness, 3),
                })
            self._send_json({"clusters": nodes, "count": len(nodes)})
            return

        # API: Blackboard Swarm Messages
        if path == "/api/blackboard/messages":
            bb = get_blackboard()
            topic_filter = query.get("topic", [None])[0]
            limit_val = int(query.get("limit", [50])[0])
            msgs = bb.get_messages(topic=topic_filter, limit=limit_val)
            self._send_json({"messages": [m.model_dump() for m in msgs], "count": len(msgs)})
            return

        # API: Consensus Status
        if path == "/api/consensus/status":
            engine = get_consensus()
            bb = get_blackboard()
            self._send_json({
                "engine": "ConsensusEngine",
                "default_threshold": engine.default_threshold,
                "total_blackboard_messages": bb.count(),
            })
            return

        # API: Installed Plugins List
        if path == "/api/plugins":
            pm = get_plugin_manager()
            self._send_json({"plugins": pm.list_plugins()})
            return

        # API: Knowledge Graph Triples & Visualization
        if path == "/api/knowledge-graph":
            kg = get_knowledge_graph()
            self._send_json(kg.export_graph_json())
            return

        # API: Declarative Security Policies
        if path == "/api/policies":
            pe = get_policy_engine()
            self._send_json({"policies": pe.list_policies()})
            return

        # API: Distributed Traces List
        if path == "/api/traces":
            exporter = TraceExporter(get_global_tracer())
            self._send_json({"traces": exporter.list_traces()})
            return

        # API: Trace Waterfall Tree
        if path.startswith("/api/traces/"):
            trace_id = path.split("/")[-1]
            exporter = TraceExporter(get_global_tracer())
            self._send_json(exporter.get_waterfall(trace_id))
            return

        # API: Sandbox Watchdog Circuit Breakers
        if path == "/api/watchdog/status":
            self._send_json(get_watchdog().get_status())
            return

        # API: Model Tiers and Routing Configuration
        if path == "/api/routing/models":
            self._send_json({"tiers": get_model_router().get_tier_info()})
            return

        # API: Strategy Evolution Status
        if path == "/api/evolution/status":
            self._send_json(get_strategy_manager().get_status())
            return

        # API: Virtual Filesystem Overlays Status
        if path == "/api/vfs/status":
            self._send_json({"tenants": get_workspace_manager().list_tenants()})
            return

        # API: Single Episode Details
        if path.startswith("/api/episodes/"):
            try:
                ep_id = int(path.split("/")[-1])
            except ValueError:
                self._send_json({"error": "Invalid episode ID"}, status=400)
                return

            conn = orch.episodic_memory._get_connection()
            c = conn.cursor()
            c.execute("SELECT id, goal, plan_json, trajectory_json, passed, total_steps, total_tokens, duration_sec, timestamp FROM episodes WHERE id = ?", (ep_id,))
            row = c.fetchone()
            conn.close()

            if not row:
                self._send_json({"error": "Episode not found"}, status=404)
                return

            self._send_json({
                "id": row[0],
                "goal": row[1],
                "plan": json.loads(row[2]) if row[2] else {},
                "trajectory": json.loads(row[3]) if row[3] else [],
                "passed": bool(row[4]),
                "total_steps": row[5],
                "total_tokens": row[6],
                "duration_sec": row[7],
                "timestamp": row[8],
            })
            return

        # API: Semantic Lessons
        if path == "/api/lessons":
            lessons_data = [
                {
                    "id": l.id,
                    "situation": l.situation,
                    "what_happened": l.what_happened,
                    "root_cause": l.root_cause,
                    "rule": l.rule,
                    "confidence": l.confidence,
                    "trust_weight": l.trust_weight,
                    "use_count": l.use_count,
                    "created_at": l.created_at,
                }
                for l in orch.semantic_memory.lessons
            ]
            self._send_json({"lessons": lessons_data})
            return

        # API: Skills in Library
        if path == "/api/skills":
            skills_data = [
                {
                    "name": s.name,
                    "description": s.description,
                    "code": s.code,
                    "test_code": s.test_code,
                    "is_verified": s.is_verified,
                    "success_count": s.success_count,
                    "fail_count": s.fail_count,
                }
                for s in orch.skill_library.skills.values()
            ]
            self._send_json({"skills": skills_data})
            return

        # API: Tools List
        if path == "/api/tools":
            tools_data = [
                {
                    "name": t.name,
                    "description": t.description,
                    "permission": t.permission.value if hasattr(t.permission, "value") else str(t.permission),
                    "parameters": t.parameters_schema,
                }
                for t in orch.tool_registry.list_tools()
            ]
            self._send_json({"tools": tools_data})
            return

        # API: Export Telemetry
        if path == "/api/export":
            conn = orch.episodic_memory._get_connection()
            c = conn.cursor()
            c.execute("SELECT id, goal, plan_json, trajectory_json, passed, total_steps, total_tokens, duration_sec, timestamp FROM episodes ORDER BY id ASC")
            rows = c.fetchall()
            conn.close()
            export_data = [
                {
                    "id": r[0],
                    "goal": r[1],
                    "plan": json.loads(r[2]) if r[2] else {},
                    "trajectory": json.loads(r[3]) if r[3] else [],
                    "passed": bool(r[4]),
                    "total_steps": r[5],
                    "total_tokens": r[6],
                    "duration_sec": r[7],
                    "timestamp": r[8],
                }
                for r in rows
            ]
            self._send_json({"exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "count": len(export_data), "episodes": export_data})
            return

        self._send_json({"error": "Not Found"}, status=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(post_body)
        except Exception:
            payload = {}

        orch = get_orchestrator()

        # API: Run Task Live
        if path == "/api/run":
            goal = payload.get("goal", "").strip()
            if not goal:
                self._send_json({"error": "Goal is required"}, status=400)
                return

            use_memory = payload.get("use_memory", True)
            use_reflection = payload.get("use_reflection", True)

            report = orch.run_task(
                goal=goal,
                use_memory=use_memory,
                use_reflection=use_reflection,
            )

            # Convert TaskRunReport to JSON serializable dict
            trajectory = [
                {
                    "step_index": s.step_index,
                    "thought": s.thought,
                    "action_name": s.action_name,
                    "action_args": s.action_args,
                    "observation": s.observation,
                    "duration_sec": round(s.duration_sec, 3),
                    "tokens_used": s.tokens_used,
                }
                for s in report.execution.trajectory
            ]

            reflection_dict = None
            if report.reflection:
                reflection_dict = {
                    "passed": report.reflection.passed,
                    "summary": report.reflection.summary,
                    "lessons": [
                        {
                            "situation": l.situation,
                            "what_happened": l.what_happened,
                            "root_cause": l.root_cause,
                            "rule": l.rule,
                            "confidence": l.confidence,
                            "trust_weight": l.trust_weight,
                        }
                        for l in report.reflection.lessons
                    ],
                }

            result = {
                "goal": report.goal,
                "passed": report.passed,
                "verdict": {
                    "passed": report.verdict.passed,
                    "score": report.verdict.score,
                    "verifier_tier": report.verdict.verifier_tier,
                    "evidence": report.verdict.evidence,
                    "trust": report.verdict.trust,
                },
                "execution": {
                    "ok": report.execution.ok,
                    "answer": report.execution.answer,
                    "total_steps": report.execution.total_steps,
                    "total_tokens": report.execution.total_tokens,
                    "duration_sec": round(report.execution.duration_sec, 3),
                    "error": report.execution.error,
                    "trajectory": trajectory,
                },
                "plan": {
                    "goal": report.plan.goal,
                    "subtasks": report.plan.subtasks,
                },
                "reflection": reflection_dict,
                "retrieved_lessons": report.retrieved_lessons,
                "retrieved_skills": report.retrieved_skills,
            }
            self._send_json(result)
            return

        # API: Real-time Streaming Task Execution (SSE)
        if path == "/api/stream_task":
            goal = payload.get("goal", "").strip()
            if not goal:
                self._send_json({"error": "Goal cannot be empty"}, status=400)
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            def send_event(event_type: str, data: dict):
                try:
                    payload_str = json.dumps({"event": event_type, "data": data})
                    self.wfile.write(f"data: {payload_str}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    pass

            send_event("start", {"goal": goal})
            report = orch.run_task(goal=goal, use_memory=True, use_reflection=True)
            for step in report.execution.trajectory:
                send_event("step", {
                    "step_index": step.step_index,
                    "thought": step.thought,
                    "action_name": step.action_name,
                    "action_args": step.action_args,
                    "observation": step.observation,
                })
            send_event("verdict", {
                "passed": report.passed,
                "score": report.verdict.score,
                "evidence": report.verdict.evidence,
                "answer": report.execution.answer,
            })
            send_event("complete", {"status": "done"})
            return

        # API: Search Semantic Memory
        if path == "/api/lessons/search":
            query = payload.get("query", "").strip()
            if not query:
                self._send_json({"lessons": []})
                return

            items = orch.semantic_memory.retrieve(query, k=5)
            results = [
                {
                    "id": item.id,
                    "situation": item.situation,
                    "rule": item.rule,
                    "confidence": item.confidence,
                    "trust_weight": item.trust_weight,
                    "root_cause": item.root_cause,
                }
                for item in items
            ]
            self._send_json({"results": results})
            return

        # API: Add & Verify Skill
        if path == "/api/skills/add":
            name = payload.get("name", "").strip()
            description = payload.get("description", "").strip()
            code = payload.get("code", "").strip()
            test_code = payload.get("test_code", "").strip()

            if not name or not code or not test_code:
                self._send_json({"error": "Name, code, and test_code are required"}, status=400)
                return

            orch.skill_library.add_skill(
                name=name,
                description=description,
                code=code,
                test_code=test_code,
            )
            promoted = orch.skill_library.verify_and_promote(name)
            self._send_json({
                "name": name,
                "is_verified": promoted,
                "message": "Skill verified and promoted to tool registry!" if promoted else "Verification failed. Inspect test code.",
            })
            return

        # API: Run Evaluation Split
        if path == "/api/eval":
            split = payload.get("split", "test")
            metrics = evaluate_split(orch, split=split, use_memory=True, use_reflection=False)
            self._send_json({"split": split, "metrics": metrics})
            return

        # API: Interactive Sandbox Playground
        if path == "/api/sandbox/run":
            tool_type = payload.get("type", "python")
            code_or_expr = payload.get("input", "").strip()
            if tool_type == "calculator":
                res = calculate(code_or_expr)
            else:
                res = run_python(code_or_expr)
            self._send_json({
                "ok": res.ok,
                "output": str(res.output) if res.output is not None else "",
                "error": res.error or "",
            })
            return

        # API: Post Message to Blackboard
        if path == "/api/blackboard/post":
            bb = get_blackboard()
            sender = payload.get("sender", "agent")
            topic = payload.get("topic", "general")
            msg_type = payload.get("msg_type", "PROPOSAL")
            data = payload.get("payload", {})
            msg = bb.post(sender=sender, topic=topic, msg_type=msg_type, payload=data)
            self._send_json({"ok": True, "message": msg.model_dump()})
            return

        # API: Evaluate Multi-Agent Consensus
        if path == "/api/consensus/vote":
            engine = get_consensus()
            raw_votes = payload.get("votes", [])
            weights = payload.get("weights", {})
            require_supermajority = payload.get("require_supermajority", False)
            threshold = payload.get("threshold", None)

            votes = [
                ConsensusVote(
                    agent_id=v.get("agent_id", f"agent_{i}"),
                    vote=VoteType(v.get("vote", "APPROVE")),
                    confidence=float(v.get("confidence", 1.0)),
                    reasoning=v.get("reasoning", ""),
                )
                for i, v in enumerate(raw_votes)
            ]
            result = engine.evaluate(
                votes=votes,
                agent_weights=weights,
                threshold=threshold,
                require_supermajority=require_supermajority,
            )
            self._send_json({"ok": True, "result": result.model_dump()})
            return

        # API: Toggle Plugin Enabled State
        if path == "/api/plugins/toggle":
            pm = get_plugin_manager()
            name = payload.get("name", "")
            enable_flag = bool(payload.get("enabled", True))
            if enable_flag:
                success = pm.enable(name)
            else:
                success = pm.disable(name)
            self._send_json({"ok": success, "name": name, "enabled": enable_flag})
            return

        # API: Hot Reload Plugin
        if path == "/api/plugins/reload":
            pm = get_plugin_manager()
            name = payload.get("name", "")
            success = pm.reload(name)
            self._send_json({"ok": success, "name": name})
            return

        # API: Add Security Policy
        if path == "/api/policies":
            pe = get_policy_engine()
            policy = ActionPolicy(
                id=payload.get("id", f"policy_{len(pe._policies)+1}"),
                name=payload.get("name", "Custom Policy"),
                effect=EffectType(payload.get("effect", "ALLOW")),
                actions=payload.get("actions", ["*"]),
                resources=payload.get("resources", ["*"]),
                conditions=payload.get("conditions", {}),
            )
            pe.add_policy(policy)
            self._send_json({"ok": True, "policy": policy.model_dump()})
            return

        # API: Evaluate Policy Dry-Run
        if path == "/api/policies/evaluate":
            pe = get_policy_engine()
            action = payload.get("action", "")
            resource = payload.get("resource", "*")
            args = payload.get("args", {})
            allowed, reason = pe.evaluate(action=action, resource=resource, args=args)
            self._send_json({"allowed": allowed, "reason": reason})
            return

        # API: Reset Sandbox Watchdog Circuit Breakers
        if path == "/api/watchdog/reset":
            get_watchdog().reset_all()
            self._send_json({"ok": True, "message": "Circuit breakers reset"})
            return

        # API: Simulate Semantic Model Routing
        if path == "/api/routing/simulate":
            goal = payload.get("goal", "").strip()
            budget = payload.get("budget", None)
            classifier = ComplexityClassifier()
            assessment = classifier.assess(goal)
            tier_cfg = get_model_router().route(goal, max_budget_usd=budget)
            self._send_json({
                "goal": goal,
                "complexity": assessment.model_dump(),
                "selected_tier": tier_cfg.model_dump(),
            })
            return

        # API: Trigger Prompt Mutation and Strategy Evolution
        if path == "/api/evolution/mutate":
            sm = get_strategy_manager()
            mutated = sm.mutator.mutate(sm.active_chromosome)
            tournament = EvolutionaryTournament()
            metrics = tournament.calculate_fitness(accuracy=1.0, avg_tokens=1100, avg_steps=2.2)
            sm.promote_variant(mutated, metrics=metrics)
            self._send_json({
                "promoted": True,
                "chromosome": mutated.model_dump(),
                "metrics": metrics.model_dump(),
            })
            return

        # API: Commit or Rollback Virtual Filesystem Overlay
        if path == "/api/vfs/commit":
            tenant_id = payload.get("tenant_id", "default")
            action = payload.get("action", "commit")
            wm = get_workspace_manager()
            overlay = wm.get_overlay(tenant_id)
            if action == "rollback":
                affected = overlay.rollback()
            else:
                affected = overlay.commit()
            self._send_json({"ok": True, "tenant_id": tenant_id, "action": action, "files_affected": affected})
            return

        self._send_json({"error": "Not Found"}, status=404)


def run_dashboard(host: str = "127.0.0.1", port: int = 8080):
    server = None
    target_port = port
    for offset in range(10):
        try:
            target_port = port + offset
            server = ThreadedHTTPServer((host, target_port), DashboardHandler)
            break
        except OSError as e:
            if e.errno == 48:  # Address already in use
                continue
            raise

    if server is None:
        print(f"Error: Could not bind to port {port} or next 10 ports. Please specify a different port.")
        sys.exit(1)

    print(f"\n========================================================")
    print(f"  AUTONOMOUS AGENT LIVE DASHBOARD RUNNING")
    print(f"  URL: http://{host}:{target_port}")
    print(f"========================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server...")
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_dashboard(port=port)

