"""Streaming statistics over stored activation batches."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from spelunk.domain import (
    FeatureId,
    FeatureSummary,
    LayerId,
    LayerSummary,
    Provenance,
    SampleId,
    Statistic,
)
from spelunk.errors import StorageError
from spelunk.storage import ActivationQuery, ActivationStore


@dataclass(slots=True)
class _LayerAccumulator:
    sample_count: int = 0
    element_count: int = 0
    feature_count: int | None = None
    total: float = 0.0
    total_squares: float = 0.0
    minimum: float | None = None
    maximum: float | None = None

    def update(self, array: Any) -> None:
        np = _numpy()
        values = np.asarray(array, dtype=float)
        if values.size == 0:
            return
        self.sample_count += int(values.shape[0]) if values.ndim > 0 else 1
        self.element_count += int(values.size)
        self.total += float(values.sum())
        self.total_squares += float((values * values).sum())
        batch_minimum = float(values.min())
        batch_maximum = float(values.max())
        self.minimum = batch_minimum if self.minimum is None else min(self.minimum, batch_minimum)
        self.maximum = batch_maximum if self.maximum is None else max(self.maximum, batch_maximum)
        if self.feature_count is None:
            self.feature_count = _feature_count(values.shape)

    def summary(self, layer_id: LayerId) -> LayerSummary:
        provenance = Provenance(source="activation-store")
        mean = self.total / self.element_count if self.element_count else 0.0
        variance = (
            (self.total_squares / self.element_count) - (mean * mean)
            if self.element_count
            else 0.0
        )
        std = max(variance, 0.0) ** 0.5
        return LayerSummary(
            layer_id=layer_id,
            activation_count=self.sample_count,
            feature_count=self.feature_count,
            statistics=(
                Statistic(
                    subject_id=layer_id,
                    subject_type="layer",
                    metric="activation_mean",
                    value=mean,
                    sample_count=self.sample_count,
                    provenance=provenance,
                ),
                Statistic(
                    subject_id=layer_id,
                    subject_type="layer",
                    metric="activation_std",
                    value=std,
                    sample_count=self.sample_count,
                    provenance=provenance,
                ),
                Statistic(
                    subject_id=layer_id,
                    subject_type="layer",
                    metric="activation_min",
                    value=self.minimum if self.minimum is not None else 0.0,
                    sample_count=self.sample_count,
                    provenance=provenance,
                ),
                Statistic(
                    subject_id=layer_id,
                    subject_type="layer",
                    metric="activation_max",
                    value=self.maximum if self.maximum is not None else 0.0,
                    sample_count=self.sample_count,
                    provenance=provenance,
                ),
            ),
        )


def summarize_layers(
    store: ActivationStore,
    query: ActivationQuery | None = None,
) -> tuple[LayerSummary, ...]:
    accumulators: dict[LayerId, _LayerAccumulator] = defaultdict(_LayerAccumulator)
    for batch in store.iter_batches(query):
        accumulators[batch.layer_id].update(batch.array)
    return tuple(
        accumulator.summary(layer_id)
        for layer_id, accumulator in sorted(accumulators.items(), key=lambda item: item[0])
    )


def summarize_feature(
    store: ActivationStore,
    *,
    layer_id: LayerId,
    feature_id: FeatureId,
) -> FeatureSummary:
    feature_index = _feature_index(feature_id)
    np = _numpy()
    values: list[float] = []
    ranked_samples: list[tuple[float, str]] = []
    for batch in store.iter_batches(ActivationQuery(layer_id=layer_id)):
        array = np.asarray(batch.array, dtype=float)
        if array.size == 0:
            continue
        feature_matrix = array.reshape((array.shape[0] if array.ndim > 0 else 1, -1))
        if feature_index >= feature_matrix.shape[1]:
            raise StorageError(
                f"Feature index {feature_index} is out of range for layer '{layer_id}'"
            )
        column = feature_matrix[:, feature_index]
        values.extend(float(value) for value in column.tolist())
        ranked_samples.extend(
            (abs(float(value)), str(sample_id))
            for value, sample_id in zip(column.tolist(), batch.sample_ids, strict=False)
        )

    if not values:
        raise StorageError(f"No activations found for layer '{layer_id}'")

    vector = np.asarray(values, dtype=float)
    provenance = Provenance(source="activation-store")
    return FeatureSummary(
        feature_id=feature_id,
        layer_id=layer_id,
        statistics=(
            Statistic(
                subject_id=str(feature_id),
                subject_type="feature",
                metric="activation_mean",
                value=float(vector.mean()),
                sample_count=int(vector.size),
                provenance=provenance,
            ),
            Statistic(
                subject_id=str(feature_id),
                subject_type="feature",
                metric="activation_std",
                value=float(vector.std()),
                sample_count=int(vector.size),
                provenance=provenance,
            ),
            Statistic(
                subject_id=str(feature_id),
                subject_type="feature",
                metric="activation_min",
                value=float(vector.min()),
                sample_count=int(vector.size),
                provenance=provenance,
            ),
            Statistic(
                subject_id=str(feature_id),
                subject_type="feature",
                metric="activation_max",
                value=float(vector.max()),
                sample_count=int(vector.size),
                provenance=provenance,
            ),
        ),
        top_examples=tuple(
            SampleId(sample_id)
            for _score, sample_id in sorted(ranked_samples, reverse=True)[:5]
        ),
    )


def _feature_index(feature_id: FeatureId) -> int:
    try:
        index = int(str(feature_id))
    except ValueError as error:
        raise StorageError(f"Feature ID must be an integer index: {feature_id}") from error
    if index < 0:
        raise StorageError(f"Feature ID must be non-negative: {feature_id}")
    return index


def _feature_count(shape: tuple[int, ...]) -> int | None:
    if len(shape) < 2:
        return None
    count = 1
    for dimension in shape[1:]:
        count *= int(dimension)
    return count


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as error:
        raise RuntimeError("Statistics require NumPy.") from error
    return np
