"""Versioned local run manifest schemas."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, Literal, cast

from spelunk._version import __version__
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
from spelunk.domain.types import JsonObject
from spelunk.errors import ManifestError, SchemaVersionError

CURRENT_SCHEMA_VERSION: Final[int] = 1
StorageBackend = Literal["numpy-shards", "zarr"]


@dataclass(frozen=True, slots=True)
class StorageBackendSpec:
    kind: StorageBackend
    root: str
    options: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunManifest:
    schema_version: int
    spelunk_version: str
    created_at: datetime
    model: ModelRef
    dataset: DatasetRef
    checkpoints: tuple[Checkpoint, ...]
    layers: tuple[Layer, ...]
    storage: StorageBackendSpec
    provenance: JsonObject = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        model: ModelRef,
        dataset: DatasetRef,
        storage: StorageBackendSpec,
        checkpoints: Iterable[Checkpoint] = (),
        layers: Iterable[Layer] = (),
        provenance: JsonObject | None = None,
    ) -> RunManifest:
        return cls(
            schema_version=CURRENT_SCHEMA_VERSION,
            spelunk_version=__version__,
            created_at=datetime.now(UTC),
            model=model,
            dataset=dataset,
            checkpoints=tuple(checkpoints),
            layers=tuple(layers),
            storage=storage,
            provenance=provenance or {},
        )


def write_manifest(path: Path, manifest: RunManifest) -> None:
    path.write_text(json.dumps(to_json(manifest), indent=2, sort_keys=True) + "\n")


def read_manifest(path: Path) -> RunManifest:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise ManifestError(f"Manifest is not valid JSON: {path}") from error
    return from_json(data)


def to_json(manifest: RunManifest) -> dict[str, Any]:
    payload = asdict(manifest)
    payload["created_at"] = manifest.created_at.isoformat()
    return payload


def from_json(data: Mapping[str, Any]) -> RunManifest:
    schema_version = data.get("schema_version")
    if schema_version != CURRENT_SCHEMA_VERSION:
        raise SchemaVersionError(
            f"Unsupported run manifest schema version: {schema_version!r}. "
            f"Expected {CURRENT_SCHEMA_VERSION}."
        )

    try:
        return RunManifest(
            schema_version=CURRENT_SCHEMA_VERSION,
            spelunk_version=_required_str(data, "spelunk_version"),
            created_at=_datetime_from_json(data, "created_at"),
            model=_model_from_json(_required_mapping(data, "model")),
            dataset=_dataset_from_json(_required_mapping(data, "dataset")),
            checkpoints=tuple(
                _checkpoint_from_json(_mapping(item, "checkpoint"))
                for item in _required_sequence(data, "checkpoints")
            ),
            layers=tuple(
                _layer_from_json(_mapping(item, "layer"))
                for item in _required_sequence(data, "layers")
            ),
            storage=_storage_from_json(_required_mapping(data, "storage")),
            provenance=_json_object(data.get("provenance", {}), "provenance"),
        )
    except KeyError as error:
        raise ManifestError(f"Manifest is missing required field: {error.args[0]}") from error
    except ValueError as error:
        raise ManifestError(f"Manifest contains an invalid value: {error}") from error


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManifestError(f"Expected '{field_name}' to be an object, got {type(value).__name__}")
    return value


def _required_mapping(data: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
    return _mapping(data[field_name], field_name)


def _required_sequence(data: Mapping[str, Any], field_name: str) -> tuple[Any, ...]:
    value = data[field_name]
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise ManifestError(f"Expected '{field_name}' to be an array, got {type(value).__name__}")
    return tuple(value)


def _json_object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(
            f"Expected '{field_name}' to be a JSON object, got {type(value).__name__}"
        )
    return value


def _required_str(data: Mapping[str, Any], field_name: str) -> str:
    value = data[field_name]
    if not isinstance(value, str) or not value:
        raise ManifestError(f"Expected '{field_name}' to be a non-empty string")
    return value


def _optional_str(data: Mapping[str, Any], field_name: str) -> str | None:
    value = data.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ManifestError(f"Expected '{field_name}' to be a string or null")
    return value


def _optional_int(data: Mapping[str, Any], field_name: str) -> int | None:
    value = data.get(field_name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ManifestError(f"Expected '{field_name}' to be an integer or null")
    return value


def _datetime_from_json(data: Mapping[str, Any], field_name: str) -> datetime:
    return datetime.fromisoformat(_required_str(data, field_name))


def _model_from_json(data: Mapping[str, Any]) -> ModelRef:
    return ModelRef(
        id=ModelId(_required_str(data, "id")),
        name=_required_str(data, "name"),
        architecture_family=_required_str(data, "architecture_family"),
        framework=_required_str(data, "framework"),
        metadata=_json_object(data.get("metadata", {}), "metadata"),
    )


def _dataset_from_json(data: Mapping[str, Any]) -> DatasetRef:
    return DatasetRef(
        id=DatasetId(_required_str(data, "id")),
        name=_required_str(data, "name"),
        source_uri=_required_str(data, "source_uri"),
        kind=_required_str(data, "kind"),
        metadata=_json_object(data.get("metadata", {}), "metadata"),
    )


def _checkpoint_from_json(data: Mapping[str, Any]) -> Checkpoint:
    return Checkpoint(
        id=CheckpointId(_required_str(data, "id")),
        label=_required_str(data, "label"),
        step=_optional_int(data, "step"),
        epoch=_optional_int(data, "epoch"),
        source_uri=_optional_str(data, "source_uri"),
        metadata=_json_object(data.get("metadata", {}), "metadata"),
    )


def _layer_from_json(data: Mapping[str, Any]) -> Layer:
    return Layer(
        id=LayerId(_required_str(data, "id")),
        name=_required_str(data, "name"),
        path=_required_str(data, "path"),
        kind=_required_str(data, "kind"),
        shape=_shape_from_json(data, "shape"),
        role=_optional_str(data, "role"),
        metadata=_json_object(data.get("metadata", {}), "metadata"),
    )


def _storage_from_json(data: Mapping[str, Any]) -> StorageBackendSpec:
    kind = _required_str(data, "kind")
    if kind not in ("numpy-shards", "zarr"):
        raise ManifestError(f"Unknown storage backend: {kind}")
    return StorageBackendSpec(
        kind=cast(StorageBackend, kind),
        root=_required_str(data, "root"),
        options=_json_object(data.get("options", {}), "options"),
    )


def _shape_from_json(data: Mapping[str, Any], field_name: str) -> tuple[int, ...]:
    shape = _required_sequence(data, field_name)
    dimensions: list[int] = []
    for dimension in shape:
        if isinstance(dimension, bool) or not isinstance(dimension, int):
            raise ManifestError("Expected 'shape' dimensions to be integers")
        if dimension < 0:
            raise ManifestError("Expected 'shape' dimensions to be non-negative")
        dimensions.append(dimension)
    return tuple(dimensions)
