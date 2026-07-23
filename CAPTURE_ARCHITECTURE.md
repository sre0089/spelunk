# Capture Architecture

Activation capture is framework-neutral at the service boundary and framework-specific inside adapters.

## Responsibilities

Spelunk owns:

- dataset loading
- sample identity
- capture plans
- layer selection
- capture progress
- activation batch streaming
- persistence into local storage

Framework adapters own:

- model introspection
- layer resolution
- framework-specific hooks
- device movement required for capture
- converting framework tensors into neutral array batches

## Capture Plan

```python
CapturePlan:
    run_id: RunId
    model_name: str
    dataset: DatasetSpec
    layers: list[LayerSelector]
    checkpoints: list[CheckpointSpec]
    max_samples: int | None
    batch_size: int
    storage: StorageSpec
```

Initial datasets should support local NumPy arrays, CSV files, JSONL records, and image folders. Loader details belong behind `DatasetSpec` and dataset services.

## Adapter Protocol

```python
class FrameworkAdapter(Protocol):
    framework: str

    def describe_model(self) -> ModelDescription: ...
    def resolve_layers(self, selectors: list[LayerSelector]) -> list[LayerHandle]: ...
    def run_capture(
        self,
        request: CaptureRequest,
        sink: ActivationSink,
    ) -> CaptureSummary: ...
```

## Activation Batch

```python
ActivationBatch:
    run_id: RunId
    checkpoint_id: CheckpointId
    layer_id: LayerId
    sample_ids: list[SampleId]
    array: ArrayLike
    shape: Shape
    dtype: str
```

`ActivationBatch` must not expose `torch.Tensor` outside the PyTorch adapter or capture boundary. Batches should be detached and converted before storage/analysis receives them.

## Initial PyTorch Scope

The first adapter supports:

- autoencoders
- sparse autoencoders
- generic `torch.nn.Module` models
- named module discovery
- forward-hook activation capture

The domain layer must not import PyTorch types.

## Progress

Capture emits typed progress:

```python
CaptureProgress:
    run_id: RunId
    stage: str
    completed_samples: int
    total_samples: int | None
    current_layer: LayerId | None
    message: str
```

The TUI displays progress live. CLI can render progress or JSON events.
