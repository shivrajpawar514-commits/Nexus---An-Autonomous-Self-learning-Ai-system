"""Role-Based Access Control (RBAC) and tenancy management."""

from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Role(str, Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    RESEARCHER = "RESEARCHER"
    READONLY = "READONLY"


# Hierarchical permission weights
ROLE_WEIGHTS: Dict[Role, int] = {
    Role.ADMIN: 400,
    Role.OPERATOR: 300,
    Role.RESEARCHER: 200,
    Role.READONLY: 100,
}


class Subject(BaseModel):
    subject_id: str
    role: Role = Role.OPERATOR
    tenant_id: str = "default"


class RBACManager:
    """Manages role assignments and enforces minimum required privilege tiers."""

    def __init__(self):
        self._subjects: Dict[str, Subject] = {}

    def assign_role(self, subject_id: str, role: Role | str, tenant_id: str = "default") -> Subject:
        if isinstance(role, str):
            role = Role(role.upper())
        subj = Subject(subject_id=subject_id, role=role, tenant_id=tenant_id)
        self._subjects[subject_id] = subj
        return subj

    def get_role(self, subject_id: str) -> Role:
        if subject_id in self._subjects:
            return self._subjects[subject_id].role
        return Role.READONLY

    def check_permission(self, subject_id: str, minimum_required_role: Role | str) -> bool:
        if isinstance(minimum_required_role, str):
            minimum_required_role = Role(minimum_required_role.upper())
        subject_role = self.get_role(subject_id)
        return ROLE_WEIGHTS.get(subject_role, 0) >= ROLE_WEIGHTS.get(minimum_required_role, 0)
