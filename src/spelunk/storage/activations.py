"""Activation array storage backends."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from spelunk.capture import ActivationBatch
from spelunk.domain import CheckpointId, LayerId, RunId, SampleId
from spelunk.errors import StorageError


@dataclass(frozen=True, slots=True)
class ActivationQuery:
    run_id: RunId | None = None
    checkpoint_id: CheckpointId | None = None
    layer_id: LayerId | None = None


class ActivationStore(Protocol):
    def write_batch(self, batch: ActivationBatch) -> None:
        """Persist one activation batch."""

    def iter_batches(self, query: ActivationQuery | None = None) -> Iterator[ActivationBatch]:
        """Stream activation batches matching a query."""


class NumpyShardActivationStore:
    """Store activation batches as inspectable `.npz` shard files."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def write_batch(self, batch: ActivationBatch) -> None:
        np = _numpy()
        directory = self.root / str(batch.run_id) / str(batch.checkpoint_id) / str(batch.layer_id)
        directory.mkdir(parents=True, exist_ok=True)
        shard_index = _next_shard_index(directory, "*.npz")
        path = directory / f"shard-{shard_index:06d}.npz"
        np.savez_compressed(
            path,
            array=np.asarray(batch.array),
            sample_ids=np.array([str(sample_id) for sample_id in batch.sample_ids]),
            metadata=np.array(
                json.dumps(
                    {
                        "run_id": str(batch.run_id),
                        "checkpoint_id": str(batch.checkpoint_id),
                        "layer_id": str(batch.layer_id),
                        "shape": batch.shape,
                        "dtype": batch.dtype,
                    }
                )
            ),
        )

    def iter_batches(self, query: ActivationQuery | None = None) -> Iterator[ActivationBatch]:
        query = query or ActivationQuery()
        for path in sorted(self.root.glob("*/*/*/shard-*.npz")):
            batch = _read_npz_batch(path)
            if _matches(batch, query):
                yield batch


class ZarrActivationStore:
    """Store activation batches in a local Zarr hierarchy."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._zarr = _zarr()

    def write_batch(self, batch: ActivationBatch) -> None:
        np = _numpy()
        directory = self.root / str(batch.run_id) / str(batch.checkpoint_id) / str(batch.layer_id)
        directory.mkdir(parents=True, exist_ok=True)
        shard_index = _next_shard_index(directory, "batch-*.zarr")
        group_path = directory / f"batch-{shard_index:06d}.zarr"
        group = self._zarr.open_group(str(group_path), mode="w")
        group.create_array("array", data=np.asarray(batch.array))
        group.attrs.update(
            {
                "run_id": str(batch.run_id),
                "checkpoint_id": str(batch.checkpoint_id),
                "layer_id": str(batch.layer_id),
                "sample_ids": [str(sample_id) for sample_id in batch.sample_ids],
                "shape": batch.shape,
                "dtype": batch.dtype,
            }
        )

    def iter_batches(self, query: ActivationQuery | None = None) -> Iterator[ActivationBatch]:
        query = query or ActivationQuery()
        for path in sorted(self.root.glob("*/*/*/batch-*.zarr")):
            batch = _read_zarr_batch(path)
            if _matches(batch, query):
                yield batch


def _read_npz_batch(path: Path) -> ActivationBatch:
    np = _numpy()
    try:
        with np.load(path, allow_pickle=False) as payload:
            metadata = json.loads(str(payload["metadata"].item()))
            sample_ids = tuple(SampleId(str(item)) for item in payload["sample_ids"].tolist())
            array = payload["array"].copy()
    except Exception as error:
        raise StorageError(f"Could not read activation shard: {path}") from error

    return ActivationBatch(
        run_id=RunId(metadata["run_id"]),
        checkpoint_id=CheckpointId(metadata["checkpoint_id"]),
        layer_id=LayerId(metadata["layer_id"]),
        sample_ids=sample_ids,
        array=array,
        shape=tuple(int(part) for part in metadata["shape"]),
        dtype=str(metadata["dtype"]),
    )


def _read_zarr_batch(path: Path) -> ActivationBatch:
    np = _numpy()
    zarr = _zarr()
    try:
        group = zarr.open_group(str(path), mode="r")
        attrs = group.attrs
        array = np.asarray(group["array"])
        sample_ids = tuple(SampleId(str(item)) for item in attrs["sample_ids"])
    except Exception as error:
        raise StorageError(f"Could not read activation group: {path}") from error

    return ActivationBatch(
        run_id=RunId(str(attrs["run_id"])),
        checkpoint_id=CheckpointId(str(attrs["checkpoint_id"])),
        layer_id=LayerId(str(attrs["layer_id"])),
        sample_ids=sample_ids,
        array=array,
        shape=tuple(int(part) for part in attrs["shape"]),
        dtype=str(attrs["dtype"]),
    )


def _matches(batch: ActivationBatch, query: ActivationQuery) -> bool:
    if query.run_id is not None and batch.run_id != query.run_id:
        return False
    if query.checkpoint_id is not None and batch.checkpoint_id != query.checkpoint_id:
        return False
    if query.layer_id is not None and batch.layer_id != query.layer_id:
        return False
    return True


def _next_shard_index(directory: Path, pattern: str) -> int:
    return len(tuple(directory.glob(pattern)))


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as error:
        raise StorageError("Activation storage requires NumPy.") from error
    return np


def _zarr() -> Any:
    try:
        import zarr
    except ImportError as error:
        raise StorageError("Zarr activation storage requires the 'arrays' extra.") from error
    return cast(Any, zarr)
