"""Unit tests for plugin lifecycle, audit logger, and cost tracking plugins."""

import pytest
from plugins.base import PluginInterface, PluginManifest, PluginContext
from plugins.manager import PluginManager
from plugins.builtin.audit_logger import AuditLoggerPlugin
from plugins.builtin.cost_tracker import CostTrackerPlugin
from tools.base import ToolRegistry


class SampleVetoPlugin(PluginInterface):
    def __init__(self):
        manifest = PluginManifest(name="veto_plugin", description="Blocks dangerous actions")
        super().__init__(manifest)

    def on_pre_execute(self, action_name: str, args: dict):
        if action_name == "delete_all":
            return False, "Deletion is prohibited"
        return True, None


def test_plugin_registration_and_listing():
    pm = PluginManager()
    audit = AuditLoggerPlugin()
    cost = CostTrackerPlugin()

    pm.register(audit)
    pm.register(cost)

    plugins = pm.list_plugins()
    assert len(plugins) == 2
    names = [p["name"] for p in plugins]
    assert "audit_logger" in names
    assert "cost_tracker" in names


def test_plugin_enable_disable_and_reload():
    pm = PluginManager()
    audit = AuditLoggerPlugin()
    pm.register(audit)

    assert audit.is_enabled is True
    pm.disable("audit_logger")
    assert audit.is_enabled is False

    pm.enable("audit_logger")
    assert audit.is_enabled is True

    assert pm.reload("audit_logger") is True


def test_plugin_pre_execute_veto():
    pm = PluginManager()
    veto = SampleVetoPlugin()
    pm.register(veto)

    # Allowed action
    allowed, _ = pm.trigger_pre_execute("calculate", {"expression": "2+2"})
    assert allowed is True

    # Blocked action
    allowed, reason = pm.trigger_pre_execute("delete_all", {})
    assert allowed is False
    assert "Deletion is prohibited" in reason

    # When disabled, veto does not trigger
    pm.disable("veto_plugin")
    allowed, _ = pm.trigger_pre_execute("delete_all", {})
    assert allowed is True


def test_audit_logger_captures_executions():
    audit = AuditLoggerPlugin()
    pm = PluginManager()
    pm.register(audit)

    pm.trigger_post_execute("calculate", {"expr": "10*5"}, 50, 0.002)
    entries = audit.get_entries()
    assert len(entries) == 1
    assert entries[0]["action_name"] == "calculate"
    assert entries[0]["result_str"] == "50"


def test_cost_tracker_budget_tripwire():
    cost = CostTrackerPlugin(max_budget_usd=0.01)
    pm = PluginManager()
    pm.register(cost)

    # Initial under budget
    allowed, _ = pm.trigger_pre_execute("calculate", {})
    assert allowed is True

    # Exceed budget
    cost.record_usage(prompt_tokens=5000, completion_tokens=3000)
    metrics = cost.get_metrics()
    assert metrics["total_spend_usd"] > 0.01

    # Now pre-execute trips
    allowed, reason = pm.trigger_pre_execute("calculate", {})
    assert allowed is False
    assert "Budget quota exceeded" in reason
