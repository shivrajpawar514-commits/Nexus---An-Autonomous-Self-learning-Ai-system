"""Semantic complexity classifier for dynamic model tier allocation."""

from __future__ import annotations
import re
from typing import Dict, List
from pydantic import BaseModel, Field


class ComplexityAssessment(BaseModel):
    goal: str
    complexity_score: float = Field(ge=0.0, le=1.0)
    category: str
    features_detected: List[str] = Field(default_factory=list)
    recommended_min_tokens: int = 1000


class ComplexityClassifier:
    """Classifies task goal complexity using semantic patterns and structural heuristics."""

    REASONING_PATTERNS = [
        (r"\b(prove|derive|theorem|deduce|logic)\b", "formal_reasoning", 0.35),
        (r"\b(optimize|refactor|benchmark|profile)\b", "code_optimization", 0.30),
        (r"\b(architect|design|hierarchy|microservice|database)\b", "system_design", 0.30),
        (r"\b(debug|root.?cause|investigate|anomaly|flaw)\b", "deep_debugging", 0.25),
        (r"\b(multi.?step|orchestrate|coordinate|consensus)\b", "multi_agent", 0.25),
    ]

    SIMPLE_PATTERNS = [
        (r"\b(calculate|add|multiply|divide|sum)\b", "arithmetic", -0.2),
        (r"\b(read|open|show|display|get|list)\b", "retrieval", -0.15),
        (r"\b(echo|hello|ping|version)\b", "trivial", -0.3),
    ]

    def assess(self, goal: str) -> ComplexityAssessment:
        goal_lower = goal.lower()
        score = 0.5  # Base baseline
        detected: List[str] = []
        category = "general_reasoning"

        # Check reasoning triggers
        for pattern, cat, weight in self.REASONING_PATTERNS:
            if re.search(pattern, goal_lower):
                score += weight
                detected.append(cat)
                category = cat

        # Check simple triggers
        for pattern, cat, weight in self.SIMPLE_PATTERNS:
            if re.search(pattern, goal_lower):
                score += weight
                detected.append(cat)
                if score < 0.4:
                    category = cat

        # Length factor
        words = goal.split()
        if len(words) > 30:
            score += 0.15
            detected.append("verbose_specification")
        elif len(words) < 6:
            score -= 0.1

        clamped = max(0.05, min(0.99, round(score, 3)))
        min_tokens = int(500 + clamped * 4000)

        return ComplexityAssessment(
            goal=goal,
            complexity_score=clamped,
            category=category,
            features_detected=detected,
            recommended_min_tokens=min_tokens,
        )
