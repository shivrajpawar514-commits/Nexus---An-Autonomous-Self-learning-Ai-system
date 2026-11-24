"""Built-in token expenditure and monetary budget tracking plugin."""

from __future__ import annotations
from typing import Any, Dict, Optional, Tuple
from plugins.base import PluginInterface, PluginManifest, PluginContext


class CostTrackerPlugin(PluginInterface):
    """Tracks token spend, estimates API costs, and trips execution when budget limit is reached."""

    def __init__(
        self,
        cost_per_1k_prompt: float = 0.0015,
        cost_per_1k_completion: float = 0.002,
        max_budget_usd: float = 10.0,
    ):
        manifest = PluginManifest(
            name="cost_tracker",
            version="1.0.0",
            description="Real-time token expense calculator and hard budget limiter",
            author="Nexus Core Team",
            hooks=["on_pre_execute", "on_post_execute"],
        )
        super().__init__(manifest)
        self.cost_per_1k_prompt = cost_per_1k_prompt
        self.cost_per_1k_completion = cost_per_1k_completion
        self.max_budget_usd = max_budget_usd
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_spend_usd = 0.0

    def record_usage(self, prompt_tokens: int, completion_tokens: int) -> float:
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        incremental_cost = (
            (prompt_tokens / 1000.0) * self.cost_per_1k_prompt
            + (completion_tokens / 1000.0) * self.cost_per_1k_completion
        )
        self.total_spend_usd += incremental_cost
        return incremental_cost

    def on_pre_execute(self, action_name: str, args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if self.total_spend_usd >= self.max_budget_usd:
            return False, f"Budget quota exceeded: spend ${self.total_spend_usd:.4f} >= limit ${self.max_budget_usd:.2f}"
        return True, None

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_spend_usd": round(self.total_spend_usd, 5),
            "max_budget_usd": self.max_budget_usd,
            "budget_remaining_usd": round(max(0.0, self.max_budget_usd - self.total_spend_usd), 5),
        }
