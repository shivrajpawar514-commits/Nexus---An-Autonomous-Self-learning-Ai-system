"""Orchestrator coordinating Plan -> Act -> Observe -> Verify -> Reflect -> Store."""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from agent.llm import LLMInterface
from agent.planner import Planner, Plan
from agent.executor import Executor, ExecutionResult, ReActStep
from agent.verifier import Verifier, Verdict
from agent.reflector import Reflector, ReflectionResult
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.skills import SkillLibrary
from tools.base import ToolRegistry, get_default_registry


class TaskRunReport(BaseModel):
    goal: str
    passed: bool
    verdict: Verdict
    execution: ExecutionResult
    plan: Plan
    reflection: Optional[ReflectionResult] = None
    retrieved_lessons: List[str] = Field(default_factory=list)
    retrieved_skills: List[str] = Field(default_factory=list)


class Orchestrator:
    def __init__(
        self,
        llm: LLMInterface,
        tool_registry: Optional[ToolRegistry] = None,
        episodic_memory: Optional[EpisodicMemory] = None,
        semantic_memory: Optional[SemanticMemory] = None,
        skill_library: Optional[SkillLibrary] = None,
    ):
        self.llm = llm
        self.tool_registry = tool_registry or get_default_registry()
        self.episodic_memory = episodic_memory or EpisodicMemory()
        self.semantic_memory = semantic_memory or SemanticMemory()
        self.skill_library = skill_library or SkillLibrary(tool_registry=self.tool_registry)

        self.planner = Planner(llm=self.llm)
        self.executor = Executor(llm=self.llm, tool_registry=self.tool_registry)
        self.verifier = Verifier(llm=self.llm)
        self.reflector = Reflector(llm=self.llm)

    def run_task(
        self,
        goal: str,
        expected_output: Any = None,
        test_fn: Optional[Callable[[Any], bool]] = None,
        use_memory: bool = True,
        use_reflection: bool = True,
    ) -> TaskRunReport:
        """Runs an end-to-end autonomous task with learning integration."""
        retrieved_lesson_items = []
        retrieved_lessons = []
        retrieved_skills = []

        # 1. Retrieve Lessons and Skills if enabled
        if use_memory:
            retrieved_lesson_items = self.semantic_memory.retrieve(goal, k=5)
            retrieved_lessons = [f"{item.situation}: {item.rule}" for item in retrieved_lesson_items]

            matched_skills = self.skill_library.retrieve_skills(goal, k=3)
            retrieved_skills = [f"{s.name}(): {s.description}" for s in matched_skills]

        # 2. Decompose Goal via Planner
        plan = self.planner.make_plan(
            goal=goal,
            retrieved_lessons=retrieved_lessons,
            retrieved_skills=retrieved_skills,
        )

        # 3. Execute via ReAct Executor
        execution = self.executor.run(
            goal=goal,
            context=f"Plan subtasks: {', '.join(plan.subtasks)}",
            retrieved_lessons=retrieved_lessons,
            retrieved_skills=retrieved_skills,
        )

        # 4. Verify outcome via Verifier Hierarchy
        if test_fn or expected_output is not None:
            verdict = self.verifier.check_programmatic(
                actual_output=execution.answer,
                expected_output=expected_output,
                test_fn=test_fn,
            )
        else:
            verdict = self.verifier.check_llm_judge(goal=goal, output=execution.answer)

        # 5. Record Episode in Episodic Memory
        self.episodic_memory.record_episode(
            goal=goal,
            plan=plan.model_dump() if hasattr(plan, "model_dump") else plan.dict(),
            trajectory=execution.trajectory,
            passed=verdict.passed,
            score=verdict.score,
            total_steps=execution.total_steps,
            total_tokens=execution.total_tokens,
            duration_sec=execution.duration_sec,
        )

        # 6. Reflect and Learn if enabled
        reflection = None
        if use_reflection:
            traj_text = "\n".join(
                f"Step {s.step_index}: Thought: {s.thought} | Action: {s.action_name}({s.action_args}) | Obs: {s.observation}"
                for s in execution.trajectory
            )
            reflection = self.reflector.reflect(
                goal=goal,
                trajectory_str=traj_text,
                verdict=verdict,
            )

            # Store lessons into semantic memory with trust weighting
            for lesson in reflection.lessons:
                self.semantic_memory.add_lesson(lesson)

            # Update past usefulness of retrieved lessons
            if retrieved_lesson_items:
                retrieved_ids = [item.id for item in retrieved_lesson_items]
                self.semantic_memory.update_usefulness(retrieved_ids, passed=verdict.passed)

        return TaskRunReport(
            goal=goal,
            passed=verdict.passed,
            verdict=verdict,
            execution=execution,
            plan=plan,
            reflection=reflection,
            retrieved_lessons=retrieved_lessons,
            retrieved_skills=retrieved_skills,
        )
