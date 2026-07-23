"""Comparison domain objects."""

from __future__ import annotations

from dataclasses import dataclass

from spelunk.domain.diagnostics import DiagnosticResult
from spelunk.domain.ids import FeatureId, LayerId, RunId
from spelunk.domain.types import StatisticValue


@dataclass(frozen=True, slots=True)
class LayerMatch:
    left_layer_id: LayerId
    right_layer_id: LayerId
    confidence: float


@dataclass(frozen=True, slots=True)
class FeatureMatch:
    left_feature_id: FeatureId
    right_feature_id: FeatureId
    confidence: float


@dataclass(frozen=True, slots=True)
class StatisticDelta:
    subject_id: str
    metric: str
    left_value: StatisticValue
    right_value: StatisticValue
    delta: float | None


@dataclass(frozen=True, slots=True)
class RunComparison:
    left_run_id: RunId
    right_run_id: RunId
    layer_matches: tuple[LayerMatch, ...] = ()
    feature_matches: tuple[FeatureMatch, ...] = ()
    metric_deltas: tuple[StatisticDelta, ...] = ()
    diagnostics: tuple[DiagnosticResult, ...] = ()

