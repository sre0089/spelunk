import json
from collections import OrderedDict
from pathlib import Path

import pytest
from pytest import MonkeyPatch
from typer.testing import CliRunner

import spelunk.cli.app as cli_app
from spelunk.capture import ActivationBatch
from spelunk.config import load_recent_runs
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


def _write_capture_config(
    tmp_path: Path,
    *,
    framework: str = "pytorch",
    layers: list[str] | None = None,
) -> Path:
    config_path = tmp_path / "capture.json"
    config_path.write_text(
        json.dumps(
            {
                "run": "run-001.spelunk",
                "model": {
                    "id": "model-001",
                    "name": "Tiny Torch",
                    "framework": framework,
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
                    "layers": layers or ["encoder"],
                    "checkpoint_id": "ckpt-001",
                    "checkpoint_label": "initial",
                },
            }
        )
    )
    return config_path


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
    monkeypatch.setenv("SPELUNK_CONFIG_HOME", str(tmp_path / "config"))

    def fake_run_tui(run_path: Path | None = None) -> None:
        if run_path is not None:
            launched.append(run_path)

    monkeypatch.setattr(cli_app, "run_tui", fake_run_tui)

    result = runner.invoke(cli_app.app, ["open", str(run)])

    assert result.exit_code == 0
    assert launched == [run]
    assert load_recent_runs() == (run.resolve(),)


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


