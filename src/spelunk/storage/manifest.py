"""Versioned local run manifest schemas."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, Literal

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
from spelunk.errors import SchemaVersionError

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
    data = json.loads(path.read_text())
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

    return RunManifest(
        schema_version=CURRENT_SCHEMA_VERSION,
        spelunk_version=str(data["spelunk_version"]),
        created_at=datetime.fromisoformat(str(data["created_at"])),
        model=_model_from_json(_mapping(data["model"])),
        dataset=_dataset_from_json(_mapping(data["dataset"])),
        checkpoints=tuple(_checkpoint_from_json(_mapping(item)) for item in data["checkpoints"]),
        layers=tuple(_layer_from_json(_mapping(item)) for item in data["layers"]),
        storage=_storage_from_json(_mapping(data["storage"])),
        provenance=_json_object(data.get("provenance", {})),
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"Expected object, got {type(value).__name__}")
    return value


def _json_object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object, got {type(value).__name__}")
    return value


def _model_from_json(data: Mapping[str, Any]) -> ModelRef:
    return ModelRef(
        id=ModelId(str(data["id"])),
        name=str(data["name"]),
        architecture_family=str(data["architecture_family"]),
        framework=str(data["framework"]),
        metadata=_json_object(data.get("metadata", {})),
    )


def _dataset_from_json(data: Mapping[str, Any]) -> DatasetRef:
    return DatasetRef(
        id=DatasetId(str(data["id"])),
        name=str(data["name"]),
        source_uri=str(data["source_uri"]),
        kind=str(data["kind"]),
        metadata=_json_object(data.get("metadata", {})),
    )


def _checkpoint_from_json(data: Mapping[str, Any]) -> Checkpoint:
    return Checkpoint(
        id=CheckpointId(str(data["id"])),
        label=str(data["label"]),
        step=data.get("step"),
        epoch=data.get("epoch"),
        source_uri=data.get("source_uri"),
        metadata=_json_object(data.get("metadata", {})),
    )


def _layer_from_json(data: Mapping[str, Any]) -> Layer:
    return Layer(
        id=LayerId(str(data["id"])),
        name=str(data["name"]),
        path=str(data["path"]),
        kind=str(data["kind"]),
        shape=tuple(int(part) for part in data["shape"]),
        role=data.get("role"),
        metadata=_json_object(data.get("metadata", {})),
    )


def _storage_from_json(data: Mapping[str, Any]) -> StorageBackendSpec:
    return StorageBackendSpec(
        kind=data["kind"],
        root=str(data["root"]),
        options=_json_object(data.get("options", {})),
    )
