from collections.abc import Sequence
from typing import Any, cast

import pytest

from spelunk.adapters.pytorch import PyTorchAdapter
from spelunk.capture import (
    CaptureRequest,
    DatasetSample,
    InMemoryActivationSink,
    InMemoryProgressSink,
)
from spelunk.domain import CheckpointId, LayerId, RunId, SampleId

torch: Any = pytest.importorskip("torch")
np: Any = pytest.importorskip("numpy")


class TinyAutoencoder(torch.nn.Module):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__()
        self.encoder = torch.nn.Linear(4, 2)
        self.decoder = torch.nn.Linear(2, 4)

    def forward(self, x: Any) -> Any:
        return self.decoder(self.encoder(x))


class TinySparseAutoencoder(torch.nn.Module):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__()
        self.encoder = torch.nn.Linear(4, 2)
        self.decoder = torch.nn.Linear(2, 4)

    def forward(self, x: Any) -> Any:
        return self.decoder(torch.relu(self.encoder(x)))


def test_pytorch_adapter_describes_autoencoder_layers() -> None:
    description = PyTorchAdapter(TinyAutoencoder(), model_id="tiny-ae").describe_model()

    assert description.model.id == "tiny-ae"
    assert description.model.framework == "pytorch"
    assert description.model.architecture_family == "autoencoder"
    assert [layer.path for layer in description.layers] == ["encoder", "decoder"]
    assert description.layers[0].shape == (2, 4)
    assert description.layers[0].role == "encoder"
    assert description.layers[1].role == "decoder"


def test_pytorch_adapter_describes_sparse_autoencoder_family() -> None:
    description = PyTorchAdapter(TinySparseAutoencoder()).describe_model()

    assert description.model.architecture_family == "sparse-autoencoder"


def test_pytorch_adapter_rejects_non_module() -> None:
    with pytest.raises(TypeError, match="torch.nn.Module"):
        PyTorchAdapter(object())


def test_pytorch_adapter_captures_selected_layers() -> None:
    model = TinyAutoencoder()
    with torch.no_grad():
        model.encoder.weight.copy_(torch.tensor([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]]))
        model.encoder.bias.zero_()
        model.decoder.weight.copy_(
            torch.tensor(
                [
                    [1.0, 0.0],
                    [0.0, 1.0],
                    [1.0, 1.0],
                    [0.0, 0.0],
                ]
            )
        )
        model.decoder.bias.zero_()

    samples = (
        DatasetSample(id=SampleId("sample-0"), data=np.array([1.0, 2.0, 3.0, 4.0])),
        DatasetSample(id=SampleId("sample-1"), data=np.array([5.0, 6.0, 7.0, 8.0])),
    )
    sink = InMemoryActivationSink()
    progress = InMemoryProgressSink()
    request = CaptureRequest(
        run_id=RunId("run-001"),
        checkpoint_id=CheckpointId("ckpt-001"),
        layers=(LayerId("encoder"),),
        batch_size=2,
        max_samples=2,
    )

    summary = PyTorchAdapter(model).run_capture(
        request,
        samples,
        sink=sink,
        progress=progress,
        input_converter=_stack_samples,
    )

    assert summary.captured_samples == 2
    assert summary.batch_count == 1
    assert len(sink.batches) == 1
    batch = sink.batches[0]
    assert batch.layer_id == "encoder"
    assert batch.sample_ids == ("sample-0", "sample-1")
    assert batch.shape == (2, 2)
    assert batch.dtype == "float32"
    captured_array = cast(Any, batch.array)
    assert captured_array.tolist() == [[1.0, 2.0], [5.0, 6.0]]
    assert [event.stage for event in progress.events] == ["started", "capturing", "completed"]


def test_pytorch_adapter_captures_multiple_batches() -> None:
    samples = tuple(
        DatasetSample(id=SampleId(f"sample-{index}"), data=np.ones(4, dtype=np.float32) * index)
        for index in range(3)
    )
    sink = InMemoryActivationSink()
    request = CaptureRequest(
        run_id=RunId("run-001"),
        checkpoint_id=CheckpointId("ckpt-001"),
        layers=(LayerId("encoder"), LayerId("decoder")),
        batch_size=1,
    )

    summary = PyTorchAdapter(TinyAutoencoder()).run_capture(
        request,
        samples,
        sink=sink,
        input_converter=_stack_samples,
    )

    assert summary.captured_samples == 3
    assert summary.batch_count == 6
    assert [batch.layer_id for batch in sink.batches[:2]] == ["encoder", "decoder"]


def test_pytorch_adapter_capture_rejects_unknown_layer() -> None:
    request = CaptureRequest(
        run_id=RunId("run-001"),
        checkpoint_id=CheckpointId("ckpt-001"),
        layers=(LayerId("missing"),),
    )

    with pytest.raises(ValueError, match="Unknown PyTorch layer"):
        PyTorchAdapter(TinyAutoencoder()).run_capture(
            request,
            (),
            sink=InMemoryActivationSink(),
            input_converter=_stack_samples,
        )


def test_pytorch_adapter_capture_rejects_invalid_batch_size() -> None:
    request = CaptureRequest(
        run_id=RunId("run-001"),
        checkpoint_id=CheckpointId("ckpt-001"),
        layers=(LayerId("encoder"),),
        batch_size=0,
    )

    with pytest.raises(ValueError, match="batch_size"):
        PyTorchAdapter(TinyAutoencoder()).run_capture(
            request,
            (),
            sink=InMemoryActivationSink(),
            input_converter=_stack_samples,
        )


def _stack_samples(samples: Sequence[DatasetSample]) -> Any:
    return torch.tensor(np.stack([sample.data for sample in samples]), dtype=torch.float32)
