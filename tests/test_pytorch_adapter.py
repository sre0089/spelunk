from typing import Any

import pytest

from spelunk.adapters.pytorch import PyTorchAdapter

torch: Any = pytest.importorskip("torch")


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