def test_capture_accepts_direct_workflow_flags(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("torch")
    np.save(tmp_path / "samples.npy", np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32))
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

    result = runner.invoke(
        cli_app.app,
        [
            "capture",
            "--run",
            str(tmp_path / "run-001.spelunk"),
            "--model-path",
            str(model_path),
            "--factory",
            "build_model",
            "--dataset",
            str(tmp_path / "samples.npy"),
            "--layers",
            "encoder",
            "--batch-size",
            "2",
            "--max-samples",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "Run: run-001" in result.output
    assert "Layers: encoder" in result.output
    scan = Session.open(tmp_path / "run-001.spelunk").scan()
    assert scan.layers[0].layer_id == "encoder"


def test_capture_direct_flags_load_checkpoint_path(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    torch = pytest.importorskip("torch")
    np.save(tmp_path / "samples.npy", np.array([[1.0, 0.0]], dtype=np.float32))
    model_path = tmp_path / "model_factory.py"
    model_path.write_text(
        "\n".join(
            [
                "from collections import OrderedDict",
                "import torch",
                "",
                "def build_model():",
                "    model = torch.nn.Sequential(",
                "        OrderedDict([('encoder', torch.nn.Linear(2, 1, bias=False))])",
                "    )",
                "    torch.nn.init.zeros_(model.encoder.weight)",
                "    return model",
                "",
            ]
        )
    )
    model = torch.nn.Sequential(OrderedDict([("encoder", torch.nn.Linear(2, 1, bias=False))]))
    with torch.no_grad():
        model.encoder.weight.copy_(torch.tensor([[5.0, 0.0]]))
    checkpoint_path = tmp_path / "weights.pt"
    torch.save({"state_dict": model.state_dict()}, checkpoint_path)

    result = runner.invoke(
        cli_app.app,
        [
            "capture",
            "--run",
            str(tmp_path / "run-001.spelunk"),
            "--model-path",
            str(model_path),
            "--checkpoint-path",
            str(checkpoint_path),
            "--dataset",
            str(tmp_path / "samples.npy"),
            "--layers",
            "encoder",
            "--batch-size",
            "1",
        ],
    )

    assert result.exit_code == 0
    scan = Session.open(tmp_path / "run-001.spelunk").scan()
    statistic = next(item for item in scan.layers[0].statistics if item.metric == "activation_mean")
    assert statistic.value == 5.0


def test_capture_direct_flags_require_run() -> None:
    result = runner.invoke(cli_app.app, ["capture", "--layers", "encoder"])

    assert result.exit_code == 1
    assert "Direct capture requires --run" in result.output


def test_quickstart_captures_reports_and_prints_tui_command(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("torch")
    monkeypatch.setenv("SPELUNK_CONFIG_HOME", str(tmp_path / "config"))
    np.save(tmp_path / "samples.npy", np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32))
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

    result = runner.invoke(
        cli_app.app,
        [
            "quickstart",
            "--run",
            str(tmp_path / "run-001.spelunk"),
            "--model-path",
            str(model_path),
            "--dataset",
            str(tmp_path / "samples.npy"),
            "--layers",
            "encoder",
            "--batch-size",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "Run: run-001" in result.output
    assert "Markdown report:" in result.output
    assert "JSON report:" in result.output
    assert "Open TUI: spelunk open" in result.output
    assert (tmp_path / "run-001.spelunk" / "reports" / "report.md").exists()
    assert (tmp_path / "run-001.spelunk" / "reports" / "report.json").exists()
    assert load_recent_runs() == ((tmp_path / "run-001.spelunk").resolve(),)


def test_capture_config_loads_checkpoint_path(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    torch = pytest.importorskip("torch")
    np.save(tmp_path / "samples.npy", np.array([[1.0, 0.0]], dtype=np.float32))
    (tmp_path / "model_factory.py").write_text(
        "\n".join(
            [
                "from collections import OrderedDict",
                "import torch",
                "",
                "def build_model():",
                "    model = torch.nn.Sequential(",
                "        OrderedDict([('encoder', torch.nn.Linear(2, 1, bias=False))])",
                "    )",
                "    torch.nn.init.zeros_(model.encoder.weight)",
                "    return model",
                "",
            ]
        )
    )
    model = torch.nn.Sequential(OrderedDict([("encoder", torch.nn.Linear(2, 1, bias=False))]))
    with torch.no_grad():
        model.encoder.weight.copy_(torch.tensor([[7.0, 0.0]]))
    torch.save(model.state_dict(), tmp_path / "weights.pt")
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
                    "checkpoint_path": "weights.pt",
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
                    "checkpoint_label": "trained",
                },
            }
        )
    )

    result = runner.invoke(cli_app.app, ["capture", str(config_path)])

    assert result.exit_code == 0
    scan = Session.open(tmp_path / "run-001.spelunk").scan()
    statistic = next(item for item in scan.layers[0].statistics if item.metric == "activation_mean")
    assert statistic.value == 7.0


def test_init_writes_starter_capture_config(tmp_path: Path) -> None:
    output = tmp_path / "spelunk.json"

    result = runner.invoke(
        cli_app.app,
        [
            "init",
            "--output",
            str(output),
            "--run",
            "runs/demo.spelunk",
            "--model-path",
            "model_factory.py",
            "--dataset",
            "samples.csv",
            "--layers",
            "encoder",
        ],
    )

    assert result.exit_code == 0
    assert "Wrote" in result.output
    payload = json.loads(output.read_text())
    assert payload["run"] == "runs/demo.spelunk"
    assert payload["model"]["path"] == "model_factory.py"
    assert payload["dataset"]["kind"] == "csv"
    assert payload["capture"]["layers"] == ["encoder"]


def test_init_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    output = tmp_path / "spelunk.json"
    output.write_text("{}\n")

    result = runner.invoke(cli_app.app, ["init", "--output", str(output)])

    assert result.exit_code == 1
    assert "Pass --force to overwrite" in result.output
    assert output.read_text() == "{}\n"


def test_init_force_overwrites_existing_config(tmp_path: Path) -> None:
    output = tmp_path / "spelunk.json"
    output.write_text("{}\n")

    result = runner.invoke(cli_app.app, ["init", "--output", str(output), "--force"])

    assert result.exit_code == 0
    assert json.loads(output.read_text())["capture"]["layers"] == ["encoder"]


def test_layers_lists_model_layer_selectors(tmp_path: Path) -> None:
    pytest.importorskip("torch")
    model_path = tmp_path / "model_factory.py"
    model_path.write_text(
        "\n".join(
            [
                "from collections import OrderedDict",
                "import torch",
                "",
                "def build_model():",
                "    return torch.nn.Sequential(",
                "        OrderedDict([",
                "            ('encoder', torch.nn.Linear(2, 2)),",
                "            ('relu', torch.nn.ReLU()),",
                "        ])",
                "    )",
                "",
            ]
        )
    )

    result = runner.invoke(
        cli_app.app,
        ["layers", "--model-path", str(model_path), "--factory", "build_model"],
    )

    assert result.exit_code == 0
    assert "encoder\tLinear" in result.output
    assert "relu\tReLU" in result.output


def test_layers_requires_model_source() -> None:
    result = runner.invoke(cli_app.app, ["layers"])

    assert result.exit_code == 1
    assert "Model loading requires either --model-path or --model-module" in result.output


def test_capture_config_refuses_existing_run(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("torch")
    np.save(tmp_path / "samples.npy", np.array([[1.0, 2.0]], dtype=np.float32))
    (tmp_path / "model_factory.py").write_text(
        "\n".join(
            [
                "from collections import OrderedDict",
                "import torch",
                "",
                "def build_model():",
                "    return torch.nn.Sequential(",
                "        OrderedDict([('encoder', torch.nn.Linear(2, 2))])",
                "    )",
                "",
            ]
        )
    )
    config_path = _write_capture_config(tmp_path)

    first = runner.invoke(cli_app.app, ["capture", str(config_path)])
    second = runner.invoke(cli_app.app, ["capture", str(config_path)])

    assert first.exit_code == 0
    assert second.exit_code == 1
    assert "Capture run already exists" in second.output


def test_capture_config_reports_missing_dataset_source(tmp_path: Path) -> None:
    model_path = tmp_path / "model_factory.py"
    model_path.write_text(
        "\n".join(
            [
                "import torch",
                "",
                "def build_model():",
                "    return torch.nn.Linear(2, 2)",
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
                    "source": "missing.npy",
                },
                "capture": {
                    "layers": ["encoder"],
                    "checkpoint_id": "ckpt-001",
                    "checkpoint_label": "initial",
                },
            }
        )
    )

    result = runner.invoke(cli_app.app, ["capture", str(config_path)])

    assert result.exit_code == 1
    assert "Dataset source does not exist" in result.output


def test_capture_config_reports_malformed_json(tmp_path: Path) -> None:
    config_path = tmp_path / "capture.json"
    config_path.write_text("{not-json")

    result = runner.invoke(cli_app.app, ["capture", str(config_path)])

    assert result.exit_code == 1
    assert "Capture config is not valid JSON" in result.output


def test_capture_config_reports_unsupported_framework(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    np.save(tmp_path / "samples.npy", np.array([[1.0, 2.0]], dtype=np.float32))
    (tmp_path / "model_factory.py").write_text("def build_model():\n    return object()\n")
    config_path = _write_capture_config(tmp_path, framework="jax")

    result = runner.invoke(cli_app.app, ["capture", str(config_path)])

    assert result.exit_code == 1
    assert "Unsupported capture framework: jax" in result.output


def test_capture_config_reports_bad_model_factory_return(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("torch")
    np.save(tmp_path / "samples.npy", np.array([[1.0, 2.0]], dtype=np.float32))
    (tmp_path / "model_factory.py").write_text("def build_model():\n    return object()\n")
    config_path = _write_capture_config(tmp_path)

    result = runner.invoke(cli_app.app, ["capture", str(config_path)])

    assert result.exit_code == 1
    assert "Model factory did not return a PyTorch module" in result.output


def test_capture_config_reports_unknown_layer(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("torch")
    np.save(tmp_path / "samples.npy", np.array([[1.0, 2.0]], dtype=np.float32))
    (tmp_path / "model_factory.py").write_text(
        "\n".join(
            [
                "import torch",
                "",
                "def build_model():",
                "    return torch.nn.Sequential(torch.nn.Linear(2, 2))",
                "",
            ]
        )
    )
    config_path = _write_capture_config(tmp_path, layers=["encoder"])

    result = runner.invoke(cli_app.app, ["capture", str(config_path)])

    assert result.exit_code == 1
    assert "Unknown PyTorch layer selector" in result.output


def test_capture_config_reports_empty_dataset(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("torch")
    np.save(tmp_path / "samples.npy", np.empty((0, 2), dtype=np.float32))
    (tmp_path / "model_factory.py").write_text(
        "\n".join(
            [
                "from collections import OrderedDict",
                "import torch",
                "",
                "def build_model():",
                "    return torch.nn.Sequential(",
                "        OrderedDict([('encoder', torch.nn.Linear(2, 2))])",
                "    )",
                "",
            ]
        )
    )
    config_path = _write_capture_config(tmp_path)

    result = runner.invoke(cli_app.app, ["capture", str(config_path)])

    assert result.exit_code == 1
    assert "Capture dataset produced no samples" in result.output


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


def test_inspect_reports_out_of_range_feature(tmp_path: Path) -> None:
    run = _run(tmp_path)
    session = Session.open(run)
    NumpyShardActivationStore(session.root / "activations").write_batch(
        ActivationBatch(
            run_id=session.run_id,
            checkpoint_id=CheckpointId("ckpt-001"),
            layer_id=LayerId("encoder"),
            sample_ids=(SampleId("sample-0"),),
            array=[[1.0, 5.0]],
            shape=(1, 2),
            dtype="float32",
        )
    )

    result = runner.invoke(
        cli_app.app,
        ["inspect", str(run), "--layer", "encoder", "--feature", "9"],
    )

    assert result.exit_code == 1
    assert "Feature index 9 is out of range" in result.output


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
