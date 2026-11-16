# Autonomous Self-Learning AI Agent System (Nexus v1.0.0)

[![CI](https://github.com/shivrajpawar514-commits/Nexus---An-Autonomous-Self-learning-Ai-system/actions/workflows/ci.yml/badge.svg)](https://github.com/shivrajpawar514-commits/Nexus---An-Autonomous-Self-learning-Ai-system/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An autonomous, sandboxed AI agent system that takes high-level declarative goals, produces verified multi-step execution plans, executes actions using a typed tool layer, reflects on outcomes through verbal reinforcement learning, builds an expanding skill library, and measurably improves performance over time.

---

## Architecture Overview

```
User Goal
   │
   ▼
[Orchestrator / LangGraph Workflow] ──► [Planner] ──► Subtask Sequence
   │                                                         │
   │                                                         ▼
   │                                                   [ReAct Executor] ◄──► [Sandboxed Tools]
   │                                                         │                • Calculator (AST-Safe)
   │                                                         ▼                • Python Sandbox
   │                                                   [Verifier Tier]        • File I/O (Jail-guarded)
   │                                                     1. Unit tests        • Web Search (Injection-filtered)
   │                                                     2. Custom Checks
   │                                                     3. LLM-as-a-judge
   │                                                         │
   ▼                                                         ▼
[Memory Subsystem] ◄───────────────────────────────── [Reflection Engine]
   • Working (In-Context Dialogue)                       • Root-Cause Analysis
   • Episodic (SQLite / PostgreSQL + pgvector)           • Trust-Weighted Lessons
   • Semantic (4-Factor Vector Ranking)                  • Promoted Skill Library
```

---

## Core Capabilities

1. **Dual Orchestration Engines**:
   - **Linear Pipeline**: Classic Plan $\to$ Act $\to$ Observe $\to$ Verify $\to$ Reflect $\to$ Store coordinator.
   - **LangGraph StateGraph**: Graph workflow with conditional edges (`should_replan`), cyclic recovery loops, and full state history tracking.
2. **Provider-Agnostic LLM Interface**:
   - Deterministic offline mock engine for zero-cost testing and benchmarking.
   - Local Ollama interface (`http://localhost:11434`) with automatic offline mock fallback.
   - Production OpenAI interface (`gpt-4o-mini`, `gpt-4o`).
3. **Four-Layer Self-Learning Subsystem**:
   - *Episodic Memory*: Persists plans, trajectory traces, tokens, and execution timings in SQLite or PostgreSQL with `pgvector`.
   - *Semantic Memory*: In-context memory retrieval incorporating Cosine Similarity ($\alpha=0.50$), Recency Decay ($\beta=0.15$), Importance ($\gamma=0.15$), and Historical Usefulness ($\delta=0.20$).
   - *Reflection Engine*: Formulates structured lessons with verifier-discounted confidence weights ($\text{TrustWeight} = \text{Confidence} \times \text{Trust}$).
   - *Voyager Skill Library*: Synthesizes, unit-tests, and promotes verified Python functions into live tools.
4. **Mission Control Web Dashboard**:
   - Multi-threaded REST telemetry server (`python main.py dashboard`).
   - Real-time interactive neural visualization canvas, ReAct sequential stepper, and Chart.js metrics.
   - Interactive Sandbox Laboratory playground.

---

## Quickstart

### 1. Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run an Autonomous Task
```bash
# Standard Orchestrator execution
python main.py run "Compute the sum of all prime numbers between 1 and 20"

# LangGraph StateGraph Workflow execution
python main.py run "Calculate compound interest on $1000 at 5% for 3 years" --workflow

# Local Ollama Provider execution
python main.py run "Analyze dataset statistics" --provider ollama
```

### 3. Launch Mission Control Dashboard
```bash
python main.py dashboard --port 8080
# Open http://localhost:8080 in your browser
```

### 4. Run Benchmark Suite
```bash
python -m eval.run --split test
```

### 5. Run Full Test Suite
```bash
pytest tests/ -v
```

---

## Docker Deployment

```bash
docker compose build
docker compose up
```

---

## Project Structure

```
nexus-autonomous-agent/
├── README.md                 # Project overview and documentation
├── Makefile                  # Build, test, and run automation
├── Dockerfile                # Multi-stage production container
├── docker-compose.yml        # Orchestration configuration
├── main.py                   # Unified CLI application entry point
├── docs/                     # Design, safety, and research specifications
├── agent/                    # Core reasoning, execution, and reflection
│   ├── orchestrator.py       # Master lifecycle coordinator
│   ├── planner.py            # Goal decomposition and replanning
│   ├── executor.py           # ReAct Thought-Action-Observation loop
│   ├── verifier.py           # 3-tier assertion hierarchy
│   ├── reflector.py          # Post-mortem verbal RL engine
│   └── llm.py                # LLM client abstractions (Mock, Ollama, OpenAI)
├── graph/                    # LangGraph StateGraph workflow engine
│   ├── state.py              # AgentState Pydantic schema
│   └── workflow.py           # Cyclic workflow with conditional replanning
├── memory/                   # Multi-tier memory architecture
│   ├── episodic.py           # Trajectory run persistence
│   ├── semantic.py           # 4-factor vector retrieval
│   ├── skills.py             # Self-testing Voyager skill library
│   └── db.py                 # SQLite & PostgreSQL + pgvector adapter
├── tools/                    # Sandboxed tool layer
│   ├── base.py               # @tool decorator and registry
│   ├── calculator.py         # AST-safe arithmetic engine
│   ├── python_sandbox.py     # Isolated execution sandbox
│   ├── files.py              # Jail-guarded file reader/writer
│   └── web.py                # Injection-filtered search
├── dashboard/                # Live Mission Control Web Dashboard
│   ├── server.py             # Multithreaded REST server
│   └── static/               # Interactive UI and legal documentation
├── eval/                     # Empirical benchmark harness
└── tests/                    # 46 unit, integration, and security tests
```

---

## Evaluation Benchmark

| Configuration | Test Split Accuracy | Avg Steps | Avg Tokens |
| :--- | :--- | :--- | :--- |
| **Nexus Autonomous System (v1.0.0)** | **100.0%** | **2.0** | **229.7** |

---

## License

MIT License. Designed and developed for autonomous AI research.


