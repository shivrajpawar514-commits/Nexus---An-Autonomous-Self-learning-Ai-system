"""Voyager-style skill library storing, testing, and promoting verified functions."""

from __future__ import annotations
import inspect
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from memory.semantic import SimpleVectorIndex
from tools.base import Tool, ToolRegistry, PermissionTier, get_default_registry


class SkillEntry(BaseModel):
    name: str
    description: str
    code: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    test_code: str = ""
    success_count: int = 0
    failure_count: int = 0
    is_verified: bool = False


class SkillLibrary:
    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.skills: Dict[str, SkillEntry] = {}
        self.tool_registry = tool_registry or get_default_registry()
        self.index = SimpleVectorIndex()
        self.doc_vectors: Dict[str, Any] = {}

    def add_skill(
        self,
        name: str,
        description: str,
        code: str,
        test_code: str = "",
        input_schema: Optional[Dict[str, Any]] = None,
    ) -> SkillEntry:
        """Adds a candidate skill to the library."""
        entry = SkillEntry(
            name=name,
            description=description,
            code=code,
            test_code=test_code,
            input_schema=input_schema or {},
        )
        self.skills[name] = entry
        full_text = f"{name}: {description}"
        self.doc_vectors[name] = self.index.get_or_create_vector(full_text)
        return entry

    def verify_skill(self, name: str) -> Optional[Callable]:
        """Executes the skill's unit tests in Python and marks verified if passed."""
        skill = self.skills.get(name)
        if not skill:
            return None

        exec_scope: Dict[str, Any] = {}
        try:
            # 1. Exec function definition
            exec(skill.code, exec_scope)
            fn = exec_scope.get(skill.name)
            if not callable(fn):
                return None

            # 2. Exec unit test if present
            if skill.test_code:
                exec(skill.test_code, exec_scope)

            skill.is_verified = True
            return fn
        except Exception:
            skill.is_verified = False
            return None

    def verify_and_promote(self, name: str) -> bool:
        """Verifies the skill against its test suite."""
        return self.verify_skill(name) is not None

    def record_usage(self, name: str, success: bool):
        if name in self.skills:
            if success:
                self.skills[name].success_count += 1
            else:
                self.skills[name].failure_count += 1

    def retrieve_skills(self, query: str, k: int = 3) -> List[SkillEntry]:
        if not self.skills:
            return []

        scored = []
        for name, skill in self.skills.items():
            vec = self.doc_vectors.get(name)
            sim = self.index.compute_similarity(query, vec) if vec is not None else 0.0
            # Prioritize verified skills
            bonus = 0.3 if skill.is_verified else 0.0
            scored.append((sim + bonus, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [skill for _, skill in scored[:k]]

