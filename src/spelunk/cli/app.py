"""Typer command-line application for Spelunk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, NoReturn, cast

import typer

from spelunk import __version__
from spelunk.errors import SpelunkError
from spelunk.services import Session, run_capture_config
from spelunk.services.results import (
    ComparisonResult,
    FeatureInspectionResult,
    RunSummary,
    ScanResult,
)
from spelunk.tui import run_tui

app = typer.Typer(
    add_completion=False,
    help="Terminal-native IDE for learned representations.",
    invoke_without_command=True,
    no_args_is_help=False,
)
config_app = typer.Typer(help="Inspect and manage Spelunk configuration.")
app.add_typer(config_app, name="config")


@app.callback()
def root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show the Spelunk version."),
) -> None:
    """Launch Spelunk or dispatch to a subcommand."""
    if version:
        typer.echo(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        run_tui()


@app.command()
def open(run: Path) -> None:
    """Open a run in the terminal application."""
    run_tui(run)


@app.command()
def scan(
    run: Path,
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Scan a run using the shared application service layer."""
    result = _open_session(run).scan()
    if json_output:
        typer.echo(json.dumps(_scan_to_json(result), indent=2, sort_keys=True))
        return

    _echo_summary(result.run)
    typer.echo(f"Diagnostics: {len(result.diagnostics)}")


@app.command()
def capture(config: Path) -> None:
    """Capture activations from a capture configuration file."""
    try:
        result = run_capture_config(config)
    except SpelunkError as error:
        _fail(str(error))
    typer.echo(f"Run: {result.run.run_id}")
    typer.echo(f"Checkpoint: {result.checkpoint_id}")
    typer.echo(f"Layers: {', '.join(str(layer) for layer in result.captured_layers)}")
    typer.echo(f"Samples: {result.captured_samples}")
    typer.echo(f"Batches: {result.batch_count}")


