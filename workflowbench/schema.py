"""YAML case schema and loader for WorkflowBench."""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class WorkflowCase:
    """A single workflow benchmark scenario."""

    id: str
    name: str
    category: str
    description: str
    context: str
    input: str
    expected_outcome: str
    escalation_expected: bool = False
    escalation_reason: str = ""
    forbidden_actions: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    difficulty: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowCase:
        return cls(
            id=data["id"],
            name=data["name"],
            category=data.get("category", "general"),
            description=data.get("description", ""),
            context=data["context"],
            input=data["input"],
            expected_outcome=data["expected_outcome"],
            escalation_expected=data.get("escalation_expected", False),
            escalation_reason=data.get("escalation_reason", ""),
            forbidden_actions=data.get("forbidden_actions", []),
            required_actions=data.get("required_actions", []),
            tags=data.get("tags", []),
            difficulty=data.get("difficulty", "medium"),
            metadata=data.get("metadata", {}),
        )

    def to_prompt(self) -> str:
        """Build the prompt string sent to the model/agent."""
        parts = [
            f"## Context\n{self.context}",
            f"\n## Task\n{self.input}",
        ]
        if self.forbidden_actions:
            forbidden = "\n".join(f"- {a}" for a in self.forbidden_actions)
            parts.append(f"\n## Constraints\nYou must NOT do the following:\n{forbidden}")
        return "\n".join(parts)


def load_case(path: str | Path) -> WorkflowCase:
    """Load a single YAML case file."""
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return WorkflowCase.from_dict(data)


def load_suite(directory: str | Path) -> list[WorkflowCase]:
    """Load all YAML cases from a directory, sorted by id."""
    directory = Path(directory)
    cases = []
    for pattern in ("*.yaml", "*.yml"):
        for filepath in sorted(directory.glob(pattern)):
            cases.append(load_case(filepath))
    # deduplicate by id preserving order
    seen: set[str] = set()
    unique: list[WorkflowCase] = []
    for c in cases:
        if c.id not in seen:
            seen.add(c.id)
            unique.append(c)
    return unique
