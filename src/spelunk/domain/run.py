"""Run and checkpoint domain objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from spelunk.domain.ids import CheckpointId, RunId
from spelunk.domain.model import DatasetRef, ModelRef
from spelunk.domain.types import JsonObject


@dataclass(frozen=True, slots=True)
class Checkpoint:
    id: CheckpointId
    label: str
    step: int | None = None
    epoch: int | None = None
    source_uri: str | None = None
    metadata: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Run:
    id: RunId
    model: ModelRef
    dataset: DatasetRef
    storage_uri: str
    checkpoints: tuple[Checkpoint, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: JsonObject = field(default_factory=dict)
