"""Model router mapping task complexity and budget to optimal LLM provider tiers."""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from routing.classifier import ComplexityClassifier, ComplexityAssessment


class ModelTier(str, Enum):
    FAST = "FAST"              # e.g. Flash / Ollama 7B (low latency, lowest cost)
    BALANCED = "BALANCED"      # e.g. Claude 3.5 Sonnet / Gemini Pro (standard workhorse)
    REASONING = "REASONING"    # e.g. o1 / DeepSeek R1 / Opus (maximum intelligence)
    OFFLINE = "OFFLINE"        # Local offline fallback


class TierConfig(BaseModel):
    tier: ModelTier
    model_name: str
    cost_per_1k_tokens: float
    max_context_window: int = 32000
    avg_latency_sec: float = 0.5


class ModelRouter:
    """Selects the optimal model tier balancing cost, latency, and reasoning requirements."""

    DEFAULT_TIER_CONFIGS: Dict[ModelTier, TierConfig] = {
        ModelTier.FAST: TierConfig(tier=ModelTier.FAST, model_name="fast-mini-llm", cost_per_1k_tokens=0.0002, avg_latency_sec=0.2),
        ModelTier.BALANCED: TierConfig(tier=ModelTier.BALANCED, model_name="balanced-pro-llm", cost_per_1k_tokens=0.002, avg_latency_sec=0.8),
        ModelTier.REASONING: TierConfig(tier=ModelTier.REASONING, model_name="deep-reasoning-llm", cost_per_1k_tokens=0.015, avg_latency_sec=2.5),
        ModelTier.OFFLINE: TierConfig(tier=ModelTier.OFFLINE, model_name="ollama-local", cost_per_1k_tokens=0.0, avg_latency_sec=1.2),
    }

    def __init__(
        self,
        classifier: Optional[ComplexityClassifier] = None,
        tier_configs: Optional[Dict[ModelTier, TierConfig]] = None,
        force_offline: bool = False,
    ):
        self.classifier = classifier or ComplexityClassifier()
        self.tier_configs = tier_configs or self.DEFAULT_TIER_CONFIGS
        self.force_offline = force_offline

    def route(self, goal: str, max_budget_usd: Optional[float] = None) -> TierConfig:
        """Route goal to best matching model tier."""
        if self.force_offline:
            return self.tier_configs[ModelTier.OFFLINE]

        assessment = self.classifier.assess(goal)
        score = assessment.complexity_score

        # Select tier by complexity threshold
        if score >= 0.75:
            selected_tier = ModelTier.REASONING
        elif score >= 0.40:
            selected_tier = ModelTier.BALANCED
        else:
            selected_tier = ModelTier.FAST

        # Budget clamping
        if max_budget_usd is not None and max_budget_usd < 0.005:
            # Low budget forces FAST or OFFLINE
            selected_tier = ModelTier.FAST

        return self.tier_configs[selected_tier]

    def get_tier_info(self) -> Dict[str, Any]:
        return {
            tier.value: {
                "model_name": cfg.model_name,
                "cost_per_1k_tokens": cfg.cost_per_1k_tokens,
                "avg_latency_sec": cfg.avg_latency_sec,
            }
            for tier, cfg in self.tier_configs.items()
        }
