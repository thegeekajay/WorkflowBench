# Changelog

All notable changes to WorkflowBench are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
WorkflowBench uses [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

Changes staged for the next release will appear here.

---

## [0.1.0] - 2026-04-19

Initial public release of WorkflowBench.

### Added

**Core framework**
- `WorkflowCase` dataclass with YAML loader (`workflowbench/schema.py`). Supports `id`, `name`, `category`, `context`, `input`, `expected_outcome`, `escalation_expected`, `escalation_reason`, `forbidden_actions`, `required_actions`, `tags`, `difficulty`, and `metadata` fields.
- `BenchmarkRun` dataclass capturing run-level aggregates: overall score, pass rate, latency, cost, and failure clusters.
- Deterministic scoring pipeline (`workflowbench/scorers.py`) with four dimensions:
  - **Completion** (35%) - phrase matching against `expected_outcome`
  - **Escalation** (25%) - keyword detection vs. `escalation_expected`
  - **Forbidden actions** (25%) - hard guardrail check
  - **Required actions** (15%) - partial-credit phrase presence check
- Pass threshold: overall score ≥ 70% **and** zero forbidden action violations.

**Adapters** (`workflowbench/adapters.py`)
- `echo` - returns prompt verbatim; zero cost, works offline
- `openai` - OpenAI Chat Completions API (requires `OPENAI_API_KEY`); default model `gpt-4o-mini`
- `anthropic` - Anthropic Messages API (requires `ANTHROPIC_API_KEY`); default model `claude-3-5-haiku-20241022`
- `BaseAdapter` base class for custom adapter implementations

**CLI** (`workflowbench/cli.py` via `click`)
- `workflowbench run` - execute a benchmark suite against an adapter; outputs HTML, Markdown, and/or JSON reports
- `workflowbench validate` - load and validate YAML cases without running model calls
- `workflowbench compare` - diff two JSON run files; surfaces regressions and improvements

**Reports** (`workflowbench/reporter.py`)
- HTML report with summary header, score card grid, per-case table, and failure clusters
- Markdown report for PR descriptions, wikis, and Notion
- JSON run file for CI pipelines and programmatic comparison

**Comparison** (`workflowbench/compare.py`)
- `compare_runs()` - computes per-case deltas, regressions, and improvements
- `render_comparison_md()` - renders a human-readable markdown diff

**Sample cases** (`cases/`)
- 20 enterprise-style YAML workflow cases across six categories:
  - `onboarding` (4): new hire, missing I-9 documentation, contractor, international hire
  - `approvals` (4): auto-approve threshold, manager routing, VP escalation, missing receipt
  - `policy` (4): training completion, overdue acknowledgment, policy rollout, whistleblower report
  - `access` (4): standard VPN request, production security review, termination revocation, annual recertification
  - `escalation` (3): customer complaint, security incident, false-positive control
  - `notifications` (2): maintenance window, SLA breach

**Website & documentation**
- Landing page (`index.html`) with dark/light mode toggle, logo swap, and benchmark flow infographic
- Developer documentation page (`docs.html`) with full CLI reference, schema field guide, scoring internals, adapter writing guide, and GitHub Actions CI example
- `assets/` folder containing SVG and PNG logo variants:
  - `workflowbench_logo_primary.svg` - for light backgrounds
  - `workflowbench_logo_dark.svg` - for dark backgrounds
  - `workflowbench_logo_mark.svg` - app icon and favicon
  - `style.css` - shared stylesheet extracted from the landing page
- `CHANGELOG.md` (this file)

**Demo & scripts**
- `scripts/generate_demo.py` - generates "good" vs "bad" agent demo reports in `demo_reports/`
- Pre-generated demo reports included for reference

**Tests** (`tests/`)
- `test_schema.py` - YAML loading, required field validation, `to_prompt()` output
- `test_scorers.py` - unit tests for all four scoring dimensions
- `test_runner.py` - end-to-end run with echo adapter
- `test_reporter.py` - HTML and Markdown report generation
- `test_compare.py` - comparison run diffing

**Project configuration**
- `pyproject.toml` with setuptools build, entry point `workflowbench`, and optional `[dev]` extras (`pytest`, `pytest-cov`, `ruff`)
- MIT license

### Known limitations in 0.1.0

- Completion scoring uses simple phrase matching; it does not use semantic similarity or an LLM judge. Phrases that paraphrase the expected outcome will be missed.
- Escalation detection relies on a fixed keyword list. Domain-specific escalation language may be missed.
- No streaming support for long-running agent responses.
- No parallel case execution; cases run sequentially.
- HTML and Markdown reports are generated from Python string templates, not a Jinja2 environment (planned for 0.2.0).

---

## Links

- [Repository](https://github.com/thegeekajay/WorkflowBench)
- [Documentation](docs.html)
- [Issues](https://github.com/thegeekajay/WorkflowBench/issues)

[Unreleased]: https://github.com/thegeekajay/WorkflowBench/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/thegeekajay/WorkflowBench/releases/tag/v0.1.0
