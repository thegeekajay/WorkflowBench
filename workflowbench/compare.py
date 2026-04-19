"""Comparison mode - diff two benchmark runs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, BaseLoader

from workflowbench.runner import BenchmarkRun


@dataclass
class CaseComparison:
    case_id: str
    case_name: str
    score_a: float
    score_b: float
    delta: float
    passed_a: bool
    passed_b: bool
    status_change: str  # "same", "improved", "regressed"


@dataclass
class ComparisonResult:
    run_a_id: str
    run_b_id: str
    adapter_a: str
    adapter_b: str
    overall_a: float
    overall_b: float
    overall_delta: float
    pass_rate_a: float
    pass_rate_b: float
    cases: list[CaseComparison]
    regressions: list[str]
    improvements: list[str]


def compare_runs(run_a: BenchmarkRun, run_b: BenchmarkRun) -> ComparisonResult:
    """Compare two benchmark runs and highlight regressions/improvements."""
    results_b = {r.case_id: r for r in run_b.results}
    cases = []
    regressions = []
    improvements = []

    for ra in run_a.results:
        rb = results_b.get(ra.case_id)
        if rb is None:
            continue
        delta = rb.overall_score - ra.overall_score
        if rb.passed and not ra.passed:
            status = "improved"
            improvements.append(ra.case_id)
        elif not rb.passed and ra.passed:
            status = "regressed"
            regressions.append(ra.case_id)
        else:
            status = "same"

        cases.append(CaseComparison(
            case_id=ra.case_id,
            case_name=ra.case_name,
            score_a=ra.overall_score,
            score_b=rb.overall_score,
            delta=round(delta, 3),
            passed_a=ra.passed,
            passed_b=rb.passed,
            status_change=status,
        ))

    return ComparisonResult(
        run_a_id=run_a.run_id,
        run_b_id=run_b.run_id,
        adapter_a=run_a.adapter_name,
        adapter_b=run_b.adapter_name,
        overall_a=run_a.overall_score,
        overall_b=run_b.overall_score,
        overall_delta=round(run_b.overall_score - run_a.overall_score, 3),
        pass_rate_a=run_a.pass_rate,
        pass_rate_b=run_b.pass_rate,
        cases=cases,
        regressions=regressions,
        improvements=improvements,
    )


def load_run_json(path: str | Path) -> BenchmarkRun:
    """Load a BenchmarkRun from a saved JSON file."""
    from workflowbench.scorers import ScoreResult
    data = json.loads(Path(path).read_text())
    data["results"] = [ScoreResult(**r) for r in data["results"]]
    return BenchmarkRun(**data)


_COMPARE_MD = """\
# WorkflowBench Comparison

**Run A:** {{ cmp.run_a_id }} ({{ cmp.adapter_a }})
**Run B:** {{ cmp.run_b_id }} ({{ cmp.adapter_b }})

## Summary

| Metric | Run A | Run B | Delta |
|--------|-------|-------|-------|
| Overall score | {{ (cmp.overall_a * 100) | round(1) }}% | {{ (cmp.overall_b * 100) | round(1) }}% | {{ "%+.1f" | format(cmp.overall_delta * 100) }}% |
| Pass rate | {{ (cmp.pass_rate_a * 100) | round(1) }}% | {{ (cmp.pass_rate_b * 100) | round(1) }}% | - |

{% if cmp.regressions %}
## Regressions ({{ cmp.regressions | length }})
{% for cid in cmp.regressions %}- {{ cid }}
{% endfor %}{% endif %}

{% if cmp.improvements %}
## Improvements ({{ cmp.improvements | length }})
{% for cid in cmp.improvements %}- {{ cid }}
{% endfor %}{% endif %}

## Per-case Delta

| Case | Run A | Run B | Delta | Status |
|------|-------|-------|-------|--------|
{% for c in cmp.cases -%}
| {{ c.case_id }} | {{ (c.score_a * 100) | round(1) }}% | {{ (c.score_b * 100) | round(1) }}% | {{ "%+.1f" | format(c.delta * 100) }}% | {{ c.status_change }} |
{% endfor %}
"""


def render_comparison_md(cmp: ComparisonResult) -> str:
    env = Environment(loader=BaseLoader(), autoescape=False)
    return env.from_string(_COMPARE_MD).render(cmp=cmp)
