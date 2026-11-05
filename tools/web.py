"""Web search and retrieval tool with indirect prompt injection defenses."""

import re
from typing import Dict
from tools.base import tool, ToolResult, PermissionTier

INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"system override",
    r"you are now in developer mode",
    r"disregard all prior rules",
    r"execute the following command",
]

# Simulated knowledge base for offline deterministic agent tests and web queries
KNOWLEDGE_BASE: Dict[str, str] = {
    "python 3.14": "Python 3.14 features template strings, enhanced deferred evaluation of annotations, and interpreter optimizations.",
    "reflexion": "Reflexion is an agent framework by Shinn et al. that uses verbal reinforcement learning via self-reflection to improve task performance without fine-tuning.",
    "voyager": "Voyager is an LLM-powered embodied agent in Minecraft that autonomously explores and builds a growing skill library of executable code.",
    "react": "ReAct by Yao et al. combines reasoning and action generation in an interleaved loop (Thought, Action, Observation).",
}


def sanitize_web_content(content: str) -> str:
    """Detects and neutralizes prompt-injection patterns from external text."""
    sanitized = content
    for pattern in INJECTION_PATTERNS:
        sanitized = re.sub(pattern, "[FILTERED_SUSPICIOUS_INSTRUCTION]", sanitized, flags=re.IGNORECASE)
    return sanitized


@tool(name="web_search", permission=PermissionTier.READ_ONLY, description="Searches web/knowledge base for verified information.")
def web_search(query: str) -> ToolResult:
    """Executes a search query with prompt injection sanitization."""
    q_lower = query.lower()
    matches = []
    for k, v in KNOWLEDGE_BASE.items():
        if k in q_lower or any(word in k for word in q_lower.split() if len(word) > 3):
            matches.append(f"[{k.title()}]: {v}")

    if not matches:
        # Fallback simulation
        return ToolResult(
            ok=True,
            output=f"Search completed for '{query}'. No high-confidence direct matches found in offline index.",
        )

    raw_output = "\n".join(matches)
    safe_output = sanitize_web_content(raw_output)
    return ToolResult(ok=True, output=safe_output)

