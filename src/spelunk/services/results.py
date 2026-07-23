"""Typed service result objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from spelunk.domain import (
    DatasetRef,
    DiagnosticResult,
    LayerSummary,
    ModelRef,
    Report,
    ReportFormat,
    RunComparison,
    RunId,
)
from spelunk.domain.types import JsonObject
from spelunk.storage import StorageBackend


@dataclass(frozen=True, slots=True)
class RunSummary:
    run_id: RunId
    model: ModelRef
    dataset: DatasetRef
    created_at: datetime
    storage_uri: str
    storage_backend: StorageBackend
    checkpoint_count: int
    layer_count: int
    metadata: JsonObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScanResult:
    run: RunSummary
    layers: tuple[LayerSummary, ...] = ()
    diagnostics: tuple[DiagnosticResult, ...] = ()


@dataclass(frozen=True, slots=True)
class CapturePlan:
    layers: tuple[str, ...]
    dataset: str
    batch_size: int = 32
    max_samples: int | None = None


@dataclass(frozen=True, slots=True)
class CaptureResult:
    run: RunSummary


@dataclass(frozen=True, slots=True)
class ReportResult:
    report: Report
    format: ReportFormat
    content: str


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    comparison: RunComparison
