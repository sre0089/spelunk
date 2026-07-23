import json
from pathlib import Path

import pytest

from spelunk import CapturePlan, Session
from spelunk.capture import ActivationBatch
from spelunk.domain import (
    Checkpoint,
    CheckpointId,
    DatasetId,
    DatasetRef,
    LayerId,
    ModelId,
    ModelRef,
    SampleId,
)
from spelunk.errors import StorageError, UnsupportedOperationError
from spelunk.storage import NumpyShardActivationStore


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


def test_session_create_writes_and_opens_manifest(tmp_path: Path) -> None:
    root = tmp_path / "run-001.spelunk"
    checkpoint = Checkpoint(id=CheckpointId("ckpt-001"), label="initial")

    created = Session.create(
        root,
        model=_model(),
        dataset=_dataset(),
        checkpoints=(checkpoint,),
        storage_backend="zarr",
    )
    opened = Session.open(root)

    assert (root / "manifest.json").exists()
    assert (root / "activations").is_dir()
    assert (root / "reports").is_dir()
    assert created.run_id == "run-001"
    assert opened.summary().storage_backend == "zarr"
    assert opened.summary().checkpoint_count == 1


def test_session_can_open_manifest_file_path(tmp_path: Path) -> None:
    root = tmp_path / "run-001.spelunk"
    Session.create(root, model=_model(), dataset=_dataset())

    opened = Session.open(root / "manifest.json")

    assert opened.root == root
    assert opened.run_id == "run-001"


def test_session_open_requires_manifest(tmp_path: Path) -> None:
    with pytest.raises(StorageError, match="No Spelunk manifest"):
        Session.open(tmp_path / "missing.spelunk")


def test_session_scan_returns_manifest_backed_summary(tmp_path: Path) -> None:
    session = Session.create(tmp_path / "run-001.spelunk", model=_model(), dataset=_dataset())

    result = session.scan()

    assert result.run.model.name == "Tiny AE"
    assert result.run.dataset.kind == "numpy"
    assert result.layers == ()
    assert result.diagnostics == ()


def test_session_scan_returns_stored_layer_summaries_and_diagnostics(tmp_path: Path) -> None:
    session = Session.create(tmp_path / "run-001.spelunk", model=_model(), dataset=_dataset())
    store = NumpyShardActivationStore(session.root / "activations")
    store.write_batch(
        ActivationBatch(
            run_id=session.run_id,
            checkpoint_id=CheckpointId("ckpt-001"),
            layer_id=LayerId("encoder"),
            sample_ids=(SampleId("sample-0"), SampleId("sample-1")),
            array=[[0.0, 0.0], [0.0, 0.0]],
            shape=(2, 2),
            dtype="float32",
        )
    )

    result = session.scan()

    assert len(result.layers) == 1
    assert result.layers[0].layer_id == "encoder"
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].severity == "critical"
    assert "inactive" in result.diagnostics[0].conclusion


def test_session_report_returns_markdown_summary(tmp_path: Path) -> None:
    session = Session.create(tmp_path / "run-001.spelunk", model=_model(), dataset=_dataset())

    result = session.report(format="markdown")

    assert result.format == "markdown"
    assert result.path == session.root / "reports" / "report.md"
    assert result.path.read_text() == result.content
    assert "# Spelunk report for run-001" in result.content
    assert "- Model: Tiny AE" in result.content
    assert "No stored activation layers." in result.content


def test_session_report_returns_json_summary(tmp_path: Path) -> None:
    session = Session.create(tmp_path / "run-001.spelunk", model=_model(), dataset=_dataset())

    result = session.report(format="json")

    assert result.format == "json"
    assert result.path == session.root / "reports" / "report.json"
    assert result.path.read_text() == result.content
    assert '"run_id": "run-001"' in result.content
    assert '"framework": "pytorch"' in result.content
    assert '"layers": []' in result.content


def test_session_report_includes_scan_evidence(tmp_path: Path) -> None:
    session = Session.create(tmp_path / "run-001.spelunk", model=_model(), dataset=_dataset())
    store = NumpyShardActivationStore(session.root / "activations")
    store.write_batch(
        ActivationBatch(
            run_id=session.run_id,
            checkpoint_id=CheckpointId("ckpt-001"),
            layer_id=LayerId("encoder"),
            sample_ids=(SampleId("sample-0"), SampleId("sample-1")),
            array=[[0.0, 0.0], [0.0, 0.0]],
            shape=(2, 2),
            dtype="float32",
        )
    )

    markdown = session.report(format="markdown")
    json_report = session.report(format="json")
    payload = json.loads(json_report.content)

    assert "### encoder" in markdown.content
    assert "- Severity: CRITICAL" in markdown.content
    assert "inactive" in markdown.content
    assert payload["layers"][0]["id"] == "encoder"
    assert payload["layers"][0]["activation_count"] == 2
    assert payload["diagnostics"][0]["severity"] == "critical"
    assert "inactive" in payload["diagnostics"][0]["conclusion"]


def test_future_service_contracts_fail_explicitly(tmp_path: Path) -> None:
    session = Session.create(tmp_path / "run-001.spelunk", model=_model(), dataset=_dataset())

    with pytest.raises(UnsupportedOperationError, match="Capture is not implemented"):
        session.capture(CapturePlan(layers=("encoder",), dataset="sample"))

    with pytest.raises(UnsupportedOperationError, match="Run comparison is not implemented"):
        session.compare(session)
