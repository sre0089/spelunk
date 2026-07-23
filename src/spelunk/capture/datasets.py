"""Spelunk-owned dataset loading for capture workflows."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from spelunk.domain import DatasetId, SampleId
from spelunk.domain.types import JsonObject
from spelunk.errors import SpelunkError

DatasetKind = Literal["numpy", "csv", "jsonl", "image-folder"]


class DatasetError(SpelunkError):
    """Raised when a dataset cannot be loaded."""


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    id: DatasetId
    name: str
    kind: DatasetKind
    source: Path
    metadata: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DatasetSample:
    id: SampleId
    data: object
    metadata: JsonObject = field(default_factory=dict)


class DatasetLoader:
    """Stream samples from a local dataset specification."""

    def __init__(self, spec: DatasetSpec) -> None:
        self.spec = spec

    def iter_samples(self) -> Iterator[DatasetSample]:
        if self.spec.kind == "numpy":
            yield from _iter_numpy(self.spec.source)
            return
        if self.spec.kind == "csv":
            yield from _iter_csv(self.spec.source)
            return
        if self.spec.kind == "jsonl":
            yield from _iter_jsonl(self.spec.source)
            return
        if self.spec.kind == "image-folder":
            yield from _iter_images(self.spec.source)
            return
        raise DatasetError(f"Unsupported dataset kind: {self.spec.kind}")


def load_dataset(spec: DatasetSpec) -> DatasetLoader:
    return DatasetLoader(spec)


def _iter_numpy(path: Path) -> Iterator[DatasetSample]:
    try:
        import numpy as np
    except ImportError as error:
        raise DatasetError("NumPy dataset loading requires the 'datasets' extra.") from error

    array = np.load(path, allow_pickle=False)
    rows = array if array.ndim > 0 else array.reshape(1)
    for index, row in enumerate(rows):
        yield DatasetSample(
            id=SampleId(str(index)),
            data=row,
            metadata={"source": str(path), "index": index},
        )


def _iter_csv(path: Path) -> Iterator[DatasetSample]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader):
            yield DatasetSample(
                id=SampleId(str(index)),
                data=dict(row),
                metadata={"source": str(path), "index": index},
            )


def _iter_jsonl(path: Path) -> Iterator[DatasetSample]:
    with path.open() as handle:
        for index, line in enumerate(handle):
            if not line.strip():
                continue
            payload: Any = json.loads(line)
            yield DatasetSample(
                id=SampleId(str(index)),
                data=payload,
                metadata={"source": str(path), "index": index},
            )


def _iter_images(path: Path) -> Iterator[DatasetSample]:
    try:
        from PIL import Image
    except ImportError as error:
        raise DatasetError("Image-folder dataset loading requires the 'datasets' extra.") from error

    suffixes = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
    image_paths = sorted(item for item in path.iterdir() if item.suffix.lower() in suffixes)
    for index, image_path in enumerate(image_paths):
        image = Image.open(image_path).convert("RGB")
        yield DatasetSample(
            id=SampleId(str(index)),
            data=image,
            metadata={"source": str(image_path), "index": index},
        )

