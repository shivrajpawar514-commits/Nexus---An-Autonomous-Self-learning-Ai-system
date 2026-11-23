"""Blackboard message bus for multi-agent swarm collaboration and knowledge sharing."""

from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    PROPOSAL = "PROPOSAL"
    CRITIQUE = "CRITIQUE"
    VOTE = "VOTE"
    KNOWLEDGE_SHARE = "KNOWLEDGE_SHARE"
    ALERT = "ALERT"


class BlackboardMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender: str
    topic: str
    msg_type: MessageType
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class Blackboard:
    """Thread-safe centralized blackboard message broker."""

    def __init__(self):
        self._messages: List[BlackboardMessage] = []
        self._subscribers: Dict[str, List[Callable[[BlackboardMessage], None]]] = {}

    def post(
        self,
        sender: str,
        topic: str,
        msg_type: MessageType | str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> BlackboardMessage:
        """Publish a new message to the blackboard and notify topic subscribers."""
        if isinstance(msg_type, str):
            msg_type = MessageType(msg_type)

        msg = BlackboardMessage(
            sender=sender,
            topic=topic,
            msg_type=msg_type,
            payload=payload or {},
            timestamp=time.time(),
        )
        self._messages.append(msg)

        # Notify subscribers
        subscribers = self._subscribers.get(topic, []) + self._subscribers.get("*", [])
        for sub in subscribers:
            try:
                sub(msg)
            except Exception:
                pass

        return msg

    def get_messages(
        self,
        topic: Optional[str] = None,
        msg_type: Optional[MessageType | str] = None,
        sender: Optional[str] = None,
        limit: int = 100,
    ) -> List[BlackboardMessage]:
        """Query messages filtered by topic, type, or sender."""
        results = self._messages
        if topic:
            results = [m for m in results if m.topic == topic]
        if msg_type:
            target_type = MessageType(msg_type) if isinstance(msg_type, str) else msg_type
            results = [m for m in results if m.msg_type == target_type]
        if sender:
            results = [m for m in results if m.sender == sender]

        return results[-limit:]

    def subscribe(self, topic: str, callback: Callable[[BlackboardMessage], None]) -> None:
        """Subscribe a callback to messages on a specific topic (or '*' for all)."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)

    def clear(self) -> None:
        """Clear all messages from the blackboard."""
        self._messages.clear()
        self._subscribers.clear()

    def count(self) -> int:
        return len(self._messages)
