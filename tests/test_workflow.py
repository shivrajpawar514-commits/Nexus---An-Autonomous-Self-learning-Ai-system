"""Unit and integration tests for LangGraph StateGraph workflow orchestration."""

import pytest
from agent.llm import MockLLM
from graph.state import AgentState
from graph.workflow import AgentWorkflow, LightweightStateGraph, END


def test_lightweight_state_graph_compilation_and_execution():
    graph = LightweightStateGraph(state_schema=AgentState)

    def node_a(state: AgentState):
        return {"goal": state.goal + " [A]"}

    def node_b(state: AgentState):
        return {"goal": state.goal + " [B]", "status": "completed"}

    graph.add_node("step_a", node_a)
    graph.add_node("step_b", node_b)
    graph.set_entry_point("step_a")
    graph.add_edge("step_a", "step_b")
    graph.add_edge("step_b", END)

    app = graph.compile()
    final_state = app.invoke(AgentState(goal="Task"))

    assert "[A] [B]" in final_state.goal
    assert final_state.status == "completed"


def test_langgraph_workflow_orchestration_end_to_end():
    llm = MockLLM()
    workflow = AgentWorkflow(llm=llm)

    state = workflow.run(
        goal="Calculate 15 * 4 + 10",
        expected_output=70,
        use_memory=True,
        use_reflection=True,
    )

    assert isinstance(state, AgentState)
    assert state.status == "completed"
    assert state.verdict is not None
    assert state.verdict.passed is True
    assert "70" in str(state.execution.answer)
