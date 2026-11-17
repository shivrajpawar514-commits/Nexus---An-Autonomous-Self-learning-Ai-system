"""Subagent delegation engine allowing hierarchical task partitioning and isolated execution."""

from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agent.llm import LLMInterface
from agent.executor import Executor, ExecutionResult
from tools.base import tool, ToolResult, PermissionTier, ToolRegistry, get_default_registry


class DelegationTask(BaseModel):
    subgoal: str
    allowed_tools: Optional[List[str]] = None
    token_budget: int = 10000
    max_steps: int = 5


class DelegationResult(BaseModel):
    subgoal: str
    ok: bool
    answer: str
    tokens_used: int = 0
    total_steps: int = 0
    duration_sec: float = 0.0
    error: Optional[str] = None


class SubagentDelegator:
    """Manages the creation and isolated execution of specialist subagents."""

    def __init__(self, llm: LLMInterface, tool_registry: Optional[ToolRegistry] = None):
        self.llm = llm
        self.parent_registry = tool_registry or get_default_registry()

    def _create_isolated_registry(self, allowed_tools: Optional[List[str]]) -> ToolRegistry:
        isolated = ToolRegistry()
        for t in self.parent_registry.list_tools():
            if allowed_tools is None or t.name in allowed_tools:
                isolated.register(t)
        return isolated

    def delegate(self, task: DelegationTask) -> DelegationResult:
        """Executes a subgoal inside an isolated subagent sandbox with budget partitioning."""
        start_time = time.time()
        isolated_registry = self._create_isolated_registry(task.allowed_tools)

        sub_executor = Executor(
            llm=self.llm,
            tool_registry=isolated_registry,
            max_steps=task.max_steps,
            token_budget=task.token_budget,
            timeout_seconds=30.0,
        )

        res: ExecutionResult = sub_executor.run(goal=task.subgoal)

        return DelegationResult(
            subgoal=task.subgoal,
            ok=res.ok,
            answer=res.answer,
            tokens_used=res.total_tokens,
            total_steps=res.total_steps,
            duration_sec=time.time() - start_time,
            error=res.error,
        )

    def delegate_batch(self, tasks: List[DelegationTask]) -> List[DelegationResult]:
        """Sequentially or concurrently executes a batch of delegated tasks."""
        return [self.delegate(t) for t in tasks]
