"""Pure domain objects for learned representation exploration."""

from spelunk.domain.activation import ActivationRef
from spelunk.domain.comparison import FeatureMatch, LayerMatch, RunComparison, StatisticDelta
from spelunk.domain.diagnostics import DiagnosticResult, EvidenceItem, Severity
from spelunk.domain.ids import (
    CheckpointId,
    DatasetId,
    DiagnosticId,
    FeatureId,
    LayerId,
    ModelId,
    ReportId,
    RunId,
    SampleId,
)
from spelunk.domain.layer import Feature, Layer
from spelunk.domain.model import DatasetRef, ModelRef
from spelunk.domain.report import Report, ReportFormat, ReportSection
from spelunk.domain.run import Checkpoint, Run
from spelunk.domain.statistics import FeatureSummary, LayerSummary, Statistic
from spelunk.domain.types import (
    JsonObject,
    JsonScalar,
    JsonValue,
    Provenance,
    Shape,
    StatisticValue,
)

__all__ = [
    "ActivationRef",
    "Checkpoint",
    "CheckpointId",
    "DatasetId",
    "DatasetRef",
    "DiagnosticId",
    "DiagnosticResult",
    "EvidenceItem",
    "Feature",
    "FeatureId",
    "FeatureMatch",
    "FeatureSummary",
    "JsonObject",
    "JsonScalar",
    "JsonValue",
    "Layer",
    "LayerId",
    "LayerMatch",
    "LayerSummary",
    "ModelId",
    "ModelRef",
    "Provenance",
    "Report",
    "ReportFormat",
    "ReportId",
    "ReportSection",
    "Run",
    "RunComparison",
    "RunId",
    "SampleId",
    "Severity",
    "Shape",
    "Statistic",
    "StatisticDelta",
    "StatisticValue",
]
