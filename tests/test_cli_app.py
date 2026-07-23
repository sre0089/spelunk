import json
from pathlib import Path

from pytest import MonkeyPatch
from typer.testing import CliRunner

import spelunk.cli.app as cli_app
from spelunk.capture import ActivationBatch
from spelunk.domain import CheckpointId, DatasetId, DatasetRef, LayerId, ModelId, ModelRef, SampleId
from spelunk.services import Session
from spelunk.storage import NumpyShardActivationStore

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


def test_default_command_launches_tui(monkeypatch: MonkeyPatch) -> None:
    launched = False

    def fake_run_tui() -> None:
        nonlocal launched
        launched = True

    monkeypatch.setattr(cli_app, "run_tui", fake_run_tui)

    result = runner.invoke(cli_app.app, [])

    assert result.exit_code == 0
    assert launched


def test_doctor_reports_basic_status() -> None:
    result = runner.invoke(cli_app.app, ["doctor"])

    assert result.exit_code == 0
    assert "Spelunk doctor" in result.output
    assert "Python package: importable" in result.output


def test_open_prints_run_summary(tmp_path: Path) -> None:
    run = _run(tmp_path)

    result = runner.invoke(cli_app.app, ["open", str(run)])

    assert result.exit_code == 0
    assert "Run: run-001" in result.output
    assert "Model: Tiny AE" in result.output


def test_scan_json_uses_session_service(tmp_path: Path) -> None:
    run = _run(tmp_path)

    result = runner.invoke(cli_app.app, ["scan", str(run), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["run"]["id"] == "run-001"
    assert payload["run"]["model"]["framework"] == "pytorch"
    assert payload["diagnostics"] == []


def test_scan_json_includes_diagnostics(tmp_path: Path) -> None:
    run = _run(tmp_path)
    session = Session.open(run)
    store = NumpyShardActivationStore(session.root / "activations")
    store.write_batch(
        ActivationBatch(
            run_id=session.run_id,
            checkpoint_id=CheckpointId("ckpt-001"),
            layer_id=LayerId("encoder"),
            sample_ids=(SampleId("sample-0"),),
            array=[[0.0, 0.0]],
            shape=(1, 2),
            dtype="float32",
        )
    )

    result = runner.invoke(cli_app.app, ["scan", str(run), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["layers"][0]["id"] == "encoder"
    assert payload["diagnostics"][0]["severity"] == "critical"
    assert "inactive" in payload["diagnostics"][0]["conclusion"]


def test_report_json_outputs_manifest_summary(tmp_path: Path) -> None:
    run = _run(tmp_path)

    result = runner.invoke(cli_app.app, ["report", str(run), "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["run_id"] == "run-001"
    assert payload["model"]["name"] == "Tiny AE"


def test_missing_run_exits_with_error(tmp_path: Path) -> None:
    result = runner.invoke(cli_app.app, ["scan", str(tmp_path / "missing.spelunk")])

    assert result.exit_code == 1
    assert "No Spelunk manifest" in result.output


def test_future_commands_fail_explicitly(tmp_path: Path) -> None:
    run = _run(tmp_path)

    capture = runner.invoke(cli_app.app, ["capture", "capture.toml"])
    compare = runner.invoke(cli_app.app, ["compare", str(run), str(run)])
    inspect = runner.invoke(
        cli_app.app,
        ["inspect", str(run), "--layer", "encoder", "--feature", "0"],
    )

    assert capture.exit_code == 1
    assert "Capture config execution is scheduled for M7" in capture.output
    assert compare.exit_code == 1
    assert "Run comparison is not implemented" in compare.output
    assert inspect.exit_code == 1
    assert "Feature inspection is scheduled" in inspect.output
