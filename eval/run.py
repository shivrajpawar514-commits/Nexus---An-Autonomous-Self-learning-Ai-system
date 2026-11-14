"""Benchmark evaluation runner measuring learning curves and ablation metrics."""

import argparse
import sys
from typing import Dict, List
from agent.llm import MockLLM
from agent.orchestrator import Orchestrator
from eval.checkers import exact_number_checker, string_contains_checker
from eval.tasks.data_tasks import get_tasks_by_split, BenchmarkTask


def evaluate_split(
    orchestrator: Orchestrator,
    split: str = "test",
    use_memory: bool = True,
    use_reflection: bool = False,
) -> Dict[str, float]:
    tasks = get_tasks_by_split(split)
    if not tasks:
        print(f"No tasks found for split '{split}'")
        return {"success_rate": 0.0, "avg_steps": 0.0, "avg_tokens": 0.0}

    passed_count = 0
    total_steps = 0
    total_tokens = 0

    print(f"\n--- Running Benchmark Evaluation on Split: [{split.upper()}] ({len(tasks)} tasks) ---")
    for t in tasks:
        checker = None
        if t.checker_name == "exact_number":
            checker = exact_number_checker(float(t.expected_output), tolerance=1e-3)
        elif t.checker_name == "string":
            checker = string_contains_checker(str(t.expected_output))

        report = orchestrator.run_task(
            goal=t.goal,
            expected_output=t.expected_output,
            test_fn=checker,
            use_memory=use_memory,
            use_reflection=use_reflection,
        )

        total_steps += report.execution.total_steps
        total_tokens += report.execution.total_tokens
        if report.passed:
            passed_count += 1
            status = "PASSED"
        else:
            status = "FAILED"

        print(f"[{status}] Task {t.id}: '{t.goal[:45]}...' | Steps: {report.execution.total_steps} | Tokens: {report.execution.total_tokens}")

    n = len(tasks)
    metrics = {
        "success_rate": round((passed_count / n) * 100, 1),
        "avg_steps": round(total_steps / n, 2),
        "avg_tokens": round(total_tokens / n, 1),
        "total_tasks": n,
    }

    print("\n--- Summary Results ---")
    print(f"Success Rate:      {metrics['success_rate']}%")
    print(f"Average Steps:     {metrics['avg_steps']}")
    print(f"Average Tokens:    {metrics['avg_tokens']}")
    return metrics


def run_learning_cycle(num_iterations: int = 3):
    """Demonstrates quantitative improvement across learning iterations."""
    print(f"\n=======================================================")
    print(f"Running Multi-Iteration Self-Learning Experiment ({num_iterations} cycles)")
    print(f"=======================================================")

    mock_llm = MockLLM()
    orchestrator = Orchestrator(llm=mock_llm)

    history = []

    for i in range(num_iterations):
        print(f"\n>>> ITERATION {i} <<<")
        # 1. Run train split WITH reflection to learn lessons & skills
        print("Training phase (reflecting and storing lessons)...")
        evaluate_split(orchestrator, split="train", use_memory=True, use_reflection=True)

        # 2. Evaluate held-out TEST split WITHOUT test contamination
        print("\nHeld-out Test Evaluation...")
        test_metrics = evaluate_split(orchestrator, split="test", use_memory=True, use_reflection=False)
        history.append((i, test_metrics))

    print("\n" + "=" * 60)
    print("LEARNING CURVE TABLE (Held-Out Test Performance)")
    print("=" * 60)
    print(f"{'Iteration':<12} | {'Test Success Rate':<18} | {'Avg Steps':<12} | {'Tokens / Task':<15}")
    print("-" * 65)
    for it, m in history:
        print(f"{it:<12} | {m['success_rate']:<17}% | {m['avg_steps']:<12} | {m['avg_tokens']:<15}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous Agent Evaluation Harness")
    parser.add_argument("--split", type=str, default="test", choices=["train", "val", "test"])
    parser.add_argument("--learn-cycles", type=int, default=0, help="Run multi-iteration learning experiment")
    args = parser.parse_args()

    if args.learn_cycles > 0:
        run_learning_cycle(args.learn_cycles)
    else:
        llm = MockLLM()
        orch = Orchestrator(llm=llm)
        evaluate_split(orch, split=args.split)

