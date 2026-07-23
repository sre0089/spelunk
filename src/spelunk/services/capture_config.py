"""Capture config execution service."""

from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from spelunk.adapters.pytorch import PyTorchAdapter
from spelunk.capture import CaptureRequest, DatasetLoader, DatasetSample, DatasetSpec
from spelunk.config import CaptureConfig, load_capture_config
from spelunk.domain import Checkpoint, DatasetRef
from spelunk.errors import SpelunkError, UnsupportedOperationError
from spelunk.services.results import CaptureResult
from spelunk.services.session import Session


def run_capture_config(path: str | Path) -> CaptureResult:
    """Execute a local capture configuration file."""
    config = load_capture_config(path)
    if config.model.framework != "pytorch":
        raise UnsupportedOperationError(f"Unsupported capture framework: {config.model.framework}")

    model = _load_model(config)
    try:
        adapter = PyTorchAdapter(model, model_id=str(config.model.id), name=config.model.name)
    except TypeError as error:
        raise SpelunkError(f"Model factory did not return a PyTorch module: {error}") from error
    description = adapter.describe_model()
    dataset_ref = DatasetRef(
        id=config.dataset.id,
        name=config.dataset.name,
        source_uri=str(config.dataset.source),
        kind=config.dataset.kind,
    )
    checkpoint = Checkpoint(
        id=config.capture.checkpoint_id,
        label=config.capture.checkpoint_label,
    )
    session = Session.create(
        config.run,
        model=description.model,
        dataset=dataset_ref,
        checkpoints=(checkpoint,),
        layers=description.layers,
        storage_backend=config.storage_backend,
    )
    loader = DatasetLoader(
        DatasetSpec(
            id=config.dataset.id,
            name=config.dataset.name,
            kind=config.dataset.kind,
            source=config.dataset.source,
        )
    )
    try:
        summary = adapter.run_capture(
            CaptureRequest(
                run_id=session.run_id,
                checkpoint_id=config.capture.checkpoint_id,
                layers=config.capture.layers,
                batch_size=config.capture.batch_size,
                max_samples=config.capture.max_samples,
            ),
            loader.iter_samples(),
            sink=session.activation_sink(),
            input_converter=_tensor_input_converter,
        )
    except (RuntimeError, TypeError, ValueError) as error:
        raise SpelunkError(f"Capture failed: {error}") from error
    if summary.captured_samples == 0:
        raise SpelunkError("Capture dataset produced no samples.")
    return CaptureResult(
        run=session.summary(),
        checkpoint_id=str(summary.checkpoint_id),
        captured_layers=summary.captured_layers,
        captured_samples=summary.captured_samples,
        batch_count=summary.batch_count,
    )


def _load_model(config: CaptureConfig) -> Any:
    factory = _load_factory(config)
    model = factory()
    return model


def _load_factory(config: CaptureConfig) -> Any:
    if config.model.path is not None:
        module = _load_module_from_path(config.model.path)
    elif config.model.module is not None:
        module = importlib.import_module(config.model.module)
    else:
        raise SpelunkError("Capture config model requires either module or path")
    factory = getattr(module, config.model.factory, None)
    if not callable(factory):
        raise SpelunkError(f"Model factory is not callable: {config.model.factory}")
    return factory


def _load_module_from_path(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("spelunk_capture_model", path)
    if spec is None or spec.loader is None:
        raise SpelunkError(f"Could not load model module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tensor_input_converter(samples: Sequence[DatasetSample]) -> Any:
    torch = _torch()
    np = _numpy()
    values = [sample.data for sample in samples]
    array = np.stack(values)
    return torch.as_tensor(array).float()


def _torch() -> Any:
    try:
        import torch
    except ImportError as error:
        raise UnsupportedOperationError("PyTorch capture requires the 'pytorch' extra.") from error
    return torch


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as error:
        raise UnsupportedOperationError("Capture datasets require the 'datasets' extra.") from error
    return cast(Any, np)
