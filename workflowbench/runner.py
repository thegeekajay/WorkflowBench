"""Runner — orchestrates case execution and scoring."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflowbench.adapters import BaseAdapter, AdapterResponse
from workflowbench.schema import WorkflowCase, load_suite
from workflowbench.scorers import ScoreResult, score_case


@dataclass
class BenchmarkRun:
    """Complete results of a benchmark suite run."""

    run_id: str
    adapter_name: str
    timestamp: str
    cases_total: int
    cases_passed: int
    cases_failed: int
    pass_rate: float
    overall_score: float
    total_latency_ms: float
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    results: list[ScoreResult]
    failure_clusters: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def _cluster_failures(results: list[ScoreResult]) -> dict[str, list[str]]:
    """Group failed cases by failure type."""
    clusters: dict[str, list[str]] = {}
    for r in results:
        if r.passed:
            continue
        reasons = []
        if r.completion_score < 0.5:
            reasons.append("low_completion")
        if r.escalation_score < 1.0:
            reasons.append("escalation_mismatch")
        if r.forbidden_action_score < 1.0:
            reasons.append("forbidden_action_violation")
        if r.required_action_score < 0.5:
            reasons.append("missing_required_action")
        if not reasons:
            reasons.append("below_threshold")
        for reason in reasons:
            clusters.setdefault(reason, []).append(r.case_id)
    return clusters


def run_benchmark(
    cases_dir: str | Path,
    adapter: BaseAdapter,
    run_id: str | None = None,
) -> BenchmarkRun:
    """Load cases, execute each, score, and return a BenchmarkRun."""
    cases = load_suite(cases_dir)
    if not cases:
        raise ValueError(f"No cases found in {cases_dir}")

    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    results: list[ScoreResult] = []
    for case in cases:
        prompt = case.to_prompt()
        try:
            response = adapter.execute(prompt, case_id=case.id)
        except Exception as exc:
            response = AdapterResponse(
                text=f"ERROR: {exc}",
                latency_ms=0.0,
                model=adapter.name,
            )
        result = score_case(case, response)
        results.append(result)

    passed = [r for r in results if r.passed]
    total_score = sum(r.overall_score for r in results) / len(results) if results else 0.0

    return BenchmarkRun(
        run_id=run_id,
        adapter_name=adapter.name,
        timestamp=datetime.now(timezone.utc).isoformat(),
        cases_total=len(results),
        cases_passed=len(passed),
        cases_failed=len(results) - len(passed),
        pass_rate=round(len(passed) / len(results), 3) if results else 0.0,
        overall_score=round(total_score, 3),
        total_latency_ms=round(sum(r.latency_ms for r in results), 1),
        total_cost_usd=round(sum(r.cost_usd for r in results), 6),
        total_input_tokens=sum(r.input_tokens for r in results),
        total_output_tokens=sum(r.output_tokens for r in results),
        results=results,
        failure_clusters=_cluster_failures(results),
    )


def save_run_json(run: BenchmarkRun, output_dir: str | Path) -> Path:
    """Persist run results as JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"run_{run.run_id}.json"
    with open(path, "w") as f:
        json.dump(run.to_dict(), f, indent=2, default=str)
    return path
