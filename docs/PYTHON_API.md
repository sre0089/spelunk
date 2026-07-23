# Python API

The public API is available from `spelunk`.

```python
from spelunk import DatasetRef, ModelRef, Session

session = Session.open("runs/tiny-autoencoder.spelunk")
scan = session.scan()
report = session.report(format="markdown")
```

## Stable Entry Points

- `Session`: open, create, scan, compare, report, and inspect local runs
- `load_capture_config`: parse JSON or TOML capture configs
- `run_capture_config`: execute a local capture config

## Stable Result Types

- `RunSummary`
- `ScanResult`
- `CaptureResult`
- `ReportResult`
- `ComparisonResult`
- `FeatureInspectionResult`

## Stable Domain Types

- `ModelRef`
- `DatasetRef`
- `Checkpoint`
- `LayerSummary`
- `FeatureSummary`
- `Statistic`
- ID wrappers such as `ModelId`, `DatasetId`, `RunId`, `LayerId`, and `FeatureId`

## Errors

User-facing failures inherit from `SpelunkError`.

- `ManifestError`
- `StorageError`
- `UnsupportedOperationError`

Storage backends, Textual widgets, PyTorch adapter internals, and manifest serializer helpers are not part of the top-level public API.
