from typing import Any

import pytest

from spelunk.capture import ActivationBatch, InMemoryActivationSink
from spelunk.diagnostics import ActivationHealthDiagnostic, DiagnosticContext
from spelunk.domain import CheckpointId, LayerId, RunId, SampleId

np: Any = pytest.importorskip("numpy")


def _batch(layer_id: str, values: object) -> ActivationBatch:
    array = np.asarray(values, dtype=np.float32)
    return ActivationBatch(
        run_id=RunId("run-001"),
        checkpoint_id=CheckpointId("ckpt-001"),
        layer_id=LayerId(layer_id),
        sample_ids=tuple(SampleId(f"sample-{index}") for index in range(array.shape[0])),
        array=array,
        shape=tuple(int(part) for part in array.shape),
        dtype=str(array.dtype),
    )


def test_activation_health_reports_normal_layer() -> None:
    store = InMemoryActivationSink()
    store.write_batch(_batch("encoder", [[1.0, 2.0], [3.0, 4.0]]))

    results = ActivationHealthDiagnostic().run(DiagnosticContext(store=store))

    assert len(results) == 1
    assert results[0].severity == "info"
    assert "looks normal" in results[0].conclusion
    assert {stat.metric for stat in results[0].statistics} == {
        "zero_fraction",
        "saturation_fraction",
        "outlier_fraction",
        "maximum_abs",
    }


def test_activation_health_detects_inactive_layer() -> None:
    store = InMemoryActivationSink()
    store.write_batch(_batch("encoder", [[0.0, 0.0], [0.0, 0.0]]))

    results = ActivationHealthDiagnostic().run(DiagnosticContext(store=store))

    assert results[0].severity == "critical"
    assert "inactive" in results[0].conclusion


def test_activation_health_detects_sparsity_saturation_and_outliers() -> None:
    store = InMemoryActivationSink()
    store.write_batch(_batch("sparse", [[0.0, 0.0, 1.0, 2.0]]))
    store.write_batch(_batch("saturated", [[20.0, 30.0, 0.0, 0.0]]))
    store.write_batch(_batch("outlier", [[1.0, 1.0, 1.0, 8.0]]))
    diagnostic = ActivationHealthDiagnostic(
        sparsity_warning_fraction=0.50,
        saturation_abs=10.0,
        saturation_fraction=0.25,
        outlier_z=1.5,
        outlier_fraction=0.20,
    )

    results = {
        result.subject_id: result
        for result in diagnostic.run(DiagnosticContext(store=store))
    }

    assert results["sparse"].severity == "warning"
    assert "sparse" in results["sparse"].conclusion
    assert results["saturated"].severity == "critical"
    assert "saturated" in results["saturated"].conclusion
    assert results["outlier"].severity == "warning"
    assert "outliers" in results["outlier"].conclusion
