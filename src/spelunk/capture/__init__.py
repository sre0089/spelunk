"""Framework-neutral activation capture interfaces and orchestration."""

from spelunk.capture.datasets import (
    DatasetError,
    DatasetKind,
    DatasetLoader,
    DatasetSample,
    DatasetSpec,
)
from spelunk.capture.pipeline import (
    ActivationBatch,
    ActivationSink,
    CaptureProgress,
    CaptureRequest,
    CaptureSummary,
    InMemoryActivationSink,
    InMemoryProgressSink,
    ProgressSink,
)

__all__ = [
    "ActivationBatch",
    "ActivationSink",
    "CaptureProgress",
    "CaptureRequest",
    "CaptureSummary",
    "DatasetError",
    "DatasetKind",
    "DatasetLoader",
    "DatasetSample",
    "DatasetSpec",
    "InMemoryActivationSink",
    "InMemoryProgressSink",
    "ProgressSink",
]
