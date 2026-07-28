"""Helpers for lower-friction local workflows."""

from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from spelunk.capture import DatasetKind
from spelunk.config import CaptureConfig, CaptureSettings, DatasetConfig, ModelConfig
from spelunk.domain import CheckpointId, DatasetId, LayerId, ModelId
from spelunk.errors import SpelunkError, UnsupportedOperationError
from spelunk.storage import StorageBackend


def load_model_factory(*, module: str | None, path: Path | None, factory: str) -> Any:
    """Load a model factory from a Python module path or importable module."""
    if path is not None:
        source = _load_module_from_path(path)
    elif module is not None:
        source = importlib.import_module(module)
    else:
        raise SpelunkError("Model loading requires either --model-path or --model-module")
    loaded = getattr(source, factory, None)
    if not callable(loaded):
        raise SpelunkError(f"Model factory is not callable: {factory}")
    return loaded


def load_model(
    *,
    module: str | None,
    path: Path | None,
    factory: str,
    checkpoint_path: Path | None = None,
) -> Any:
    model = load_model_factory(module=module, path=path, factory=factory)()
    if checkpoint_path is not None:
        apply_model_checkpoint(model, checkpoint_path)
    return model


def apply_model_checkpoint(model: Any, checkpoint_path: Path) -> None:
    """Load a PyTorch state dict into a factory-created model."""
    if not checkpoint_path.exists():
        raise SpelunkError(f"Model checkpoint file does not exist: {checkpoint_path}")
    try:
        checkpoint = _torch().load(checkpoint_path, map_location="cpu")
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise SpelunkError(f"Could not load model checkpoint: {checkpoint_path}") from error
    state_dict = _checkpoint_state_dict(checkpoint)
    load_state_dict = getattr(model, "load_state_dict", None)
    if not callable(load_state_dict):
        raise SpelunkError("Model checkpoint loading requires a PyTorch module.")
    try:
        load_state_dict(state_dict)
    except (RuntimeError, TypeError, ValueError) as error:
        raise SpelunkError(f"Could not apply model checkpoint: {checkpoint_path}") from error


def build_capture_config(
    *,
    run: Path,
    model_path: Path | None,
    model_module: str | None,
    factory: str,
    checkpoint_path: Path | None,
    dataset: Path,
    layers: tuple[str, ...],
    storage_backend: str,
    model_id: str,
    model_name: str,
    dataset_id: str,
    dataset_name: str,
    dataset_kind: str | None,
    checkpoint_id: str,
    checkpoint_label: str,
    batch_size: int,
    max_samples: int | None,
) -> CaptureConfig:
    if not layers:
        raise SpelunkError("At least one --layers value is required.")
    kind = dataset_kind or infer_dataset_kind(dataset)
    return CaptureConfig(
        run=run,
        storage_backend=_storage_backend(storage_backend),
        model=ModelConfig(
            id=ModelId(model_id),
            name=model_name,
            framework="pytorch",
            path=model_path,
            module=model_module,
            checkpoint_path=checkpoint_path,
            factory=factory,
        ),
        dataset=DatasetConfig(
            id=DatasetId(dataset_id),
            name=dataset_name,
            kind=_dataset_kind(kind),
            source=dataset,
        ),
        capture=CaptureSettings(
            layers=tuple(LayerId(layer) for layer in layers),
            checkpoint_id=CheckpointId(checkpoint_id),
            checkpoint_label=checkpoint_label,
            batch_size=batch_size,
            max_samples=max_samples,
        ),
    )


def infer_dataset_kind(path: Path) -> str:
    if path.is_dir():
        return "image-folder"
    suffix = path.suffix.lower()
    if suffix == ".npy":
        return "numpy"
    if suffix == ".csv":
        return "csv"
    if suffix == ".jsonl":
        return "jsonl"
    raise SpelunkError(
        "Could not infer dataset kind. Pass --dataset-kind with one of: "
        "numpy, csv, jsonl, image-folder."
    )


def _load_module_from_path(path: Path) -> Any:
    if not path.exists():
        raise SpelunkError(f"Model factory file does not exist: {path}")
    spec = importlib.util.spec_from_file_location("spelunk_workflow_model", path)
    if spec is None or spec.loader is None:
        raise SpelunkError(f"Could not load model module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _checkpoint_state_dict(checkpoint: Any) -> Mapping[str, Any]:
    if not isinstance(checkpoint, Mapping):
        raise SpelunkError("Checkpoint must be a PyTorch state_dict or contain 'state_dict'.")
    state_dict = checkpoint.get("state_dict")
    if isinstance(state_dict, Mapping):
        return state_dict
    model_state_dict = checkpoint.get("model_state_dict")
    if isinstance(model_state_dict, Mapping):
        return model_state_dict
    return checkpoint


def _torch() -> Any:
    try:
        import torch
    except ImportError as error:
        raise UnsupportedOperationError(
            "PyTorch checkpoint loading requires the 'pytorch' extra."
        ) from error
    return torch


def _dataset_kind(value: str) -> DatasetKind:
    if value not in ("numpy", "csv", "jsonl", "image-folder"):
        raise SpelunkError(f"Unsupported dataset kind: {value}")
    return cast(DatasetKind, value)


def _storage_backend(value: str) -> StorageBackend:
    if value not in ("numpy-shards", "zarr"):
        raise SpelunkError(f"Unsupported storage backend: {value}")
    return cast(StorageBackend, value)
