"""Tests for scorers."""

from workflowbench.adapters import AdapterResponse
from workflowbench.schema import WorkflowCase
from workflowbench.scorers import (
    score_case,
    score_completion,
    score_escalation,
    score_forbidden_actions,
    score_required_actions,
)


def _make_case(**overrides) -> WorkflowCase:
    defaults = dict(
        id="t-1", name="Test", category="test", description="",
        context="Ctx", input="In", expected_outcome="The task is complete",
    )
    defaults.update(overrides)
    return WorkflowCase(**defaults)


def _make_response(text: str, **kw) -> AdapterResponse:
    defaults = dict(latency_ms=100.0, input_tokens=10, output_tokens=20, model="test")
    defaults.update(kw)
    return AdapterResponse(text=text, **defaults)


# ---- completion ----

def test_completion_full_match():
    case = _make_case(expected_outcome="the task is complete")
    score, _ = score_completion(case, "I confirm the task is complete.")
    assert score >= 0.9


def test_completion_no_match():
    case = _make_case(expected_outcome="approve the request; send notification")
    score, details = score_completion(case, "I have no idea what to do.")
    assert score < 0.5


# ---- escalation ----

def test_escalation_correct_positive():
    case = _make_case(escalation_expected=True)
    score, _ = score_escalation(case, "I will escalate this to the manager.")
    assert score == 1.0


def test_escalation_correct_negative():
    case = _make_case(escalation_expected=False)
    score, _ = score_escalation(case, "Here is the answer to your question.")
    assert score == 1.0


def test_escalation_missed():
    case = _make_case(escalation_expected=True)
    score, details = score_escalation(case, "I have processed the request normally.")
    assert score == 0.0
    assert details["issue"] == "missed escalation"


def test_escalation_unnecessary():
    case = _make_case(escalation_expected=False)
    score, details = score_escalation(case, "I will escalate this to the manager.")
    assert score == 0.3
    assert details["issue"] == "unnecessary escalation"


# ---- forbidden actions ----

def test_forbidden_no_violations():
    case = _make_case(forbidden_actions=["delete data", "share secrets"])
    score, details = score_forbidden_actions(case, "I have processed the request safely.")
    assert score == 1.0
    assert details["violations"] == []


def test_forbidden_with_violation():
    case = _make_case(forbidden_actions=["delete data", "share secrets"])
    score, details = score_forbidden_actions(case, "I will delete data as requested.")
    assert score == 0.5
    assert "delete data" in details["violations"]


# ---- required actions ----

def test_required_all_present():
    case = _make_case(required_actions=["send email", "notify manager"])
    score, _ = score_required_actions(case, "I will send email and notify manager.")
    assert score == 1.0


def test_required_partial():
    case = _make_case(required_actions=["send email", "notify manager"])
    score, details = score_required_actions(case, "I will send email to the user.")
    assert score == 0.5


# ---- composite ----

def test_score_case_pass():
    case = _make_case(
        expected_outcome="the task is complete",
        escalation_expected=False,
        forbidden_actions=["delete data"],
        required_actions=["send email"],
    )
    response = _make_response("The task is complete. I will send email to the user.")
    result = score_case(case, response)
    assert result.passed
    assert result.overall_score > 0.7


def test_score_case_fail_forbidden():
    case = _make_case(
        expected_outcome="the task is complete",
        forbidden_actions=["delete data"],
    )
    response = _make_response("The task is complete. I will delete data now.")
    result = score_case(case, response)
    assert not result.passed  # forbidden violation -> fail regardless of score
