from pathlib import Path
from typing import Any, cast

import pytest

from spelunk.capture import ActivationBatch
from spelunk.domain import CheckpointId, LayerId, RunId, SampleId
from spelunk.storage import (
    ActivationQuery,
    NumpyShardActivationStore,
    ZarrActivationStore,
)

np: Any = pytest.importorskip("numpy")
pytest.importorskip("zarr")


def _batch(layer_id: str = "encoder", values: object | None = None) -> ActivationBatch:
    array = np.asarray(values if values is not None else [[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    return ActivationBatch(
        run_id=RunId("run-001"),
        checkpoint_id=CheckpointId("ckpt-001"),
        layer_id=LayerId(layer_id),
        sample_ids=(SampleId("sample-0"), SampleId("sample-1")),
        array=array,
        shape=tuple(int(part) for part in array.shape),
        dtype=str(array.dtype),
    )


@pytest.mark.parametrize("store_type", [NumpyShardActivationStore, ZarrActivationStore])
def test_activation_store_round_trips_batches(store_type: type, tmp_path: Path) -> None:
    store = store_type(tmp_path / "activations")
    store.write_batch(_batch())

    batches = list(store.iter_batches())

    assert len(batches) == 1
    restored = batches[0]
    assert restored.run_id == "run-001"
    assert restored.checkpoint_id == "ckpt-001"
    assert restored.layer_id == "encoder"
    assert restored.sample_ids == ("sample-0", "sample-1")
    assert restored.shape == (2, 2)
    assert restored.dtype == "float32"
    assert cast(Any, restored.array).tolist() == [[1.0, 2.0], [3.0, 4.0]]


@pytest.mark.parametrize("store_type", [NumpyShardActivationStore, ZarrActivationStore])
def test_activation_store_filters_by_query(store_type: type, tmp_path: Path) -> None:
    store = store_type(tmp_path / "activations")
    store.write_batch(_batch("encoder"))
    store.write_batch(_batch("decoder"))

    batches = list(store.iter_batches(ActivationQuery(layer_id=LayerId("decoder"))))

    assert len(batches) == 1
    assert batches[0].layer_id == "decoder"


def test_pytorch_capture_streams_to_numpy_store(tmp_path: Path) -> None:
    torch = pytest.importorskip("torch")

    from spelunk.adapters.pytorch import PyTorchAdapter
    from spelunk.analysis import summarize_layers
    from spelunk.capture import CaptureRequest, DatasetSample

    model = torch.nn.Linear(2, 1)
    with torch.no_grad():
        model.weight.copy_(torch.tensor([[1.0, 2.0]]))
        model.bias.zero_()

    samples = (
        DatasetSample(id=SampleId("sample-0"), data=np.array([1.0, 2.0])),
        DatasetSample(id=SampleId("sample-1"), data=np.array([3.0, 4.0])),
    )
    store = NumpyShardActivationStore(tmp_path / "activations")

    PyTorchAdapter(torch.nn.Sequential(model)).run_capture(
        CaptureRequest(
            run_id=RunId("run-001"),
            checkpoint_id=CheckpointId("ckpt-001"),
            layers=(LayerId("0"),),
            batch_size=2,
        ),
        samples,
        sink=store,
        input_converter=lambda batch: torch.tensor(
            np.stack([sample.data for sample in batch]),
            dtype=torch.float32,
        ),
    )

    summaries = summarize_layers(store)

    assert len(summaries) == 1
    assert summaries[0].layer_id == "0"
    assert summaries[0].activation_count == 2
    assert summaries[0].feature_count == 1
