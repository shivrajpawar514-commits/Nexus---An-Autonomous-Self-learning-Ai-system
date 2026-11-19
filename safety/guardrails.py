"""Security Guardrail enforcing RBAC and declarative policies on agent executions."""

from __future__ import annotations
from typing import Any, Dict, Optional, Tuple
from safety.policy_engine import PolicyEngine, ActionPolicy, EffectType
from safety.rbac import RBACManager, Role


class SecurityGuardrail:
    """Unified security barrier checking RBAC roles and declarative action policies."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        rbac_manager: Optional[RBACManager] = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.rbac_manager = rbac_manager or RBACManager()

    def validate_execution(
        self,
        action_name: str,
        args: Optional[Dict[str, Any]] = None,
        subject_id: str = "default",
        resource: str = "*",
    ) -> Tuple[bool, str]:
        """Verify role entitlement and policy clearance before executing a tool."""
        # 1. READONLY subjects cannot run modifying actions
        if action_name not in ["calculate", "read_file", "search_web"]:
            if not self.rbac_manager.check_permission(subject_id, Role.OPERATOR):
                return False, f"Subject '{subject_id}' lacks OPERATOR role required for action '{action_name}'"

        # 2. Check declarative policies
        allowed, reason = self.policy_engine.evaluate(action=action_name, resource=resource, args=args)
        return allowed, reason
