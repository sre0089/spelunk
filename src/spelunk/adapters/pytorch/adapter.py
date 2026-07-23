"""PyTorch model description adapter."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from spelunk.adapters.base import ModelDescription
from spelunk.capture import (
    ActivationBatch,
    ActivationSink,
    CaptureProgress,
    CaptureRequest,
    CaptureSummary,
    DatasetSample,
    ProgressSink,
)
from spelunk.domain import Layer, LayerId, ModelId, ModelRef

InputConverter = Callable[[Sequence[DatasetSample]], Any]


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

    def run_capture(
        self,
        request: CaptureRequest,
        samples: Iterable[DatasetSample],
        *,
        sink: ActivationSink,
        input_converter: InputConverter,
        progress: ProgressSink | None = None,
    ) -> CaptureSummary:
        torch = _torch()
        modules = dict(self._model.named_modules())
        missing = tuple(layer for layer in request.layers if str(layer) not in modules)
        if missing:
            missing_layers = ", ".join(str(layer) for layer in missing)
            raise ValueError(f"Unknown PyTorch layer selector(s): {missing_layers}")

        selected = {str(layer): modules[str(layer)] for layer in request.layers}
        captured: dict[str, Any] = {}
        handles = [
            module.register_forward_hook(_capture_hook(path, captured))
            for path, module in selected.items()
        ]
        completed_samples = 0
        batch_count = 0
        _emit(
            progress,
            CaptureProgress(
                run_id=request.run_id,
                stage="started",
                completed_samples=0,
                total_samples=request.max_samples,
                message="Capture started.",
            ),
        )
        try:
            self._model.eval()
            with torch.no_grad():
                for batch_samples in _sample_batches(
                    samples,
                    batch_size=request.batch_size,
                    max_samples=request.max_samples,
                ):
                    if not batch_samples:
                        continue
                    captured.clear()
                    model_input = input_converter(batch_samples)
                    self._model(model_input)
                    sample_ids = tuple(sample.id for sample in batch_samples)
                    completed_samples += len(batch_samples)
                    for layer_id in request.layers:
                        layer_key = str(layer_id)
                        if layer_key not in captured:
                            raise RuntimeError(f"No activation captured for layer: {layer_key}")
                        array = _to_numpy(captured[layer_key])
                        sink.write_batch(
                            ActivationBatch(
                                run_id=request.run_id,
                                checkpoint_id=request.checkpoint_id,
                                layer_id=layer_id,
                                sample_ids=sample_ids,
                                array=array,
                                shape=tuple(int(part) for part in array.shape),
                                dtype=str(array.dtype),
                            )
                        )
                        batch_count += 1
                        _emit(
                            progress,
                            CaptureProgress(
                                run_id=request.run_id,
                                stage="capturing",
                                completed_samples=completed_samples,
                                total_samples=request.max_samples,
                                current_layer=layer_id,
                                message=f"Captured {layer_key}.",
                            ),
                        )
        finally:
            for handle in handles:
                handle.remove()

        _emit(
            progress,
            CaptureProgress(
                run_id=request.run_id,
                stage="completed",
                completed_samples=completed_samples,
                total_samples=request.max_samples,
                message="Capture completed.",
            ),
        )
        return CaptureSummary(
            run_id=request.run_id,
            checkpoint_id=request.checkpoint_id,
            captured_layers=request.layers,
            captured_samples=completed_samples,
            batch_count=batch_count,
        )


def _torch() -> Any:
    try:
        import torch
    except ImportError as error:
        raise RuntimeError("PyTorch support requires the 'pytorch' extra.") from error
    return torch


def _capture_hook(
    path: str,
    captured: dict[str, Any],
) -> Callable[[Any, tuple[Any, ...], Any], None]:
    def hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> None:
        captured[path] = output

    return hook


def _sample_batches(
    samples: Iterable[DatasetSample],
    *,
    batch_size: int,
    max_samples: int | None,
) -> Iterable[tuple[DatasetSample, ...]]:
    if batch_size <= 0:
        raise ValueError("Capture batch_size must be positive")
    batch: list[DatasetSample] = []
    emitted = 0
    for sample in samples:
        if max_samples is not None and emitted >= max_samples:
            break
        batch.append(sample)
        emitted += 1
        if len(batch) == batch_size:
            yield tuple(batch)
            batch.clear()
    if batch:
        yield tuple(batch)


def _to_numpy(value: Any) -> Any:
    torch = _torch()
    if isinstance(value, (tuple, list)):
        value = value[0]
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"Expected hook output to be a torch.Tensor, got {type(value).__name__}")
    return value.detach().cpu().numpy()


def _emit(progress: ProgressSink | None, event: CaptureProgress) -> None:
    if progress is not None:
        progress.emit(event)


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
