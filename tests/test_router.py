"""Unit tests for semantic complexity classification, multi-tier routing, and ensemble arbitration."""

import pytest
from routing.classifier import ComplexityClassifier
from routing.router import ModelRouter, ModelTier
from routing.arbiter import EnsembleArbiter, CandidatePlan


def test_complexity_classifier():
    classifier = ComplexityClassifier()

    # Simple arithmetic
    simple = classifier.assess("calculate 25 * 40")
    assert simple.complexity_score < 0.4
    assert "arithmetic" in simple.features_detected

    # Deep reasoning & architecture
    complex_task = classifier.assess("Architect and design a fault-tolerant distributed consensus engine with deep debugging")
    assert complex_task.complexity_score >= 0.75
    assert "system_design" in complex_task.features_detected or "deep_debugging" in complex_task.features_detected


def test_model_router_tier_selection():
    router = ModelRouter()

    # Fast tier for simple task
    cfg_fast = router.route("calculate 10 + 20")
    assert cfg_fast.tier == ModelTier.FAST

    # Reasoning tier for complex task
    cfg_reasoning = router.route("Prove theorem and architect formal consensus protocol")
    assert cfg_reasoning.tier == ModelTier.REASONING

    # Budget constraint clamping to FAST tier
    cfg_clamped = router.route("Prove theorem and architect formal consensus protocol", max_budget_usd=0.001)
    assert cfg_clamped.tier == ModelTier.FAST


def test_model_router_force_offline():
    router = ModelRouter(force_offline=True)
    cfg = router.route("Any goal here")
    assert cfg.tier == ModelTier.OFFLINE
    assert cfg.cost_per_1k_tokens == 0.0


def test_ensemble_arbiter_selection():
    arbiter = EnsembleArbiter()
    candidates = [
        CandidatePlan(model_source="fast-model", plan_text="Plan A in 10 steps", estimated_steps=10, confidence_score=0.7),
        CandidatePlan(model_source="pro-model", plan_text="Plan B in 3 steps", estimated_steps=3, confidence_score=0.95),
        CandidatePlan(model_source="reasoning-model", plan_text="Plan C in 20 steps", estimated_steps=20, confidence_score=0.85),
    ]

    result = arbiter.arbitrate(candidates)
    assert result.selected_plan.model_source == "pro-model"
    assert len(result.alternatives) == 2
    assert "pro-model" in result.selection_reason
