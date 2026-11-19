"""Declarative Policy Engine for autonomous agent zero-trust governance."""

from __future__ import annotations
import fnmatch
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class EffectType(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class ActionPolicy(BaseModel):
    id: str
    name: str
    effect: EffectType
    actions: List[str] = Field(description="Action names or wildcards, e.g. ['files:*', 'calculate']")
    resources: List[str] = Field(default_factory=lambda: ["*"])
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Constraints on arguments, e.g. regex")


class PolicyEngine:
    """Evaluates fine-grained declarative security policies with explicit DENY precedence."""

    def __init__(self, default_effect: EffectType = EffectType.ALLOW):
        self.default_effect = default_effect
        self._policies: Dict[str, ActionPolicy] = {}

    def add_policy(self, policy: ActionPolicy) -> None:
        self._policies[policy.id] = policy

    def remove_policy(self, policy_id: str) -> bool:
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False

    def list_policies(self) -> List[Dict[str, Any]]:
        return [p.model_dump() for p in self._policies.values()]

    def evaluate(
        self,
        action: str,
        resource: str = "*",
        args: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """Evaluates whether an action is permitted. Explicit DENY overrides any ALLOW."""
        args = args or {}
        matched_allow = False
        allow_reason = "Default allow"

        for policy in self._policies.values():
            action_matched = any(fnmatch.fnmatch(action, pat) for pat in policy.actions)
            resource_matched = any(fnmatch.fnmatch(resource, pat) for pat in policy.resources)

            if action_matched and resource_matched:
                # Check condition constraints (e.g. regex on args)
                conditions_met = True
                if policy.conditions:
                    for arg_key, pattern in policy.conditions.items():
                        arg_val = str(args.get(arg_key, ""))
                        if not re.search(str(pattern), arg_val, re.IGNORECASE):
                            conditions_met = False
                            break

                if conditions_met:
                    if policy.effect == EffectType.DENY:
                        return False, f"Denied by policy '{policy.name}' ({policy.id})"
                    elif policy.effect == EffectType.ALLOW:
                        matched_allow = True
                        allow_reason = f"Allowed by policy '{policy.name}' ({policy.id})"

        if matched_allow:
            return True, allow_reason

        if self.default_effect == EffectType.ALLOW:
            return True, "Default allow"
        return False, "Default deny: no matching allow policy"
