"""Standard evaluation benchmark tasks across train, val, and test splits."""

from typing import Any, Callable, Dict, List
from pydantic import BaseModel
from eval.checkers import exact_number_checker, string_contains_checker


class BenchmarkTask(BaseModel):
    id: str
    goal: str
    split: str  # train, val, test
    expected_output: Any = None
    checker_name: str = "exact"


BENCHMARK_TASKS: List[BenchmarkTask] = [
    # Train Split (Used during learning iterations)
    BenchmarkTask(
        id="train-01",
        goal="Calculate the sum of all prime numbers between 1 and 20 using calculator or Python.",
        split="train",
        expected_output=77.0,
        checker_name="exact_number",
    ),
    BenchmarkTask(
        id="train-02",
        goal="Compute 15% tip on a $120.00 restaurant bill.",
        split="train",
        expected_output=18.0,
        checker_name="exact_number",
    ),
    BenchmarkTask(
        id="train-03",
        goal="What is the square root of 1764 plus 58?",
        split="train",
        expected_output=100.0,
        checker_name="exact_number",
    ),
    # Validation Split (Hyperparameter & prompt calibration)
    BenchmarkTask(
        id="val-01",
        goal="Find the median value of the dataset: [12, 5, 22, 30, 7, 9, 18].",
        split="val",
        expected_output=12.0,
        checker_name="exact_number",
    ),
    BenchmarkTask(
        id="val-02",
        goal="Calculate 2 to the power of 8 divided by 4.",
        split="val",
        expected_output=64.0,
        checker_name="exact_number",
    ),
    # Test Split (HELD-OUT: Never touched during learning/reflection)
    BenchmarkTask(
        id="test-01",
        goal="Calculate the compound interest on $1000 at 5% annual rate compounded once for 3 years: 1000 * (1 + 0.05)^3.",
        split="test",
        expected_output=1157.625,
        checker_name="exact_number",
    ),
    BenchmarkTask(
        id="test-02",
        goal="Compute the sample standard deviation variance of [10, 20, 30, 40, 50] with denominator N-1.",
        split="test",
        expected_output=250.0,
        checker_name="exact_number",
    ),
    BenchmarkTask(
        id="test-03",
        goal="Calculate the product of 45 and 18 minus 110.",
        split="test",
        expected_output=700.0,
        checker_name="exact_number",
    ),
]


def get_tasks_by_split(split: str) -> List[BenchmarkTask]:
    return [t for t in BENCHMARK_TASKS if t.split == split]

