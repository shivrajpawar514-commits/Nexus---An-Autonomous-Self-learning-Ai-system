"""Semantic memory with recency, importance, and past-usefulness scoring."""

from __future__ import annotations
import math
import time
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import numpy as np
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from agent.reflector import StructuredLesson


class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    text: str
    rule: str
    situation: str
    importance: float = 0.5  # 0.0 to 1.0
    created_at: float = Field(default_factory=time.time)
    last_accessed_at: float = Field(default_factory=time.time)
    times_retrieved: int = 0
    success_count: int = 0
    failure_count: int = 0

    @property
    def usefulness(self) -> float:
        # Laplace-smoothed success rate
        return (self.success_count + 1) / (self.success_count + self.failure_count + 2)


class SimpleVectorIndex:
    """Lightweight, self-contained semantic vector index using TF-IDF character/word n-grams."""

    def __init__(self):
        self.vocab: Dict[str, int] = {}
        self.vectors: Dict[str, np.ndarray] = {}

    def _tokenize(self, text: str) -> List[str]:
        words = [w.strip().lower() for w in text.split() if len(w) > 2]
        # Include character tri-grams for robust partial matching
        ngrams = []
        for w in words:
            if len(w) >= 3:
                for i in range(len(w) - 2):
                    ngrams.append(w[i : i + 3])
        return words + ngrams

    def get_or_create_vector(self, text: str) -> np.ndarray:
        tokens = self._tokenize(text)
        for t in tokens:
            if t not in self.vocab:
                self.vocab[t] = len(self.vocab)

        vec = np.zeros(max(len(self.vocab), 1))
        for t in tokens:
            idx = self.vocab[t]
            vec[idx] += 1.0

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def compute_similarity(self, query: str, doc_vec: np.ndarray) -> float:
        query_vec = self.get_or_create_vector(query)
        # Pad to match dimensions if vocab grew
        dim = max(len(query_vec), len(doc_vec))
        q_padded = np.zeros(dim)
        d_padded = np.zeros(dim)
        q_padded[: len(query_vec)] = query_vec
        d_padded[: len(doc_vec)] = doc_vec

        sim = float(np.dot(q_padded, d_padded))
        return max(0.0, min(1.0, sim))


class SemanticMemory:
    def __init__(
        self,
        alpha_sim: float = 0.50,
        beta_recency: float = 0.15,
        gamma_importance: float = 0.15,
        delta_usefulness: float = 0.20,
        recency_decay_lambda: float = 0.001,
    ):
        self.items: Dict[str, MemoryItem] = {}
        self.index = SimpleVectorIndex()
        self.doc_vectors: Dict[str, np.ndarray] = {}
        self.alpha = alpha_sim
        self.beta = beta_recency
        self.gamma = gamma_importance
        self.delta = delta_usefulness
        self.decay_lambda = recency_decay_lambda

    def add_lesson(self, lesson: Any) -> str:
        situation = getattr(lesson, "situation", "")
        rule = getattr(lesson, "rule", "")
        root_cause = getattr(lesson, "root_cause", "")
        confidence = float(getattr(lesson, "confidence", 0.8))
        trust_weight = float(getattr(lesson, "trust_weight", 1.0))

        full_text = f"{situation} | {rule} | {root_cause}"
        item = MemoryItem(
            text=full_text,
            rule=rule,
            situation=situation,
            importance=confidence * trust_weight,
        )
        self.items[item.id] = item
        self.doc_vectors[item.id] = self.index.get_or_create_vector(full_text)
        return item.id

    def retrieve(self, query: str, k: int = 5) -> List[MemoryItem]:
        if not self.items:
            return []

        scored_candidates = []
        now = time.time()

        for mem_id, item in self.items.items():
            doc_vec = self.doc_vectors.get(mem_id)
            sim = self.index.compute_similarity(query, doc_vec) if doc_vec is not None else 0.0

            # Recency decay: e^(-lambda * dt)
            dt = max(0.0, now - item.created_at)
            recency = math.exp(-self.decay_lambda * dt)

            score = (
                self.alpha * sim
                + self.beta * recency
                + self.gamma * item.importance
                + self.delta * item.usefulness
            )
            scored_candidates.append((score, item))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        top_k = [item for _, item in scored_candidates[:k]]

        # Update access telemetry
        for item in top_k:
            item.last_accessed_at = now
            item.times_retrieved += 1

        return top_k

    def query_lessons(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        """Convenience alias for retrieve."""
        return self.retrieve(query=query, k=top_k)

    def update_usefulness(self, memory_ids: List[str], passed: bool):
        for mid in memory_ids:
            if mid in self.items:
                if passed:
                    self.items[mid].success_count += 1
                else:
                    self.items[mid].failure_count += 1

    def record_outcome(self, memory_id: str, success: bool):
        """Records outcome for a single memory item."""
        self.update_usefulness([memory_id], passed=success)

