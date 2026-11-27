# Prompt Evolution & Genetic Tuning Methodology

## Overview
Nexus implements autonomous strategy evolution, treating system prompt components as genetic chromosomes that mutate, compete in evaluation tournaments, and self-optimize against benchmark splits.

## Chromosome Anatomy (`evolution/mutator.py`)
- **Persona**: Base identity and problem-solving perspective.
- **Heuristics**: Modular execution tips discovered from reflective learning.
- **Constraints**: Negative rules and boundaries preventing hallucinated or unsafe actions.

## Genetic Mutation Operators
1. `add_heuristic`: Injects high-signal tactical heuristics discovered during reflective post-mortems.
2. `sharpen_constraint`: Adds explicit guardrails against observed boundary errors.
3. `prune_heuristic`: Eliminates redundant heuristics to maintain token efficiency.
4. `enhance_persona`: Calibrates tone and precision.

## Multi-Objective Pareto Fitness Function
$$\text{Fitness} = 0.70 \times \text{Accuracy} + 0.20 \times \text{TokenEfficiency} + 0.10 \times \text{StepEfficiency}$$

## Checkpointing & Rollback Safety
Every promoted chromosome is appended to an immutable history stack (`StrategyManager`). If regression is detected on validation benchmarks, `rollback()` instantly restores the previous known-good prompt checkpoint.
