"""Comprehensive unit tests for the SystemDiagnostics subsystem health probe engine."""

import time
import pytest
from unittest.mock import MagicMock
from dashboard.diagnostics import SystemDiagnostics, SubsystemProbeResult, DiagnosticsReport


class TestDiagnosticsModels:
    """Tests for Pydantic data schemas in diagnostics module."""

    def test_probe_result_defaults(self):
        result = SubsystemProbeResult(name="test_subsystem")
        assert result.name == "test_subsystem"
        assert result.status == "HEALTHY"
        assert result.latency_ms == 0.0
        assert result.details == {}

    def test_diagnostics_report_defaults(self):
        report = DiagnosticsReport()
        assert report.overall_status == "HEALTHY"
        assert report.subsystems_probed == 0
        assert report.healthy_count == 0
        assert report.results == []
        assert report.timestamp > 0.0


class TestSystemDiagnosticsEngine:
    """Tests for SystemDiagnostics probe logic across subsystem contexts."""

    def test_probe_all_empty_context(self):
        """When context has no subsystems, probes should gracefully produce reports."""
        diag = SystemDiagnostics(server_context={})
        report = diag.probe_all()

        assert isinstance(report, DiagnosticsReport)
        assert report.subsystems_probed == 7
        names = [r.name for r in report.results]
        assert "memory_hierarchy" in names
        assert "virtual_filesystem" in names
        assert "sandbox_watchdog" in names
        assert "policy_engine" in names
        assert "model_router" in names
        assert "swarm_blackboard" in names
        assert "knowledge_graph" in names

    def test_probe_all_fully_healthy_subsystems(self):
        """Mock all 7 operational subsystems returning healthy metrics."""
        mock_orch = MagicMock()
        mock_orch.episodic_memory.get_summary_stats.return_value = {"total_episodes": 42}
        mock_orch.semantic_memory.items = [MagicMock(), MagicMock()]

        mock_wm = MagicMock()
        mock_wm.list_tenants.return_value = ["tenant-1", "tenant-2"]

        mock_watchdog = MagicMock()
        mock_watchdog.get_status.return_value = {
            "total_monitored_tools": 5,
            "breakers": {
                "bash": {"state": "CLOSED", "failure_count": 0},
                "python": {"state": "CLOSED", "failure_count": 0},
            },
        }

        mock_pe = MagicMock()
        mock_pe.list_policies.return_value = ["policy_1", "policy_2"]

        mock_mr = MagicMock()
        mock_mr.get_tier_info.return_value = {"FAST": {}, "STANDARD": {}, "REASONING": {}}

        mock_bb = MagicMock()
        mock_bb.count.return_value = 15

        mock_kg = MagicMock()
        mock_kg.count.return_value = 120

        ctx = {
            "orchestrator": mock_orch,
            "workspace_manager": mock_wm,
            "watchdog": mock_watchdog,
            "policy_engine": mock_pe,
            "model_router": mock_mr,
            "blackboard": mock_bb,
            "knowledge_graph": mock_kg,
        }

        diag = SystemDiagnostics(server_context=ctx)
        report = diag.probe_all()

        assert report.overall_status == "HEALTHY"
        assert report.subsystems_probed == 7
        assert report.healthy_count == 7
        for probe in report.results:
            assert probe.status == "HEALTHY"
            assert probe.latency_ms >= 0.0

    def test_probe_watchdog_circuit_breaker_tripped(self):
        """When a circuit breaker is in OPEN state, watchdog probe status becomes DEGRADED."""
        mock_watchdog = MagicMock()
        mock_watchdog.get_status.return_value = {
            "total_monitored_tools": 2,
            "breakers": {
                "unsafe_tool": {"state": "OPEN", "failure_count": 5},
                "safe_tool": {"state": "CLOSED", "failure_count": 0},
            },
        }

        ctx = {
            "watchdog": mock_watchdog,
        }

        diag = SystemDiagnostics(server_context=ctx)
        report = diag.probe_all()

        watchdog_probe = next(r for r in report.results if r.name == "sandbox_watchdog")
        assert watchdog_probe.status == "DEGRADED"
        assert "unsafe_tool" in watchdog_probe.details["tripped_breakers"]
        assert report.overall_status in ["HEALTHY", "DEGRADED"]

    def test_probe_handles_subsystem_exception(self):
        """If a subsystem call raises an unexpected exception, it is caught as DEGRADED or UNHEALTHY."""
        broken_orch = MagicMock()
        broken_orch.episodic_memory.get_summary_stats.side_effect = RuntimeError("Database locked")

        broken_watchdog = MagicMock()
        broken_watchdog.get_status.side_effect = ValueError("Corrupt watchdog state")

        ctx = {
            "orchestrator": broken_orch,
            "watchdog": broken_watchdog,
        }

        diag = SystemDiagnostics(server_context=ctx)
        report = diag.probe_all()

        mem_probe = next(r for r in report.results if r.name == "memory_hierarchy")
        assert mem_probe.status == "DEGRADED"
        assert "Database locked" in mem_probe.details["error"]

        wd_probe = next(r for r in report.results if r.name == "sandbox_watchdog")
        assert wd_probe.status == "UNHEALTHY"
        assert "Corrupt watchdog state" in wd_probe.details["error"]
