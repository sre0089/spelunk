"""Capture configuration parsing."""

from __future__ import annotations

import json
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from spelunk.capture import DatasetKind
from spelunk.domain import CheckpointId, DatasetId, LayerId, ModelId
from spelunk.errors import ManifestError
from spelunk.storage import StorageBackend


@dataclass(frozen=True, slots=True)
class ModelConfig:
    id: ModelId
    name: str
    framework: str
    factory: str
    module: str | None = None
    path: Path | None = None


@dataclass(frozen=True, slots=True)
class DatasetConfig:
    id: DatasetId
    name: str
    kind: DatasetKind
    source: Path


@dataclass(frozen=True, slots=True)
class CaptureSettings:
    layers: tuple[LayerId, ...]
    checkpoint_id: CheckpointId
    checkpoint_label: str
    batch_size: int = 32
    max_samples: int | None = None


@dataclass(frozen=True, slots=True)
class CaptureConfig:
    run: Path
    model: ModelConfig
    dataset: DatasetConfig
    capture: CaptureSettings
    storage_backend: StorageBackend = "numpy-shards"


def load_capture_config(path: str | Path) -> CaptureConfig:
    config_path = Path(path)
    data = _read_config(config_path)
    base = config_path.parent
    return CaptureConfig(
        run=_resolve_path(_required_str(data, "run"), base),
        model=_model_config(_required_mapping(data, "model"), base),
        dataset=_dataset_config(_required_mapping(data, "dataset"), base),
        capture=_capture_settings(_required_mapping(data, "capture")),
        storage_backend=_storage_backend(data.get("storage_backend", "numpy-shards")),
    )


def _read_config(path: Path) -> Mapping[str, Any]:
    if path.suffix == ".json":
        try:
            return _mapping(json.loads(path.read_text()), "capture config")
        except json.JSONDecodeError as error:
            raise ManifestError(f"Capture config is not valid JSON: {path}") from error
    if path.suffix == ".toml":
        try:
            return _mapping(tomllib.loads(path.read_text()), "capture config")
        except tomllib.TOMLDecodeError as error:
            raise ManifestError(f"Capture config is not valid TOML: {path}") from error
    raise ManifestError(f"Unsupported capture config format: {path.suffix or '<none>'}")


def _model_config(data: Mapping[str, Any], base: Path) -> ModelConfig:
    module = data.get("module")
    model_path = data.get("path")
    if module is None and model_path is None:
        raise ManifestError("Capture config model requires either 'module' or 'path'")
    if module is not None and not isinstance(module, str):
        raise ManifestError("Expected 'model.module' to be a string")
    if model_path is not None and not isinstance(model_path, str):
        raise ManifestError("Expected 'model.path' to be a string")
    return ModelConfig(
        id=ModelId(_required_str(data, "id")),
        name=_required_str(data, "name"),
        framework=_required_str(data, "framework"),
        module=module,
        path=_resolve_path(model_path, base) if model_path is not None else None,
        factory=_required_str(data, "factory"),
    )


def _dataset_config(data: Mapping[str, Any], base: Path) -> DatasetConfig:
    kind = _dataset_kind(_required_str(data, "kind"))
    return DatasetConfig(
        id=DatasetId(_required_str(data, "id")),
        name=_required_str(data, "name"),
        kind=kind,
        source=_resolve_path(_required_str(data, "source"), base),
    )


def _capture_settings(data: Mapping[str, Any]) -> CaptureSettings:
    layers = _string_sequence(data, "layers")
    return CaptureSettings(
        layers=tuple(LayerId(layer) for layer in layers),
        checkpoint_id=CheckpointId(_required_str(data, "checkpoint_id")),
        checkpoint_label=_required_str(data, "checkpoint_label"),
        batch_size=_positive_int(data.get("batch_size", 32), "batch_size"),
        max_samples=_optional_positive_int(data.get("max_samples"), "max_samples"),
    )


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManifestError(f"Expected '{field_name}' to be an object")
    return value


def _required_mapping(data: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
    return _mapping(data[field_name], field_name)


def _required_str(data: Mapping[str, Any], field_name: str) -> str:
    value = data[field_name]
    if not isinstance(value, str) or not value:
        raise ManifestError(f"Expected '{field_name}' to be a non-empty string")
    return value


def _string_sequence(data: Mapping[str, Any], field_name: str) -> tuple[str, ...]:
    value = data[field_name]
    if isinstance(value, str) or not isinstance(value, list | tuple):
        raise ManifestError(f"Expected '{field_name}' to be an array of strings")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ManifestError(f"Expected '{field_name}' to contain non-empty strings")
        result.append(item)
    return tuple(result)


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ManifestError(f"Expected '{field_name}' to be a positive integer")
    return value


def _optional_positive_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    return _positive_int(value, field_name)


def _resolve_path(value: str, base: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return base / path


def _dataset_kind(value: str) -> DatasetKind:
    if value not in ("numpy", "csv", "jsonl", "image-folder"):
        raise ManifestError(f"Unsupported dataset kind: {value}")
    return cast(DatasetKind, value)


def _storage_backend(value: Any) -> StorageBackend:
    if value not in ("numpy-shards", "zarr"):
        raise ManifestError(f"Unsupported storage backend: {value}")
    return cast(StorageBackend, value)
