"""Activation references."""

from __future__ import annotations

from dataclasses import dataclass, field

from spelunk.domain.ids import CheckpointId, LayerId, RunId
from spelunk.domain.types import JsonObject, Shape


@dataclass(frozen=True, slots=True)
class ActivationRef:
    run_id: RunId
    checkpoint_id: CheckpointId
    layer_id: LayerId
    shard_uri: str
    shape: Shape
    dtype: str
    metadata: JsonObject = field(default_factory=dict)

