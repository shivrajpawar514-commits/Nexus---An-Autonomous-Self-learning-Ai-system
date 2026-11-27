"""Unit tests for prompt chromosomes, genetic mutations, tournament ranking, and rollback."""

import pytest
from evolution.mutator import PromptChromosome, PromptMutator
from evolution.tournament import EvolutionaryTournament, FitnessMetrics
from evolution.strategy import StrategyManager


def test_chromosome_assembly():
    c = PromptChromosome()
    prompt = c.assemble_prompt()
    assert "You are an autonomous AI" in prompt
    assert "Core Heuristics:" in prompt
    assert "Strict Constraints:" in prompt


def test_prompt_mutator():
    mutator = PromptMutator()
    initial = PromptChromosome()
    mutated = mutator.mutate(initial)

    assert mutated.version == initial.version + 1
    assert mutated.generation == initial.generation + 1
    assert mutated.assemble_prompt() is not None


def test_tournament_fitness_calculation_and_ranking():
    tournament = EvolutionaryTournament()

    # High accuracy, low token count
    fit1 = tournament.calculate_fitness(accuracy=1.0, avg_tokens=1000, avg_steps=2.0)
    # Low accuracy, high token count
    fit2 = tournament.calculate_fitness(accuracy=0.6, avg_tokens=5000, avg_steps=6.0)

    assert fit1.composite_fitness > fit2.composite_fitness

    c1 = PromptChromosome(version=1)
    c2 = PromptChromosome(version=2)
    ranked = tournament.rank_population([(c2, fit2), (c1, fit1)])
    assert ranked[0][0].version == 1


def test_strategy_manager_promotion_and_rollback():
    sm = StrategyManager()
    initial_version = sm.active_chromosome.version

    # Mutate and promote
    c2 = PromptChromosome(version=2, generation=1)
    sm.promote_variant(c2)
    assert sm.active_chromosome.version == 2
    assert sm.get_status()["current_version"] == 2

    # Rollback
    rolled_back = sm.rollback()
    assert rolled_back is not None
    assert sm.active_chromosome.version == initial_version
