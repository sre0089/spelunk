"""Notebook-friendly public API helpers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, cast

from spelunk.adapters.pytorch import PyTorchAdapter
from spelunk.capture import CaptureRequest, DatasetLoader, DatasetSample, DatasetSpec
from spelunk.domain import Checkpoint, CheckpointId, DatasetId, DatasetRef, LayerId, SampleId
from spelunk.errors import SpelunkError
from spelunk.services import CaptureResult, Session
from spelunk.services.workflow import infer_dataset_kind
from spelunk.storage import StorageBackend


def capture(
    *,
    model: Any,
    dataset: str | Path | Iterable[object],
    layers: Sequence[str],
    run: str | Path,
    batch_size: int = 32,
    max_samples: int | None = None,
    checkpoint_id: str = "ckpt-001",
    checkpoint_label: str = "initial",
    dataset_id: str = "dataset",
    dataset_name: str | None = None,
    dataset_kind: str | None = None,
    storage_backend: StorageBackend = "numpy-shards",
) -> CaptureResult:
    """Capture PyTorch activations from Python without writing a config file."""
    if not layers:
        raise SpelunkError("At least one layer is required.")
    adapter = PyTorchAdapter(model)
    description = adapter.describe_model()
    dataset_ref, samples = _dataset_ref_and_samples(
        dataset,
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        dataset_kind=dataset_kind,
    )
    checkpoint = Checkpoint(id=CheckpointId(checkpoint_id), label=checkpoint_label)
    session = Session.create(
        run,
        model=description.model,
        dataset=dataset_ref,
        checkpoints=(checkpoint,),
        layers=description.layers,
        storage_backend=storage_backend,
    )
    try:
        summary = adapter.run_capture(
            CaptureRequest(
                run_id=session.run_id,
                checkpoint_id=CheckpointId(checkpoint_id),
                layers=tuple(LayerId(layer) for layer in layers),
                batch_size=batch_size,
                max_samples=max_samples,
            ),
            samples,
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


def _dataset_ref_and_samples(
    dataset: str | Path | Iterable[object],
    *,
    dataset_id: str,
    dataset_name: str | None,
    dataset_kind: str | None,
) -> tuple[DatasetRef, Iterable[DatasetSample]]:
    if isinstance(dataset, str | Path):
        path = Path(dataset)
        kind = cast(Any, dataset_kind or infer_dataset_kind(path))
        return (
            DatasetRef(
                id=DatasetId(dataset_id),
                name=dataset_name or path.stem,
                source_uri=str(path),
                kind=kind,
            ),
            DatasetLoader(
                DatasetSpec(
                    id=DatasetId(dataset_id),
                    name=dataset_name or path.stem,
                    kind=kind,
                    source=path,
                )
            ).iter_samples(),
        )
    return (
        DatasetRef(
            id=DatasetId(dataset_id),
            name=dataset_name or dataset_id,
            source_uri="memory://dataset",
            kind=cast(Any, "numpy"),
        ),
        _iter_memory_samples(dataset),
    )


def _iter_memory_samples(dataset: Iterable[object]) -> Iterable[DatasetSample]:
    for index, row in enumerate(dataset):
        yield DatasetSample(
            id=SampleId(str(index)),
            data=row,
            metadata={"source": "memory", "index": index},
        )


def _tensor_input_converter(samples: Sequence[DatasetSample]) -> Any:
    try:
        import numpy as np
        import torch
    except ImportError as error:
        raise SpelunkError("Python capture requires NumPy and PyTorch.") from error
    numpy = cast(Any, np)
    torch_module = cast(Any, torch)
    values = [sample.data for sample in samples]
    array: Any = numpy.stack(values)
    return torch_module.as_tensor(array).float()


__all__ = ["capture"]
