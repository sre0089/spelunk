import json
from pathlib import Path

import pytest
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


def test_open_launches_tui_for_run(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    run = _run(tmp_path)
    launched: list[Path] = []

    def fake_run_tui(run_path: Path | None = None) -> None:
        if run_path is not None:
            launched.append(run_path)

    monkeypatch.setattr(cli_app, "run_tui", fake_run_tui)

    result = runner.invoke(cli_app.app, ["open", str(run)])

    assert result.exit_code == 0
    assert launched == [run]


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


def test_capture_config_executes_pytorch_capture(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("torch")
    data_path = tmp_path / "samples.npy"
    np.save(data_path, np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32))
    model_path = tmp_path / "model_factory.py"
    model_path.write_text(
        "\n".join(
            [
                "from collections import OrderedDict",
                "import torch",
                "",
                "def build_model():",
                "    return torch.nn.Sequential(",
                "        OrderedDict([('encoder', torch.nn.Linear(2, 2, bias=False))])",
                "    )",
                "",
            ]
        )
    )
    config_path = tmp_path / "capture.json"
    config_path.write_text(
        json.dumps(
            {
                "run": "run-001.spelunk",
                "model": {
                    "id": "model-001",
                    "name": "Tiny Torch",
                    "framework": "pytorch",
                    "path": "model_factory.py",
                    "factory": "build_model",
                },
                "dataset": {
                    "id": "dataset-001",
                    "name": "samples",
                    "kind": "numpy",
                    "source": "samples.npy",
                },
                "capture": {
                    "layers": ["encoder"],
                    "checkpoint_id": "ckpt-001",
                    "checkpoint_label": "initial",
                    "batch_size": 2,
                    "max_samples": 2,
                },
            }
        )
    )

    result = runner.invoke(cli_app.app, ["capture", str(config_path)])

    assert result.exit_code == 0
    assert "Run: run-001" in result.output
    assert "Layers: encoder" in result.output
    assert "Samples: 2" in result.output
    scan = Session.open(tmp_path / "run-001.spelunk").scan()
    assert scan.layers[0].layer_id == "encoder"
    assert scan.layers[0].activation_count == 2


def test_report_json_outputs_manifest_summary(tmp_path: Path) -> None:
    run = _run(tmp_path)

    result = runner.invoke(cli_app.app, ["report", str(run), "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["run_id"] == "run-001"
    assert payload["model"]["name"] == "Tiny AE"


def test_compare_json_outputs_metric_deltas(tmp_path: Path) -> None:
    left = _run(tmp_path / "left")
    right = _run(tmp_path / "right")
    left_session = Session.open(left)
    right_session = Session.open(right)
    NumpyShardActivationStore(left_session.root / "activations").write_batch(
        ActivationBatch(
            run_id=left_session.run_id,
            checkpoint_id=CheckpointId("ckpt-001"),
            layer_id=LayerId("encoder"),
            sample_ids=(SampleId("sample-0"),),
            array=[[1.0, 2.0]],
            shape=(1, 2),
            dtype="float32",
        )
    )
    NumpyShardActivationStore(right_session.root / "activations").write_batch(
        ActivationBatch(
            run_id=right_session.run_id,
            checkpoint_id=CheckpointId("ckpt-001"),
            layer_id=LayerId("encoder"),
            sample_ids=(SampleId("sample-0"), SampleId("sample-1")),
            array=[[2.0, 4.0], [6.0, 8.0]],
            shape=(2, 2),
            dtype="float32",
        )
    )

    result = runner.invoke(cli_app.app, ["compare", str(left), str(right), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["left_run_id"] == "run-001"
    assert payload["right_run_id"] == "run-001"
    assert payload["layer_matches"][0]["left_layer_id"] == "encoder"
    assert any(delta["metric"] == "activation_mean" for delta in payload["metric_deltas"])


def test_inspect_json_outputs_feature_statistics(tmp_path: Path) -> None:
    run = _run(tmp_path)
    session = Session.open(run)
    NumpyShardActivationStore(session.root / "activations").write_batch(
        ActivationBatch(
            run_id=session.run_id,
            checkpoint_id=CheckpointId("ckpt-001"),
            layer_id=LayerId("encoder"),
            sample_ids=(SampleId("sample-0"), SampleId("sample-1")),
            array=[[1.0, 5.0], [2.0, 9.0]],
            shape=(2, 2),
            dtype="float32",
        )
    )

    result = runner.invoke(
        cli_app.app,
        ["inspect", str(run), "--layer", "encoder", "--feature", "1", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["layer_id"] == "encoder"
    assert payload["feature_id"] == "1"
    assert payload["top_examples"][0] == "sample-1"
    assert any(statistic["metric"] == "activation_mean" for statistic in payload["statistics"])


def test_missing_run_exits_with_error(tmp_path: Path) -> None:
    result = runner.invoke(cli_app.app, ["scan", str(tmp_path / "missing.spelunk")])

    assert result.exit_code == 1
    assert "No Spelunk manifest" in result.output


def test_future_commands_fail_explicitly(tmp_path: Path) -> None:
    run = _run(tmp_path)

    inspect = runner.invoke(
        cli_app.app,
        ["inspect", str(run), "--layer", "encoder", "--feature", "bad"],
    )

    assert inspect.exit_code == 1
    assert "Feature ID must be an integer index" in inspect.output
