"""Tests for runner."""

from pathlib import Path

from workflowbench.adapters import EchoAdapter
from workflowbench.runner import run_benchmark

CASES_DIR = Path(__file__).resolve().parent.parent / "cases"


def test_run_benchmark_echo():
    adapter = EchoAdapter()
    bench = run_benchmark(CASES_DIR, adapter, run_id="test-echo")
    assert bench.run_id == "test-echo"
    assert bench.cases_total >= 15
    assert bench.adapter_name == "echo"
    assert len(bench.results) == bench.cases_total


def test_run_benchmark_summary_fields():
    adapter = EchoAdapter()
    bench = run_benchmark(CASES_DIR, adapter)
    assert 0.0 <= bench.pass_rate <= 1.0
    assert 0.0 <= bench.overall_score <= 1.0
    assert bench.cases_passed + bench.cases_failed == bench.cases_total
