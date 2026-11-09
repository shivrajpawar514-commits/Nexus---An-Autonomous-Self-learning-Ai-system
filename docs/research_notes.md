# Foundations & Literature Review
## Foundational Papers in Autonomous Agent Architectures

This document summarizes the core theoretical foundations that inform the architectural design of this autonomous agent system.

---

### 1. ReAct: Synergizing Reasoning and Acting in Language Models
*Yao et al., ICLR 2023 (Princeton University & Google Research)*

- **Core Insight**: Pure reasoning (Chain-of-Thought) suffers from factual hallucinations and inability to inspect world state. Pure action (act-only policies) fails to plan, track sub-goals, or adjust strategies when unexpected results occur. ReAct combines both into an interleaved loop:
  $$\dots \to \text{Thought}_t \to \text{Action}_t \to \text{Observation}_t \to \text{Thought}_{t+1} \dots$$
- **Mechanism**: The agent decomposes high-level instructions by maintaining an explicit working memory trace. Before invoking any tool (`Action`), the model outputs its reasoning (`Thought`), inspects the environment response (`Observation`), and updates its mental model.
- **System Integration**: Our `agent/executor.py` implements the strict ReAct loop with Pydantic validation, token budgeting, and execution step caps.

---

### 2. Reflexion: Language Agents with Verbal Reinforcement Learning
*Shinn et al., NeurIPS 2023 (Northeastern & MIT)*

- **Core Insight**: Rather than updating neural network weights via traditional RL (PPO) which is sample-inefficient and requires thousands of episodes, agents can perform verbal reinforcement learning. The agent reflects upon task outcomes and converts trial-and-error signals into natural-language heuristic memories.
- **Mechanism**:
  - An evaluation signal (e.g., binary pass/fail, error trace) triggers a **Self-Reflection** prompt.
  - The agent identifies: (1) what situation it was in, (2) what mistake was made, (3) the root cause, and (4) an actionable rule to avoid repeating the mistake.
  - Reflections are appended to episodic and semantic memory and retrieved during future planning.
- **System Integration**: Our `agent/reflector.py` generates structured JSON reflections that are filtered through our verification hierarchy before persistence into `memory/episodic.py` and `memory/semantic.py`.

---

### 3. Voyager: An Open-Ended Embodied Agent with Large Language Models
*Wang et al., NeurIPS 2023 (Stanford, Caltech, UT Austin)*

- **Core Insight**: Complex real-world and coding tasks require a progressively expanding **Skill Library**. Once an agent synthesizes an effective sequence of actions or Python functions that successfully resolves an environment state, it should crystallize that solution as an executable, documented, and tested tool.
- **Mechanism**:
  - Vector-indexed retrieval of existing skills based on task description embeddings.
  - Skill synthesis via iterative prompting until self-verification unit tests pass.
  - Recursive skill composition: complex skills call simpler primitive skills.
- **System Integration**: Implemented in `memory/skills.py`. Verified functions are dynamically loaded and registered as runtime tools for future planner and executor iterations.

---

### 4. Self-Refine: Iterative Refinement with Self-Feedback
*Madaan et al., NeurIPS 2023 (CMU, Allen Institute, UW)*

- **Core Insight**: LLMs generate suboptimal solutions on the first pass (single-turn zero-shot). Iterative feedback-and-refine loops allow the model to critique its own intermediate drafts, identify edge-case deficiencies, and repair them without external supervision.
- **Mechanism**:
  - Feedback Generator: critiques the output against task criteria (correctness, efficiency, safety).
  - Refiner: modifies the output conditioned on the feedback.
- **System Integration**: Integrated into `agent/verifier.py` and `agent/planner.py` for automated replanning when intermediate execution checks indicate incomplete or erroneous states.

---

### 5. MemGPT: Towards LLMs as Operating Systems
*Packer et al., 2023 (UC Berkeley)*

- **Core Insight**: Fixed LLM context windows should be managed analogous to traditional computer memory hierarchies (Virtual Memory, RAM, Disk).
- **Mechanism**:
  - **Working Memory**: In-context scratchpad, user input, system prompt (fast, limited capacity).
  - **Recall / Episodic Memory**: Complete conversation and task logs persisted in relational storage.
  - **Archival / Semantic Memory**: Vector-indexed external storage dynamically queried via search functions.
  - Autonomous memory page swapping and summarization to avoid context window degradation.
- **System Integration**: Implemented across `memory/` modules, pairing SQLite for structured historical episodes with semantic vector retrieval and context length curation.

---

### 6. Verbal Reinforcement Dynamics & Verifier Trust Weighting

To prevent negative transfer (where erroneous feedback degrades agent performance), Nexus formalizes verbal reinforcement via trust-discounted lesson formulation:

$$\text{TrustWeight}(L) = \text{Confidence}(L) \times \text{Trust}(\text{Verdict})$$

- When a programmatic test suite verifies an outcome ($\text{Trust} = 1.0$), lessons are incorporated with full confidence ($1.0 \times 0.85 = 0.85$).
- When heuristic fallbacks or unverified assertions evaluate the outcome ($\text{Trust} \le 0.4$), the resulting lesson weight is discounted ($\le 0.34$), preventing hallucinated rules from dominating retrieval ranking in subsequent tasks.


