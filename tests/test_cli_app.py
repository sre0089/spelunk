import json
from pathlib import Path

from typer.testing import CliRunner

from spelunk.cli.app import app
from spelunk.domain import DatasetId, DatasetRef, ModelId, ModelRef
from spelunk.services import Session

runner = CliRunner()


def _model() -> ModelRef:
    return ModelRef(
        id=ModelId("model-001"),
        name="Tiny AE",
        architecture_family="autoencoder",
        framework="pytorch",
    )


def _dataset() -> DatasetRef:
    return DatasetRef(
        id=DatasetId("dataset-001"),
        name="sample",
        source_uri="file://sample.npy",
        kind="numpy",
    )


def _run(tmp_path: Path) -> Path:
    root = tmp_path / "run-001.spelunk"
    Session.create(root, model=_model(), dataset=_dataset())
    return root


def test_default_command_shows_project_picker_placeholder() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "project picker is scheduled for M5" in result.output


def test_doctor_reports_basic_status() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Spelunk doctor" in result.output
    assert "Python package: importable" in result.output


def test_open_prints_run_summary(tmp_path: Path) -> None:
    run = _run(tmp_path)

    result = runner.invoke(app, ["open", str(run)])

    assert result.exit_code == 0
    assert "Run: run-001" in result.output
    assert "Model: Tiny AE" in result.output


def test_scan_json_uses_session_service(tmp_path: Path) -> None:
    run = _run(tmp_path)

    result = runner.invoke(app, ["scan", str(run), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["run"]["id"] == "run-001"
    assert payload["run"]["model"]["framework"] == "pytorch"
    assert payload["diagnostics"] == []


def test_report_json_outputs_manifest_summary(tmp_path: Path) -> None:
    run = _run(tmp_path)

    result = runner.invoke(app, ["report", str(run), "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["run_id"] == "run-001"
    assert payload["model"]["name"] == "Tiny AE"


def test_missing_run_exits_with_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["scan", str(tmp_path / "missing.spelunk")])

    assert result.exit_code == 1
    assert "No Spelunk manifest" in result.output


def test_future_commands_fail_explicitly(tmp_path: Path) -> None:
    run = _run(tmp_path)

    capture = runner.invoke(app, ["capture", "capture.toml"])
    compare = runner.invoke(app, ["compare", str(run), str(run)])
    inspect = runner.invoke(app, ["inspect", str(run), "--layer", "encoder", "--feature", "0"])

    assert capture.exit_code == 1
    assert "Capture config execution is scheduled for M7" in capture.output
    assert compare.exit_code == 1
    assert "Run comparison is not implemented" in compare.output
    assert inspect.exit_code == 1
    assert "Feature inspection is scheduled" in inspect.output
