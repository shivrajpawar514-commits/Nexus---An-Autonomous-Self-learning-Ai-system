# ADR 001: Hybrid Memory Hierarchy and Verbal Reinforcement Learning

## Status
Accepted

## Context
Autonomous agents operating in production environments face two conflicting requirements:
1. Long-term performance improvement through experience accumulation without gradient-based weight fine-tuning.
2. Strict context window constraints and low retrieval latency.

## Decision
We adopt a four-tier hybrid memory hierarchy coupled with verbal reinforcement learning:
1. **Working Memory (In-Context Scratchpad)**: Ephemeral ReAct trajectory trace (bounded by step limit and token caps).
2. **Episodic Memory (Relational Store)**: Full historical execution runs stored in SQLite / PostgreSQL (`episodes` table) for auditing and trajectory playback.
3. **Semantic Memory (Vector Index)**: Extracted post-mortem lessons retrieved via a 4-factor scoring function:
   $$\text{Score} = \alpha \cdot \text{Sim} + \beta \cdot \text{Recency} + \gamma \cdot \text{Importance} + \delta \cdot \text{Usefulness}$$
4. **Voyager Skill Library**: Dynamically synthesized and unit-tested Python functions promoted directly into the runtime `ToolRegistry`.

## Consequences
- **Positive**: Zero fine-tuning costs; continuous in-context improvement; deterministic verifier guarantees prevent hallucinated rules from corrupting retrieval.
- **Negative**: Requires periodic archival compaction (`compact_memory`) to prevent memory index saturation.
