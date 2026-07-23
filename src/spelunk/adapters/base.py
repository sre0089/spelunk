"""Framework-neutral adapter description types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from spelunk.domain import Layer, ModelRef


@dataclass(frozen=True, slots=True)
class ModelDescription:
    model: ModelRef
    layers: tuple[Layer, ...]


class ModelAdapter(Protocol):
    framework: str

    def describe_model(self) -> ModelDescription:
        """Describe a model without exposing framework-specific types."""

