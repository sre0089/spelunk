"""PyTorch model description adapter."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from spelunk.adapters.base import ModelDescription
from spelunk.domain import Layer, LayerId, ModelId, ModelRef


class PyTorchAdapter:
    """Describe PyTorch modules through framework-neutral domain objects."""

    framework = "pytorch"

    def __init__(self, model: Any, *, model_id: str = "model", name: str | None = None) -> None:
        torch = _torch()
        if not isinstance(model, torch.nn.Module):
            raise TypeError("PyTorchAdapter requires a torch.nn.Module")
        self._model = model
        self._model_id = model_id
        self._name = name or model.__class__.__name__

    def describe_model(self) -> ModelDescription:
        return ModelDescription(
            model=ModelRef(
                id=ModelId(self._model_id),
                name=self._name,
                architecture_family=_architecture_family(self._model),
                framework=self.framework,
                metadata={"module_class": self._model.__class__.__name__},
            ),
            layers=tuple(self._describe_layers()),
        )

    def _describe_layers(self) -> Iterable[Layer]:
        for path, module in self._model.named_modules():
            if path == "":
                continue
            yield Layer(
                id=LayerId(path),
                name=path.rsplit(".", maxsplit=1)[-1],
                path=path,
                kind=module.__class__.__name__,
                shape=_module_shape(module),
                role=_layer_role(path, module),
                metadata={"module_class": module.__class__.__name__},
            )


def _torch() -> Any:
    try:
        import torch
    except ImportError as error:
        raise RuntimeError("PyTorch support requires the 'pytorch' extra.") from error
    return torch


def _architecture_family(model: Any) -> str:
    class_name = model.__class__.__name__.lower()
    module_names = {name.lower() for name, _ in model.named_modules()}
    combined = " ".join([class_name, *module_names])
    if "sparse" in combined and "autoencoder" in combined:
        return "sparse-autoencoder"
    if "sae" in combined:
        return "sparse-autoencoder"
    if "autoencoder" in combined or {"encoder", "decoder"}.issubset(module_names):
        return "autoencoder"
    return "generic-pytorch"


def _module_shape(module: Any) -> tuple[int, ...]:
    if hasattr(module, "weight") and module.weight is not None:
        return tuple(int(part) for part in module.weight.shape)
    if hasattr(module, "normalized_shape"):
        return tuple(int(part) for part in module.normalized_shape)
    return ()


def _layer_role(path: str, module: Any) -> str | None:
    lowered = path.lower()
    if "encoder" in lowered:
        return "encoder"
    if "decoder" in lowered:
        return "decoder"
    class_name = module.__class__.__name__.lower()
    if "attention" in class_name or "attn" in lowered:
        return "attention"
    if "conv" in class_name:
        return "convolution"
    if "linear" in class_name:
        return "projection"
    return None

