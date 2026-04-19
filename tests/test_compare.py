"""Tests for compare module."""

from pathlib import Path

from workflowbench.adapters import EchoAdapter
from workflowbench.runner import run_benchmark
from workflowbench.compare import compare_runs, render_comparison_md

CASES_DIR = Path(__file__).resolve().parent.parent / "cases"


def test_compare_same_run():
    adapter = EchoAdapter()
    run_a = run_benchmark(CASES_DIR, adapter, run_id="a")
    run_b = run_benchmark(CASES_DIR, adapter, run_id="b")
    cmp = compare_runs(run_a, run_b)
    assert cmp.overall_delta == 0.0
    assert len(cmp.regressions) == 0
    assert len(cmp.improvements) == 0


def test_render_comparison_md():
    adapter = EchoAdapter()
    run_a = run_benchmark(CASES_DIR, adapter, run_id="a")
    run_b = run_benchmark(CASES_DIR, adapter, run_id="b")
    cmp = compare_runs(run_a, run_b)
    md = render_comparison_md(cmp)
    assert "WorkflowBench Comparison" in md
    assert "Run A" in md
