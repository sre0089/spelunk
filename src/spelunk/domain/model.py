"""Model and dataset references."""

from __future__ import annotations

from dataclasses import dataclass, field

from spelunk.domain.ids import DatasetId, ModelId
from spelunk.domain.types import JsonObject


@dataclass(frozen=True, slots=True)
class ModelRef:
    id: ModelId
    name: str
    architecture_family: str
    framework: str
    metadata: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DatasetRef:
    id: DatasetId
    name: str
    source_uri: str
    kind: str
    metadata: JsonObject = field(default_factory=dict)

