"""Diagnostic result objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from spelunk.domain.ids import DiagnosticId
from spelunk.domain.statistics import Statistic
from spelunk.domain.types import JsonObject, Provenance

Severity = Literal["info", "warning", "critical"]


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    label: str
    value: str
    metadata: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DiagnosticResult:
    id: DiagnosticId
    name: str
    subject_id: str
    subject_type: str
    severity: Severity
    conclusion: str
    explanation: str
    evidence: tuple[EvidenceItem, ...]
    statistics: tuple[Statistic, ...]
    provenance: Provenance

