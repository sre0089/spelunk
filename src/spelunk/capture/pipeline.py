"""Framework-neutral activation capture pipeline contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from spelunk.domain import CheckpointId, LayerId, RunId, SampleId
from spelunk.domain.types import Shape


@dataclass(frozen=True, slots=True)
class CaptureRequest:
    run_id: RunId
    checkpoint_id: CheckpointId
    layers: tuple[LayerId, ...]
    batch_size: int = 32
    max_samples: int | None = None


@dataclass(frozen=True, slots=True)
class CaptureProgress:
    run_id: RunId
    stage: str
    completed_samples: int
    total_samples: int | None
    current_layer: LayerId | None = None
    message: str = ""


@dataclass(frozen=True, slots=True)
class ActivationBatch:
    run_id: RunId
    checkpoint_id: CheckpointId
    layer_id: LayerId
    sample_ids: tuple[SampleId, ...]
    array: object
    shape: Shape
    dtype: str


@dataclass(frozen=True, slots=True)
class CaptureSummary:
    run_id: RunId
    checkpoint_id: CheckpointId
    captured_layers: tuple[LayerId, ...]
    captured_samples: int
    batch_count: int


class ActivationSink(Protocol):
    def write_batch(self, batch: ActivationBatch) -> None:
        """Persist or collect one activation batch."""


class ProgressSink(Protocol):
    def emit(self, progress: CaptureProgress) -> None:
        """Receive capture progress events."""


class InMemoryActivationSink:
    """Simple capture sink for tests and early service integration."""

    def __init__(self) -> None:
        self.batches: list[ActivationBatch] = []

    def write_batch(self, batch: ActivationBatch) -> None:
        self.batches.append(batch)


class InMemoryProgressSink:
    """Simple progress sink for tests and early TUI wiring."""

    def __init__(self) -> None:
        self.events: list[CaptureProgress] = []

    def emit(self, progress: CaptureProgress) -> None:
        self.events.append(progress)

