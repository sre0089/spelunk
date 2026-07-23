from typing import Any

import pytest

from spelunk.analysis import summarize_layers
from spelunk.capture import ActivationBatch, InMemoryActivationSink
from spelunk.domain import CheckpointId, LayerId, RunId, SampleId
from spelunk.storage import ActivationQuery

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


def test_summarize_layers_streams_activation_batches() -> None:
    store = InMemoryActivationSink()
    store.write_batch(_batch("encoder", [[1.0, 2.0], [3.0, 4.0]]))
    store.write_batch(_batch("encoder", [[5.0, 6.0]]))
    store.write_batch(_batch("decoder", [[10.0, 20.0]]))

    summaries = summarize_layers(store)

    assert [summary.layer_id for summary in summaries] == ["decoder", "encoder"]
    encoder = summaries[1]
    stats = {stat.metric: stat.value for stat in encoder.statistics}
    assert encoder.activation_count == 3
    assert encoder.feature_count == 2
    assert stats["activation_mean"] == 3.5
    assert stats["activation_min"] == 1.0
    assert stats["activation_max"] == 6.0


def test_summarize_layers_respects_query() -> None:
    store = InMemoryActivationSink()
    store.write_batch(_batch("encoder", [[1.0, 2.0]]))
    store.write_batch(_batch("decoder", [[10.0, 20.0]]))

    summaries = summarize_layers(store, ActivationQuery(layer_id=LayerId("decoder")))

    assert len(summaries) == 1
    assert summaries[0].layer_id == "decoder"
