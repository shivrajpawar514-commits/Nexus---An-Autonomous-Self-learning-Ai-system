# ADR 002: Multi-Agent Blackboard Communication and Swarm Consensus Protocol

## Status
Accepted

## Context
As Nexus expands from single-agent ReAct and subagent tree delegation toward autonomous agent swarms, subagents require peer-to-peer collaboration, plan auditing, and agreement protocols. Direct point-to-point messaging creates tight coupling and $O(N^2)$ communication channels.

## Decision
We introduce:
1. **Blackboard Architecture (`Blackboard`)**: A decoupled, thread-safe publish-subscribe message broker where agents post typed messages (`PROPOSAL`, `CRITIQUE`, `VOTE`, `KNOWLEDGE_SHARE`, `ALERT`) to specific topics.
2. **Consensus Engine (`ConsensusEngine`)**: A configurable voting evaluator supporting:
   - Simple majority and supermajority ($2/3$) quorums.
   - Reputation-weighted confidence scoring ($W_i \times C_i$).
   - Explicit tie-breaking and abstention handling.
3. **Debate Coordinator (`DebateCoordinator`)**: Iterative proposer-critic dialectic loop that challenges and refines solutions before execution.

## Consequences
- **Decoupled Swarm Coordination**: Multiple agents can monitor, critique, or build upon proposals asynchronously.
- **Higher Safety & Correctness**: Supermajority voting and debate loops suppress hallucinated steps or risky actions before tool execution.
- **Observability**: Live blackboard messages and consensus evaluations are exposed through dashboard REST endpoints (`/api/blackboard/messages`, `/api/consensus/status`).
