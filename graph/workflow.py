"""LangGraph-compatible Workflow Orchestrator for Autonomous AI Agent."""

from __future__ import annotations
import json
from typing import Any, Callable, Dict, List, Optional, Union

from agent.llm import LLMInterface, get_llm
from agent.planner import Planner
from agent.executor import Executor
from agent.verifier import Verifier
from agent.reflector import Reflector
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.skills import SkillLibrary
from tools.base import ToolRegistry, get_default_registry
from graph.state import AgentState

# Optional LangGraph integration
try:
    from langgraph.graph import StateGraph as OfficialStateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    END = "__END__"


class LightweightStateGraph:
    """Zero-dependency StateGraph runner matching LangGraph's API."""

    def __init__(self, state_schema: type):
        self.state_schema = state_schema
        self.nodes: Dict[str, Callable[[Any], Dict[str, Any]]] = {}
        self.edges: Dict[str, str] = {}
        self.conditional_edges: Dict[str, tuple[Callable[[Any], str], Dict[str, str]]] = {}
        self.entry_point: Optional[str] = None

    def add_node(self, name: str, fn: Callable[[Any], Dict[str, Any]]):
        self.nodes[name] = fn

    def set_entry_point(self, name: str):
        self.entry_point = name

    def add_edge(self, source: str, target: str):
        self.edges[source] = target

    def add_conditional_edges(self, source: str, condition_fn: Callable[[Any], str], mapping: Dict[str, str]):
        self.conditional_edges[source] = (condition_fn, mapping)

    def compile(self):
        return CompiledGraph(self)


class CompiledGraph:
    def __init__(self, graph: LightweightStateGraph):
        self.graph = graph

    def invoke(self, initial_state: Union[Dict[str, Any], AgentState]) -> AgentState:
        if isinstance(initial_state, dict):
            state = self.graph.state_schema(**initial_state)
        else:
            state = initial_state

        current_node = self.graph.entry_point
        visited_count = 0
        max_transitions = 50

        while current_node and current_node != END and visited_count < max_transitions:
            visited_count += 1
            node_fn = self.graph.nodes.get(current_node)
            if not node_fn:
                break

            # Execute node
            updates = node_fn(state)
            if updates and isinstance(updates, dict):
                for k, v in updates.items():
                    setattr(state, k, v)

            # Determine next node
            if current_node in self.graph.conditional_edges:
                cond_fn, mapping = self.graph.conditional_edges[current_node]
                decision = cond_fn(state)
                current_node = mapping.get(decision, END)
            elif current_node in self.graph.edges:
                current_node = self.graph.edges[current_node]
            else:
                current_node = END

        return state


