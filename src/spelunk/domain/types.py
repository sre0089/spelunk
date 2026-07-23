"""Shared primitive types for domain objects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = Mapping[str, JsonValue]
StatisticValue: TypeAlias = float | int | str | bool
Shape: TypeAlias = tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Provenance:
    """Information about where a derived object came from."""

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: str | None = None
    metadata: JsonObject = field(default_factory=dict)
