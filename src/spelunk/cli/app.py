"""Typer command-line application for Spelunk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal, NoReturn, cast

import typer

from spelunk import __version__
from spelunk.adapters.pytorch import PyTorchAdapter
from spelunk.config import CaptureConfig, remember_recent_run
from spelunk.errors import SpelunkError
from spelunk.services import Session, run_capture, run_capture_config
from spelunk.services.results import (
    CaptureResult,
    ComparisonResult,
    FeatureInspectionResult,
    RunSummary,
    ScanResult,
)
from spelunk.services.workflow import build_capture_config, load_model
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
    session = _open_session(run)
    remember_recent_run(session.root)
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
def capture(
    config: Annotated[
        Path | None,
        typer.Argument(help="Capture config path. Optional when direct flags are used."),
    ] = None,
    run: Annotated[
        Path | None,
        typer.Option("--run", help="Output run directory."),
    ] = None,
    model_path: Annotated[
        Path | None,
        typer.Option("--model-path", help="Python file containing the model factory."),
    ] = None,
    model_module: Annotated[
        str | None,
        typer.Option("--model-module", help="Importable module containing the model factory."),
    ] = None,
    factory: Annotated[
        str,
        typer.Option("--factory", help="Model factory callable name."),
    ] = "build_model",
    dataset: Annotated[
        Path | None,
        typer.Option("--dataset", help="Dataset file or image folder."),
    ] = None,
    layer_selectors: Annotated[
        list[str] | None,
        typer.Option("--layers", help="Layer selector to capture. Repeat for multiple layers."),
    ] = None,
    dataset_kind: Annotated[
        str | None,
        typer.Option("--dataset-kind", help="Dataset kind: numpy, csv, jsonl, or image-folder."),
    ] = None,
    storage_backend: Annotated[
        str,
        typer.Option("--storage-backend", help="Storage backend: numpy-shards or zarr."),
    ] = "numpy-shards",
    batch_size: Annotated[
        int,
        typer.Option("--batch-size", help="Capture batch size."),
    ] = 32,
    max_samples: Annotated[
        int | None,
        typer.Option("--max-samples", help="Maximum samples to capture."),
    ] = None,
    model_id: Annotated[
        str,
        typer.Option("--model-id", help="Model identifier stored in the run manifest."),
    ] = "model",
    model_name: Annotated[
        str | None,
        typer.Option("--model-name", help="Display name stored in the run manifest."),
    ] = None,
    dataset_id: Annotated[
        str,
        typer.Option("--dataset-id", help="Dataset identifier stored in the run manifest."),
    ] = "dataset",
    dataset_name: Annotated[
        str | None,
        typer.Option("--dataset-name", help="Dataset display name stored in the run manifest."),
    ] = None,
    checkpoint_id: Annotated[
        str,
        typer.Option("--checkpoint-id", help="Checkpoint identifier."),
    ] = "ckpt-001",
    checkpoint_label: Annotated[
        str,
        typer.Option("--checkpoint-label", help="Checkpoint label."),
    ] = "initial",
) -> None:
    """Capture activations from config or direct workflow flags."""
    try:
        if config is not None:
            result = run_capture_config(config)
        else:
            capture_config = _capture_config_from_flags(
                run=run,
                model_path=model_path,
                model_module=model_module,
                factory=factory,
                dataset=dataset,
                layer_selectors=tuple(layer_selectors or ()),
                dataset_kind=dataset_kind,
                storage_backend=storage_backend,
                batch_size=batch_size,
                max_samples=max_samples,
                model_id=model_id,
                model_name=model_name,
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                checkpoint_id=checkpoint_id,
                checkpoint_label=checkpoint_label,
            )
            result = run_capture(capture_config)
    except SpelunkError as error:
        _fail(str(error))
    _echo_capture_result(result)


def _echo_capture_result(result: CaptureResult) -> None:
    typer.echo(f"Run: {result.run.run_id}")
    typer.echo(f"Checkpoint: {result.checkpoint_id}")
    typer.echo(f"Layers: {', '.join(str(layer) for layer in result.captured_layers)}")
    typer.echo(f"Samples: {result.captured_samples}")
    typer.echo(f"Batches: {result.batch_count}")


@app.command()
def layers(
    model_path: Annotated[
        Path | None,
        typer.Option("--model-path", help="Python file containing the model factory."),
    ] = None,
    model_module: Annotated[
        str | None,
        typer.Option("--model-module", help="Importable module containing the model factory."),
    ] = None,
    factory: Annotated[
        str,
        typer.Option("--factory", help="Model factory callable name."),
    ] = "build_model",
) -> None:
    """List valid PyTorch layer selectors for capture."""
    try:
        model = load_model(module=model_module, path=model_path, factory=factory)
        description = PyTorchAdapter(model).describe_model()
    except (SpelunkError, RuntimeError, TypeError) as error:
        _fail(str(error))
    if not description.layers:
        typer.echo("No named layers found.")
        return
    for layer in description.layers:
        shape = "x".join(str(part) for part in layer.shape) if layer.shape else "-"
        typer.echo(f"{layer.path}\t{layer.kind}\tshape={shape}\trole={layer.role}")


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


def _capture_config_from_flags(
    *,
    run: Path | None,
    model_path: Path | None,
    model_module: str | None,
    factory: str,
    dataset: Path | None,
    layer_selectors: tuple[str, ...],
    dataset_kind: str | None,
    storage_backend: str,
    batch_size: int,
    max_samples: int | None,
    model_id: str,
    model_name: str | None,
    dataset_id: str,
    dataset_name: str | None,
    checkpoint_id: str,
    checkpoint_label: str,
) -> CaptureConfig:
    if run is None:
        raise SpelunkError("Direct capture requires --run.")
    if model_path is None and model_module is None:
        raise SpelunkError("Direct capture requires --model-path or --model-module.")
    if dataset is None:
        raise SpelunkError("Direct capture requires --dataset.")
    return build_capture_config(
        run=run,
        model_path=model_path,
        model_module=model_module,
        factory=factory,
        dataset=dataset,
        layers=layer_selectors,
        storage_backend=storage_backend,
        model_id=model_id,
        model_name=model_name or _default_model_name(model_path, model_module),
        dataset_id=dataset_id,
        dataset_name=dataset_name or dataset.stem,
        dataset_kind=dataset_kind,
        checkpoint_id=checkpoint_id,
        checkpoint_label=checkpoint_label,
        batch_size=batch_size,
        max_samples=max_samples,
    )


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


def _default_model_name(model_path: Path | None, model_module: str | None) -> str:
    if model_path is not None:
        return model_path.stem
    if model_module is not None:
        return model_module.rsplit(".", maxsplit=1)[-1]
    return "model"


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
