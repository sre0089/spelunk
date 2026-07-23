"""Statistics and summaries."""

from __future__ import annotations

from dataclasses import dataclass

from spelunk.domain.ids import FeatureId, LayerId, SampleId
from spelunk.domain.types import Provenance, StatisticValue


@dataclass(frozen=True, slots=True)
class Statistic:
    subject_id: str
    subject_type: str
    metric: str
    value: StatisticValue
    sample_count: int
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class LayerSummary:
    layer_id: LayerId
    activation_count: int
    feature_count: int | None
    statistics: tuple[Statistic, ...] = ()


@dataclass(frozen=True, slots=True)
class FeatureSummary:
    feature_id: FeatureId
    layer_id: LayerId
    statistics: tuple[Statistic, ...] = ()
    top_examples: tuple[SampleId, ...] = ()

