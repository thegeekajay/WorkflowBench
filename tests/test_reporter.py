"""Tests for reporter."""

from pathlib import Path

from workflowbench.adapters import EchoAdapter
from workflowbench.runner import run_benchmark
from workflowbench.reporter import render_html, render_markdown

CASES_DIR = Path(__file__).resolve().parent.parent / "cases"


def _get_bench():
    return run_benchmark(CASES_DIR, EchoAdapter(), run_id="test-report")


def test_render_markdown():
    bench = _get_bench()
    md = render_markdown(bench)
    assert "WorkflowBench Report" in md
    assert "test-report" in md
    assert "onb-001" in md


def test_render_html():
    bench = _get_bench()
    html = render_html(bench)
    assert "<html" in html
    assert "test-report" in html
    assert "WorkflowBench Report" in html
