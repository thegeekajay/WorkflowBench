"""CLI entrypoint for WorkflowBench."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from workflowbench import __version__


@click.group()
@click.version_option(__version__, prog_name="workflowbench")
def main():
    """WorkflowBench — benchmark harness for AI-driven business workflows."""


@main.command()
@click.argument("cases_dir", type=click.Path(exists=True))
@click.option("--adapter", "-a", default="echo", help="Adapter name: openai, anthropic, echo")
@click.option("--model", "-m", default=None, help="Model name to pass to the adapter")
@click.option("--output", "-o", default="reports", help="Output directory for reports")
@click.option("--run-id", default=None, help="Custom run identifier")
@click.option("--format", "formats", multiple=True, default=("html", "md", "json"),
              type=click.Choice(["html", "md", "json"]), help="Report formats to generate")
def run(cases_dir: str, adapter: str, model: str | None, output: str, run_id: str | None,
        formats: tuple[str, ...]):
    """Run a benchmark suite against a provider adapter."""
    from workflowbench.adapters import get_adapter
    from workflowbench.runner import run_benchmark, save_run_json
    from workflowbench.reporter import save_html, save_markdown

    kwargs = {}
    if model:
        kwargs["model"] = model

    try:
        adp = get_adapter(adapter, **kwargs)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    click.echo(f"Running WorkflowBench with adapter '{adp.name}' on {cases_dir} ...")
    bench = run_benchmark(cases_dir, adp, run_id=run_id)

    output_dir = Path(output)
    generated: list[str] = []
    if "json" in formats:
        p = save_run_json(bench, output_dir)
        generated.append(str(p))
    if "md" in formats:
        p = save_markdown(bench, output_dir)
        generated.append(str(p))
    if "html" in formats:
        p = save_html(bench, output_dir)
        generated.append(str(p))

    click.echo()
    click.echo(f"  Cases:      {bench.cases_total}")
    click.echo(f"  Passed:     {bench.cases_passed}")
    click.echo(f"  Failed:     {bench.cases_failed}")
    click.echo(f"  Pass rate:  {bench.pass_rate * 100:.1f}%")
    click.echo(f"  Score:      {bench.overall_score * 100:.1f}%")
    click.echo(f"  Latency:    {bench.total_latency_ms:.0f}ms")
    click.echo(f"  Cost:       ${bench.total_cost_usd:.4f}")
    click.echo()
    for p in generated:
        click.echo(f"  -> {p}")
    click.echo()

    if bench.failure_clusters:
        click.echo("  Failure clusters:")
        for cluster, ids in bench.failure_clusters.items():
            click.echo(f"    {cluster}: {', '.join(ids)}")
        click.echo()


@main.command()
@click.argument("run_a", type=click.Path(exists=True))
@click.argument("run_b", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="Write comparison markdown to file")
def compare(run_a: str, run_b: str, output: str | None):
    """Compare two benchmark run JSON files."""
    from workflowbench.compare import load_run_json, compare_runs, render_comparison_md

    a = load_run_json(run_a)
    b = load_run_json(run_b)
    cmp = compare_runs(a, b)
    md = render_comparison_md(cmp)

    if output:
        Path(output).write_text(md)
        click.echo(f"Comparison saved to {output}")
    else:
        click.echo(md)


@main.command()
@click.argument("cases_dir", type=click.Path(exists=True))
def validate(cases_dir: str):
    """Validate YAML cases without running them."""
    from workflowbench.schema import load_suite

    try:
        cases = load_suite(cases_dir)
    except Exception as e:
        click.echo(f"Validation failed: {e}", err=True)
        sys.exit(1)

    click.echo(f"Validated {len(cases)} cases:")
    for c in cases:
        click.echo(f"  {c.id}: {c.name} [{c.category}]")


if __name__ == "__main__":
    main()
