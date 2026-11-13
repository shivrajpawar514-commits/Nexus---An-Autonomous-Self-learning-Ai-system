"""State definitions for the Agent LangGraph Workflow."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agent.planner import Plan
from agent.executor import ExecutionResult, ReActStep
from agent.verifier import Verdict
from agent.reflector import ReflectionResult


class AgentState(BaseModel):
    goal: str
    expected_output: Optional[Any] = None
    use_memory: bool = True
    use_reflection: bool = True
    
    # Memory and retrieval state
    retrieved_lessons: List[str] = Field(default_factory=list)
    retrieved_skills: List[str] = Field(default_factory=list)
    
    # Execution and verification state
    plan: Optional[Plan] = None
    execution: Optional[ExecutionResult] = None
    verdict: Optional[Verdict] = None
    reflection: Optional[ReflectionResult] = None
    
    # Loop tracking
    iteration: int = 0
    max_retries: int = 2
    status: str = "pending"  # pending, executing, verified, failed, completed
    error: Optional[str] = None