@app.command()
def compare(
    left_run: Path,
    right_run: Path,
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Compare two runs."""
    left = _open_session(left_run)
    right = _open_session(right_run)
    result = _compare_or_fail(left, right)
    if json_output:
        typer.echo(json.dumps(_comparison_to_json(result), indent=2, sort_keys=True))
        return
    comparison = result.comparison
    typer.echo(f"Left: {comparison.left_run_id}")
    typer.echo(f"Right: {comparison.right_run_id}")
    typer.echo(f"Layer matches: {len(comparison.layer_matches)}")
    typer.echo(f"Metric deltas: {len(comparison.metric_deltas)}")
    typer.echo(f"Diagnostics: {len(comparison.diagnostics)}")


@app.command()
def report(
    run: Path,
    format: str = typer.Option("markdown", "--format", help="Report format: markdown or json."),
) -> None:
    """Generate a report for a run."""
    report_format = _report_format(format)
    result = _open_session(run).report(format=report_format)
    typer.echo(result.content)


@app.command()
def inspect(
    run: Path,
    layer: str = typer.Option(..., "--layer", help="Layer ID or path."),
    feature: str = typer.Option(..., "--feature", help="Feature ID or key."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Inspect a layer feature."""
    session = _open_session(run)
    try:
        result = session.inspect_feature(layer_id=layer, feature_id=feature)
    except SpelunkError as error:
        _fail(str(error))
    if json_output:
        typer.echo(json.dumps(_feature_inspection_to_json(result), indent=2, sort_keys=True))
        return
    typer.echo(f"Run: {result.run.run_id}")
    typer.echo(f"Layer: {result.feature.layer_id}")
    typer.echo(f"Feature: {result.feature.feature_id}")
    for statistic in result.feature.statistics:
        typer.echo(f"{statistic.metric}: {statistic.value}")
    if result.feature.top_examples:
        typer.echo("Top examples: " + ", ".join(str(item) for item in result.feature.top_examples))


@app.command()
def doctor() -> None:
    """Report basic environment status."""
    typer.echo("Spelunk doctor")
    typer.echo(f"Version: {__version__}")
    typer.echo("Python package: importable")


@config_app.command("show")
def config_show() -> None:
    """Show effective configuration."""
    typer.echo("{}")


def main() -> None:
    """Console script entrypoint."""
    app()


def _open_session(run: Path) -> Session:
    try:
        return Session.open(run)
    except SpelunkError as error:
        _fail(str(error))


def _compare_or_fail(left: Session, right: Session) -> ComparisonResult:
    try:
        return left.compare(right)
    except SpelunkError as error:
        _fail(str(error))


def _fail(message: str) -> NoReturn:
    typer.echo(f"Error: {message}")
    raise typer.Exit(code=1)


def _report_format(value: str) -> Literal["markdown", "json"]:
    if value not in ("markdown", "json"):
        _fail(f"Unsupported report format: {value}")
    return cast(Literal["markdown", "json"], value)


def _echo_summary(summary: RunSummary) -> None:
    typer.echo(f"Run: {summary.run_id}")
    typer.echo(f"Model: {summary.model.name}")
    typer.echo(f"Dataset: {summary.dataset.name}")
    typer.echo(f"Checkpoints: {summary.checkpoint_count}")
    typer.echo(f"Layers: {summary.layer_count}")


def _scan_to_json(result: ScanResult) -> dict[str, object]:
    return {
        "run": {
            "id": result.run.run_id,
            "model": {
                "id": result.run.model.id,
                "name": result.run.model.name,
                "architecture_family": result.run.model.architecture_family,
                "framework": result.run.model.framework,
            },
            "dataset": {
                "id": result.run.dataset.id,
                "name": result.run.dataset.name,
                "kind": result.run.dataset.kind,
                "source_uri": result.run.dataset.source_uri,
            },
            "checkpoint_count": result.run.checkpoint_count,
            "layer_count": result.run.layer_count,
            "storage_backend": result.run.storage_backend,
        },
        "layers": [
            {
                "id": summary.layer_id,
                "activation_count": summary.activation_count,
                "feature_count": summary.feature_count,
                "statistics": [
                    {
                        "metric": statistic.metric,
                        "value": statistic.value,
                        "sample_count": statistic.sample_count,
                    }
                    for statistic in summary.statistics
                ],
            }
            for summary in result.layers
        ],
        "diagnostics": [
            {
                "id": diagnostic.id,
                "name": diagnostic.name,
                "subject_id": diagnostic.subject_id,
                "subject_type": diagnostic.subject_type,
                "severity": diagnostic.severity,
                "conclusion": diagnostic.conclusion,
                "explanation": diagnostic.explanation,
                "evidence": [
                    {"label": item.label, "value": item.value}
                    for item in diagnostic.evidence
                ],
            }
            for diagnostic in result.diagnostics
        ],
    }


def _comparison_to_json(result: ComparisonResult) -> dict[str, object]:
    comparison = result.comparison
    return {
        "left_run_id": comparison.left_run_id,
        "right_run_id": comparison.right_run_id,
        "layer_matches": [
            {
                "left_layer_id": match.left_layer_id,
                "right_layer_id": match.right_layer_id,
                "confidence": match.confidence,
            }
            for match in comparison.layer_matches
        ],
        "metric_deltas": [
            {
                "subject_id": delta.subject_id,
                "metric": delta.metric,
                "left_value": delta.left_value,
                "right_value": delta.right_value,
                "delta": delta.delta,
            }
            for delta in comparison.metric_deltas
        ],
        "diagnostics": [
            {
                "id": diagnostic.id,
                "name": diagnostic.name,
                "subject_id": diagnostic.subject_id,
                "subject_type": diagnostic.subject_type,
                "severity": diagnostic.severity,
                "conclusion": diagnostic.conclusion,
            }
            for diagnostic in comparison.diagnostics
        ],
    }


def _feature_inspection_to_json(result: FeatureInspectionResult) -> dict[str, object]:
    return {
        "run_id": result.run.run_id,
        "layer_id": result.feature.layer_id,
        "feature_id": result.feature.feature_id,
        "statistics": [
            {
                "metric": statistic.metric,
                "value": statistic.value,
                "sample_count": statistic.sample_count,
            }
            for statistic in result.feature.statistics
        ],
        "top_examples": list(result.feature.top_examples),
    }
