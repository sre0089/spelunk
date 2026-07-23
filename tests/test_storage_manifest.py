import json
from pathlib import Path

import pytest

from spelunk.domain import (
    Checkpoint,
    CheckpointId,
    DatasetId,
    DatasetRef,
    Layer,
    LayerId,
    ModelId,
    ModelRef,
)
from spelunk.errors import ManifestError, SchemaVersionError
from spelunk.storage import (
    CURRENT_SCHEMA_VERSION,
    RunManifest,
    StorageBackendSpec,
    from_json,
    read_manifest,
    to_json,
    write_manifest,
)


def _manifest() -> RunManifest:
    model = ModelRef(
        id=ModelId("model-001"),
        name="Tiny AE",
        architecture_family="autoencoder",
        framework="pytorch",
    )
    dataset = DatasetRef(
        id=DatasetId("dataset-001"),
        name="sample",
        source_uri="file://sample.npy",
        kind="numpy",
    )
    checkpoint = Checkpoint(id=CheckpointId("ckpt-001"), label="initial")
    layer = Layer(
        id=LayerId("encoder"),
        name="encoder",
        path="encoder",
        kind="linear",
        shape=(16, 8),
    )
    return RunManifest.create(
        model=model,
        dataset=dataset,
        checkpoints=(checkpoint,),
        layers=(layer,),
        storage=StorageBackendSpec(kind="numpy-shards", root="activations"),
        provenance={"test": True},
    )


def test_manifest_round_trips_through_json() -> None:
    manifest = _manifest()
    restored = from_json(to_json(manifest))

    assert restored.schema_version == CURRENT_SCHEMA_VERSION
    assert restored.model.id == "model-001"
    assert restored.dataset.kind == "numpy"
    assert restored.checkpoints[0].id == "ckpt-001"
    assert restored.layers[0].shape == (16, 8)
    assert restored.storage.kind == "numpy-shards"
    assert restored.provenance == {"test": True}


def test_manifest_round_trips_through_file(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"

    write_manifest(path, _manifest())
    restored = read_manifest(path)

    assert json.loads(path.read_text())["schema_version"] == CURRENT_SCHEMA_VERSION
    assert restored.storage.root == "activations"


def test_manifest_rejects_unknown_schema_version() -> None:
    payload = to_json(_manifest())
    payload["schema_version"] = 999

    with pytest.raises(SchemaVersionError):
        from_json(payload)


def test_manifest_rejects_missing_required_field() -> None:
    payload = to_json(_manifest())
    del payload["model"]["name"]

    with pytest.raises(ManifestError, match="missing required field"):
        from_json(payload)


def test_manifest_rejects_unknown_storage_backend() -> None:
    payload = to_json(_manifest())
    payload["storage"]["kind"] = "sqlite"

    with pytest.raises(ManifestError, match="Unknown storage backend"):
        from_json(payload)


def test_manifest_accepts_zarr_storage_backend() -> None:
    payload = to_json(_manifest())
    payload["storage"]["kind"] = "zarr"

    restored = from_json(payload)

    assert restored.storage.kind == "zarr"


def test_manifest_rejects_invalid_shape() -> None:
    payload = to_json(_manifest())
    payload["layers"][0]["shape"] = [16, -1]

    with pytest.raises(ManifestError, match="non-negative"):
        from_json(payload)


def test_manifest_rejects_invalid_checkpoint_step() -> None:
    payload = to_json(_manifest())
    payload["checkpoints"][0]["step"] = "100"

    with pytest.raises(ManifestError, match="integer or null"):
        from_json(payload)


def test_read_manifest_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text("{not-json")

    with pytest.raises(ManifestError, match="not valid JSON"):
        read_manifest(path)
