"""Activation health diagnostic."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from spelunk.capture import ActivationBatch
from spelunk.diagnostics.interfaces import DiagnosticContext
from spelunk.domain import (
    DiagnosticId,
    DiagnosticResult,
    EvidenceItem,
    LayerId,
    Provenance,
    Severity,
    Statistic,
)


@dataclass(slots=True)
class _Accumulator:
    sample_count: int = 0
    element_count: int = 0
    zero_count: int = 0
    saturated_count: int = 0
    outlier_count: int = 0
    maximum_abs: float = 0.0
    total: float = 0.0
    total_squares: float = 0.0

    def update(self, array: Any, *, zero_epsilon: float, saturation_abs: float) -> None:
        np = _numpy()
        values = np.asarray(array, dtype=float)
        if values.size == 0:
            return
        self.sample_count += int(values.shape[0]) if values.ndim > 0 else 1
        self.element_count += int(values.size)
        absolute = np.abs(values)
        self.zero_count += int((absolute <= zero_epsilon).sum())
        self.saturated_count += int((absolute >= saturation_abs).sum())
        self.maximum_abs = max(self.maximum_abs, float(absolute.max()))
        self.total += float(values.sum())
        self.total_squares += float((values * values).sum())

    def finalize(self, *, outlier_z: float) -> None:
        # Outlier detection is a second pass in the diagnostic class.
        _ = outlier_z

    @property
    def mean(self) -> float:
        return self.total / self.element_count if self.element_count else 0.0

    @property
    def std(self) -> float:
        if not self.element_count:
            return 0.0
        variance = (self.total_squares / self.element_count) - (self.mean * self.mean)
        return float(max(variance, 0.0) ** 0.5)

    @property
    def zero_fraction(self) -> float:
        return self.zero_count / self.element_count if self.element_count else 0.0

    @property
    def saturation_fraction(self) -> float:
        return self.saturated_count / self.element_count if self.element_count else 0.0

    @property
    def outlier_fraction(self) -> float:
        return float(self.outlier_count / self.element_count) if self.element_count else 0.0


class ActivationHealthDiagnostic:
    id = "activation-health"
    name = "Activation health"

    def __init__(
        self,
        *,
        zero_epsilon: float = 1e-8,
        inactive_fraction: float = 0.95,
        sparsity_warning_fraction: float = 0.80,
        saturation_abs: float = 10.0,
        saturation_fraction: float = 0.05,
        outlier_z: float = 6.0,
        outlier_fraction: float = 0.01,
    ) -> None:
        self.zero_epsilon = zero_epsilon
        self.inactive_fraction = inactive_fraction
        self.sparsity_warning_fraction = sparsity_warning_fraction
        self.saturation_abs = saturation_abs
        self.saturation_fraction = saturation_fraction
        self.outlier_z = outlier_z
        self.outlier_fraction = outlier_fraction

    def run(self, context: DiagnosticContext) -> tuple[DiagnosticResult, ...]:
        accumulators: dict[LayerId, _Accumulator] = defaultdict(_Accumulator)
        batches = tuple(context.store.iter_batches(context.query))
        for batch in batches:
            accumulators[batch.layer_id].update(
                batch.array,
                zero_epsilon=self.zero_epsilon,
                saturation_abs=self.saturation_abs,
            )

        self._count_outliers(accumulators, batches)

        return tuple(
            self._result(layer_id, accumulator)
            for layer_id, accumulator in sorted(accumulators.items(), key=lambda item: item[0])
        )

    def _count_outliers(
        self,
        accumulators: dict[LayerId, _Accumulator],
        batches: tuple[ActivationBatch, ...],
    ) -> None:
        np = _numpy()
        for batch in batches:
            accumulator = accumulators[batch.layer_id]
            if accumulator.std == 0.0:
                continue
            values = np.asarray(batch.array, dtype=float)
            z_scores = np.abs((values - accumulator.mean) / accumulator.std)
            accumulator.outlier_count += int((z_scores >= self.outlier_z).sum())

    def _result(self, layer_id: LayerId, accumulator: _Accumulator) -> DiagnosticResult:
        flags = self._flags(accumulator)
        severity: Severity = "info"
        if flags:
            severity = "warning"
        if "inactive" in flags or "saturated" in flags:
            severity = "critical"

        conclusion = (
            f"Layer {layer_id} activation health looks normal."
            if not flags
            else f"Layer {layer_id} shows activation health issues: {', '.join(flags)}."
        )
        explanation = (
            "Spelunk checked inactivity, sparsity, saturation, and large outliers over stored "
            "activation batches."
        )
        provenance = Provenance(source=self.id)
        statistics = self._statistics(layer_id, accumulator, provenance)
        return DiagnosticResult(
            id=DiagnosticId(f"{self.id}:{layer_id}"),
            name=self.name,
            subject_id=layer_id,
            subject_type="layer",
            severity=severity,
            conclusion=conclusion,
            explanation=explanation,
            evidence=(
                EvidenceItem(label="zero_fraction", value=f"{accumulator.zero_fraction:.6f}"),
                EvidenceItem(
                    label="saturation_fraction",
                    value=f"{accumulator.saturation_fraction:.6f}",
                ),
                EvidenceItem(label="outlier_fraction", value=f"{accumulator.outlier_fraction:.6f}"),
                EvidenceItem(label="maximum_abs", value=f"{accumulator.maximum_abs:.6f}"),
            ),
            statistics=statistics,
            provenance=provenance,
        )

    def _flags(self, accumulator: _Accumulator) -> tuple[str, ...]:
        flags: list[str] = []
        if accumulator.zero_fraction >= self.inactive_fraction:
            flags.append("inactive")
        elif accumulator.zero_fraction >= self.sparsity_warning_fraction:
            flags.append("sparse")
        if accumulator.saturation_fraction >= self.saturation_fraction:
            flags.append("saturated")
        if accumulator.outlier_fraction >= self.outlier_fraction:
            flags.append("outliers")
        return tuple(flags)

    def _statistics(
        self,
        layer_id: LayerId,
        accumulator: _Accumulator,
        provenance: Provenance,
    ) -> tuple[Statistic, ...]:
        return (
            Statistic(
                subject_id=layer_id,
                subject_type="layer",
                metric="zero_fraction",
                value=accumulator.zero_fraction,
                sample_count=accumulator.sample_count,
                provenance=provenance,
            ),
            Statistic(
                subject_id=layer_id,
                subject_type="layer",
                metric="saturation_fraction",
                value=accumulator.saturation_fraction,
                sample_count=accumulator.sample_count,
                provenance=provenance,
            ),
            Statistic(
                subject_id=layer_id,
                subject_type="layer",
                metric="outlier_fraction",
                value=accumulator.outlier_fraction,
                sample_count=accumulator.sample_count,
                provenance=provenance,
            ),
            Statistic(
                subject_id=layer_id,
                subject_type="layer",
                metric="maximum_abs",
                value=accumulator.maximum_abs,
                sample_count=accumulator.sample_count,
                provenance=provenance,
            ),
        )


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as error:
        raise RuntimeError("Activation health diagnostics require NumPy.") from error
    return np
