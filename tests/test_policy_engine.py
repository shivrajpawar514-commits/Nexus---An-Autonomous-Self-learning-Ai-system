"""Unit tests for Declarative Policy Engine, RBAC tiers, and Security Guardrails."""

import pytest
from safety.policy_engine import PolicyEngine, ActionPolicy, EffectType
from safety.rbac import RBACManager, Role
from safety.guardrails import SecurityGuardrail


def test_policy_engine_allow_and_deny_wildcard():
    pe = PolicyEngine()
    pe.add_policy(
        ActionPolicy(
            id="allow_read",
            name="Allow file reading",
            effect=EffectType.ALLOW,
            actions=["read_file", "files:*"],
        )
    )
    pe.add_policy(
        ActionPolicy(
            id="deny_root",
            name="Deny root writes",
            effect=EffectType.DENY,
            actions=["write_file", "delete_file"],
            resources=["/etc/*", "/root/*"],
        )
    )

    # Allowed read
    allowed, _ = pe.evaluate("read_file", "/home/user/doc.txt")
    assert allowed is True

    # Denied root write
    allowed, reason = pe.evaluate("delete_file", "/etc/passwd")
    assert allowed is False
    assert "Denied by policy" in reason


def test_policy_engine_argument_regex_condition():
    pe = PolicyEngine()
    pe.add_policy(
        ActionPolicy(
            id="block_sql_drop",
            name="Block DROP statements in queries",
            effect=EffectType.DENY,
            actions=["execute_sql"],
            conditions={"query": r"\bDROP\s+TABLE\b"},
        )
    )

    # Harmless query passes
    allowed, _ = pe.evaluate("execute_sql", args={"query": "SELECT * FROM users;"})
    assert allowed is True

    # Malicious DROP query blocked
    allowed, reason = pe.evaluate("execute_sql", args={"query": "DROP TABLE users;"})
    assert allowed is False
    assert "Block DROP statements" in reason


def test_rbac_role_hierarchy():
    rbac = RBACManager()
    rbac.assign_role("alice", Role.ADMIN)
    rbac.assign_role("bob", Role.RESEARCHER)

    assert rbac.check_permission("alice", Role.OPERATOR) is True
    assert rbac.check_permission("bob", Role.ADMIN) is False
    assert rbac.check_permission("bob", Role.RESEARCHER) is True


def test_security_guardrail_integration():
    pe = PolicyEngine()
    pe.add_policy(ActionPolicy(id="deny_rm", name="Deny rm", effect=EffectType.DENY, actions=["rm_rf"]))
    rbac = RBACManager()
    rbac.assign_role("charlie", Role.READONLY)

    guard = SecurityGuardrail(policy_engine=pe, rbac_manager=rbac)

    # Readonly user cannot perform operator actions
    allowed, reason = guard.validate_execution("write_file", subject_id="charlie")
    assert allowed is False
    assert "lacks OPERATOR role" in reason

    # Explicit deny trumps
    rbac.assign_role("admin_user", Role.ADMIN)
    allowed, reason = guard.validate_execution("rm_rf", subject_id="admin_user")
    assert allowed is False
    assert "Denied by policy" in reason
