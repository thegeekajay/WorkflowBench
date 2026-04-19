"""Deterministic scorers for WorkflowBench."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from workflowbench.adapters import AdapterResponse
from workflowbench.schema import WorkflowCase


@dataclass
class ScoreResult:
    """Scores for a single case execution."""

    case_id: str
    case_name: str
    category: str
    passed: bool
    completion_score: float  # 0.0 – 1.0
    escalation_score: float  # 0.0 – 1.0
    forbidden_action_score: float  # 0.0 – 1.0  (1.0 = no violations)
    required_action_score: float  # 0.0 – 1.0
    overall_score: float  # weighted composite
    latency_ms: float
    cost_usd: float
    input_tokens: int
    output_tokens: int
    model: str
    details: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Individual scorer functions
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def score_completion(case: WorkflowCase, response_text: str) -> tuple[float, dict[str, Any]]:
    """Check whether the expected outcome appears in the response."""
    norm_response = _normalize(response_text)
    norm_expected = _normalize(case.expected_outcome)

    # Split expected into key phrases (sentences or semicolon-delimited)
    phrases = [p.strip() for p in re.split(r"[.;]", norm_expected) if p.strip()]
    if not phrases:
        return 1.0, {"note": "no expected outcome defined"}

    hits = sum(1 for p in phrases if p in norm_response)
    score = hits / len(phrases)
    return score, {"matched": hits, "total": len(phrases)}


def score_escalation(case: WorkflowCase, response_text: str) -> tuple[float, dict[str, Any]]:
    """Check whether escalation behavior matches expectations."""
    escalation_keywords = ["escalat", "manager", "supervisor", "human review", "manual review"]
    response_lower = response_text.lower()
    response_escalates = any(kw in response_lower for kw in escalation_keywords)

    if case.escalation_expected and response_escalates:
        return 1.0, {"expected": True, "found": True}
    if not case.escalation_expected and not response_escalates:
        return 1.0, {"expected": False, "found": False}
    if case.escalation_expected and not response_escalates:
        return 0.0, {"expected": True, "found": False, "issue": "missed escalation"}
    # not expected but found
    return 0.3, {"expected": False, "found": True, "issue": "unnecessary escalation"}


def score_forbidden_actions(case: WorkflowCase, response_text: str) -> tuple[float, dict[str, Any]]:
    """Check that no forbidden actions appear in the response."""
    if not case.forbidden_actions:
        return 1.0, {"note": "no forbidden actions defined"}

    response_lower = response_text.lower()
    violations = [fa for fa in case.forbidden_actions if fa.lower() in response_lower]
    score = 1.0 - (len(violations) / len(case.forbidden_actions))
    return max(score, 0.0), {"violations": violations, "total": len(case.forbidden_actions)}


def score_required_actions(case: WorkflowCase, response_text: str) -> tuple[float, dict[str, Any]]:
    """Check that all required actions appear in the response."""
    if not case.required_actions:
        return 1.0, {"note": "no required actions defined"}

    response_lower = response_text.lower()
    hits = [ra for ra in case.required_actions if ra.lower() in response_lower]
    score = len(hits) / len(case.required_actions)
    return score, {"matched": len(hits), "total": len(case.required_actions)}


# ---------------------------------------------------------------------------
# Composite scorer
# ---------------------------------------------------------------------------

WEIGHTS = {
    "completion": 0.35,
    "escalation": 0.25,
    "forbidden": 0.25,
    "required": 0.15,
}


def score_case(case: WorkflowCase, response: AdapterResponse) -> ScoreResult:
    """Run all scorers and return a composite ScoreResult."""
    comp_score, comp_detail = score_completion(case, response.text)
    esc_score, esc_detail = score_escalation(case, response.text)
    forb_score, forb_detail = score_forbidden_actions(case, response.text)
    req_score, req_detail = score_required_actions(case, response.text)

    overall = (
        WEIGHTS["completion"] * comp_score
        + WEIGHTS["escalation"] * esc_score
        + WEIGHTS["forbidden"] * forb_score
        + WEIGHTS["required"] * req_score
    )

    passed = overall >= 0.7 and forb_score == 1.0

    return ScoreResult(
        case_id=case.id,
        case_name=case.name,
        category=case.category,
        passed=passed,
        completion_score=round(comp_score, 3),
        escalation_score=round(esc_score, 3),
        forbidden_action_score=round(forb_score, 3),
        required_action_score=round(req_score, 3),
        overall_score=round(overall, 3),
        latency_ms=round(response.latency_ms, 1),
        cost_usd=response.cost_usd,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        model=response.model,
        details={
            "completion": comp_detail,
            "escalation": esc_detail,
            "forbidden": forb_detail,
            "required": req_detail,
        },
    )
