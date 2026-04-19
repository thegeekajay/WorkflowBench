"""Tests for YAML case schema and loader."""

from pathlib import Path

from workflowbench.schema import WorkflowCase, load_case, load_suite

CASES_DIR = Path(__file__).resolve().parent.parent / "cases"


def test_workflowcase_from_dict():
    data = {
        "id": "test-001",
        "name": "Test case",
        "category": "testing",
        "description": "A test",
        "context": "You are a test assistant.",
        "input": "Do the thing.",
        "expected_outcome": "The thing is done.",
        "escalation_expected": False,
        "forbidden_actions": ["skip testing"],
        "required_actions": ["run tests"],
    }
    case = WorkflowCase.from_dict(data)
    assert case.id == "test-001"
    assert case.name == "Test case"
    assert case.category == "testing"
    assert case.forbidden_actions == ["skip testing"]
    assert case.required_actions == ["run tests"]


def test_to_prompt_includes_context_and_input():
    case = WorkflowCase(
        id="t-1", name="T", category="test",
        description="", context="Context here.", input="Input here.",
        expected_outcome="Outcome.",
    )
    prompt = case.to_prompt()
    assert "Context here." in prompt
    assert "Input here." in prompt


def test_to_prompt_includes_constraints():
    case = WorkflowCase(
        id="t-2", name="T", category="test",
        description="", context="C", input="I",
        expected_outcome="O",
        forbidden_actions=["delete data", "share secrets"],
    )
    prompt = case.to_prompt()
    assert "delete data" in prompt
    assert "share secrets" in prompt
    assert "Constraints" in prompt


def test_load_suite_from_cases_dir():
    cases = load_suite(CASES_DIR)
    assert len(cases) >= 15
    ids = [c.id for c in cases]
    assert "onb-001" in ids
    assert "apr-001" in ids
    assert "pol-001" in ids
    assert "acc-001" in ids
    assert "esc-001" in ids
    assert "not-001" in ids


def test_load_single_case():
    case = load_case(CASES_DIR / "onb-001.yaml")
    assert case.id == "onb-001"
    assert case.category == "onboarding"
    assert not case.escalation_expected
