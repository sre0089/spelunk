"""Report domain objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from spelunk.domain.ids import ReportId, RunId
from spelunk.domain.types import JsonObject

ReportFormat = Literal["markdown", "json"]


@dataclass(frozen=True, slots=True)
class ReportSection:
    title: str
    body: str
    metadata: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Report:
    id: ReportId
    run_id: RunId
    title: str
    sections: tuple[ReportSection, ...]
    formats: frozenset[ReportFormat]
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: JsonObject = field(default_factory=dict)
