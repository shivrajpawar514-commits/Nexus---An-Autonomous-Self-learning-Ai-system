# ADR 004: Semantic Model Routing and Ensemble Arbitration Subsystem

## Status
Accepted

## Context
Running every agent task against a frontier deep-reasoning LLM incurs excessive token costs ($0.015+/1k tokens) and high latency (2-5s), while running complex architectural tasks on lightweight models causes plan hallucination and higher retry rates. A dynamic semantic routing and arbitration layer is required to operate along the cost-accuracy Pareto frontier.

## Decision
We implement:
1. **Semantic Complexity Classifier (`ComplexityClassifier`)**: Analyzes lexical and structural keywords, task length, and required capabilities to calculate a normalized complexity score ($0.05 \to 0.99$).
2. **Multi-Tier Model Router (`ModelRouter`)**:
   - `FAST` ($< 0.40$ complexity, e.g., Flash / Mini models, lowest cost and latency).
   - `BALANCED` ($0.40 \le c < 0.75$, general-purpose workhorse).
   - `REASONING` ($c \ge 0.75$, formal proof, root-cause investigation, and deep architecture).
   - `OFFLINE` (local zero-cost fallback via Ollama).
   - Budget clamping: tight budget parameters automatically downgrade model tier.
3. **Ensemble Arbiter (`EnsembleArbiter`)**: Penalizes long step counts against candidate confidence scores to select concise, high-confidence plans among multi-model proposals.
4. **Dashboard Simulation**: Exposes `/api/routing/models` and `/api/routing/simulate` for real-time routing inspection.

## Consequences
- Reduces average token spend by 40-70% on standard tasks.
- Preserves top-tier reasoning capabilities when solving high-complexity problems.