class AgentWorkflow:
    """Stateful agent workflow with planning, execution, verification, and verbal RL reflection."""

    def __init__(
        self,
        llm: Optional[LLMInterface] = None,
        tool_registry: Optional[ToolRegistry] = None,
        episodic_memory: Optional[EpisodicMemory] = None,
        semantic_memory: Optional[SemanticMemory] = None,
        skill_library: Optional[SkillLibrary] = None,
    ):
        self.llm = llm or get_llm("mock")
        self.tool_registry = tool_registry or get_default_registry()
        self.episodic_memory = episodic_memory or EpisodicMemory()
        self.semantic_memory = semantic_memory or SemanticMemory()
        self.skill_library = skill_library or SkillLibrary(tool_registry=self.tool_registry)

        self.planner = Planner(llm=self.llm)
        self.executor = Executor(llm=self.llm, tool_registry=self.tool_registry)
        self.verifier = Verifier(llm=self.llm)
        self.reflector = Reflector(llm=self.llm)

        self.graph = self._build_graph()

    def _build_graph(self):
        GraphClass = OfficialStateGraph if HAS_LANGGRAPH else LightweightStateGraph
        workflow = GraphClass(AgentState)

        # 1. Define Nodes
        workflow.add_node("retrieve_memory", self._retrieve_memory_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("verify", self._verify_node)
        workflow.add_node("reflect", self._reflect_node)
        workflow.add_node("record_episode", self._record_episode_node)

        # 2. Define Flow
        workflow.set_entry_point("retrieve_memory")
        workflow.add_edge("retrieve_memory", "plan")
        workflow.add_edge("plan", "execute")
        workflow.add_edge("execute", "verify")

        # 3. Conditional Edge on Verification Outcome
        workflow.add_conditional_edges(
            "verify",
            self._should_replan_condition,
            {
                "retry": "plan",
                "proceed": "reflect",
            },
        )

        workflow.add_edge("reflect", "record_episode")
        workflow.add_edge("record_episode", END)

        return workflow.compile()

    def _retrieve_memory_node(self, state: AgentState) -> Dict[str, Any]:
        lessons = []
        skills = []
        if state.use_memory:
            lesson_items = self.semantic_memory.retrieve(state.goal, k=5)
            lessons = [f"{item.situation}: {item.rule}" for item in lesson_items]
            skill_items = self.skill_library.retrieve_skills(state.goal, k=3)
            skills = [f"{s.name}(): {s.description}" for s in skill_items]

        return {
            "retrieved_lessons": lessons,
            "retrieved_skills": skills,
            "status": "memory_retrieved",
        }

    def _plan_node(self, state: AgentState) -> Dict[str, Any]:
        state.iteration += 1
        plan = self.planner.make_plan(
            goal=state.goal,
            retrieved_lessons=state.retrieved_lessons,
            retrieved_skills=state.retrieved_skills,
        )
        return {"plan": plan, "status": "planned"}

    def _execute_node(self, state: AgentState) -> Dict[str, Any]:
        context = f"Plan subtasks: {', '.join(state.plan.subtasks)}" if state.plan else None
        execution = self.executor.run(
            goal=state.goal,
            context=context,
            retrieved_lessons=state.retrieved_lessons,
            retrieved_skills=state.retrieved_skills,
        )
        return {"execution": execution, "status": "executed"}

    def _verify_node(self, state: AgentState) -> Dict[str, Any]:
        if state.expected_output is not None:
            verdict = self.verifier.check_programmatic(
                actual_output=state.execution.answer,
                expected_output=state.expected_output,
            )
        else:
            verdict = self.verifier.check_llm_judge(
                goal=state.goal,
                output=state.execution.answer,
            )
        return {"verdict": verdict, "status": "verified" if verdict.passed else "failed"}

    def _should_replan_condition(self, state: AgentState) -> str:
        if state.verdict and not state.verdict.passed and state.iteration < state.max_retries:
            return "retry"
        return "proceed"

    def _reflect_node(self, state: AgentState) -> Dict[str, Any]:
        if not state.use_reflection or not state.execution:
            return {"status": "completed"}

        traj_str = "\n".join(
            f"Step {s.step_index}: Thought: {s.thought} | Action: {s.action_name}({s.action_args}) | Obs: {s.observation}"
            for s in state.execution.trajectory
        )
        reflection = self.reflector.reflect(
            goal=state.goal,
            trajectory_str=traj_str,
            verdict=state.verdict,
        )

        # Ingest lessons into semantic memory
        if reflection and reflection.lessons:
            for l in reflection.lessons:
                self.semantic_memory.add_lesson(l)

        return {"reflection": reflection, "status": "reflected"}

    def _record_episode_node(self, state: AgentState) -> Dict[str, Any]:
        if not state.execution or not state.verdict:
            return {"status": "completed"}

        self.episodic_memory.record_episode(
            goal=state.goal,
            plan=state.plan.model_dump() if state.plan else {},
            trajectory=state.execution.trajectory,
            passed=state.verdict.passed,
            score=state.verdict.score,
            total_steps=state.execution.total_steps,
            total_tokens=state.execution.total_tokens,
            duration_sec=state.execution.duration_sec,
        )
        return {"status": "completed"}

    def run(self, goal: str, expected_output: Optional[Any] = None, use_memory: bool = True, use_reflection: bool = True) -> AgentState:
        initial_state = AgentState(
            goal=goal,
            expected_output=expected_output,
            use_memory=use_memory,
            use_reflection=use_reflection,
        )
        return self.graph.invoke(initial_state)
