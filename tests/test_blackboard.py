"""Unit tests for blackboard message bus and topic subscriptions."""

import pytest
from agent.blackboard import Blackboard, BlackboardMessage, MessageType


def test_blackboard_post_and_retrieve():
    bb = Blackboard()
    msg1 = bb.post(
        sender="planner",
        topic="architecture",
        msg_type=MessageType.PROPOSAL,
        payload={"plan": "split into 3 subtasks"},
    )
    assert msg1.id is not None
    assert msg1.sender == "planner"
    assert msg1.topic == "architecture"

    msg2 = bb.post(
        sender="critic",
        topic="architecture",
        msg_type=MessageType.CRITIQUE,
        payload={"flaw": "subtask 2 has cyclic dependency"},
    )

    all_msgs = bb.get_messages()
    assert len(all_msgs) == 2

    # Query by topic
    arch_msgs = bb.get_messages(topic="architecture")
    assert len(arch_msgs) == 2

    # Query by type
    critiques = bb.get_messages(msg_type=MessageType.CRITIQUE)
    assert len(critiques) == 1
    assert critiques[0].sender == "critic"


def test_blackboard_subscription_callback():
    bb = Blackboard()
    received = []

    def on_alert(msg: BlackboardMessage):
        received.append(msg)

    bb.subscribe("security", on_alert)

    # Post message on another topic
    bb.post("agent1", "perf", MessageType.KNOWLEDGE_SHARE, {"cache": "hit"})
    assert len(received) == 0

    # Post message on subscribed topic
    bb.post("agent2", "security", MessageType.ALERT, {"violation": "sandbox breach"})
    assert len(received) == 1
    assert received[0].payload["violation"] == "sandbox breach"


def test_blackboard_clear():
    bb = Blackboard()
    bb.post("a", "t", MessageType.PROPOSAL)
    assert bb.count() == 1
    bb.clear()
    assert bb.count() == 0
    assert len(bb.get_messages()) == 0
