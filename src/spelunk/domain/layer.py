"""Layer and feature domain objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from spelunk.domain.ids import FeatureId, LayerId
from spelunk.domain.types import JsonObject, Shape


@dataclass(frozen=True, slots=True)
class Layer:
    id: LayerId
    name: str
    path: str
    kind: str
    shape: Shape
    role: str | None = None
    metadata: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Feature:
    id: FeatureId
    layer_id: LayerId
    key: str
    kind: str
    label: str | None = None
    metadata: JsonObject = field(default_factory=dict)

