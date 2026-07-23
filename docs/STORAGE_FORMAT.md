# Storage Format

Spelunk storage is local-first, versioned, and streamable.

## Run Directory

```text
run-001.spelunk/
  manifest.json
  model.json
  dataset.json
  checkpoints.json
  layers.json
  features.json
  statistics.json
  diagnostics.json
  reports/
    report.md
    report.json
  activations/
    layer-id/
      shard-000001.npz
      shard-000002.npz
    zarr/
```

## Format Strategy

Spelunk supports both:

- NumPy shard files for simple, inspectable local persistence.
- Zarr chunked array storage for large activation datasets.

Both formats sit behind the same storage interface. Services should not care which physical format backs a run.

## Manifest Requirements

Every manifest includes:

- `schema_version`
- `spelunk_version`
- created timestamp
- model reference
- dataset reference
- checkpoint references
- layer metadata
- storage backend information
- provenance

## Storage Interface

```python
class ActivationStore(Protocol):
    def write_batch(self, batch: ActivationBatch) -> ActivationRef: ...
    def iter_batches(self, query: ActivationQuery) -> Iterator[ActivationBatch]: ...
    def read_summary(self, subject: SubjectRef) -> Summary | None: ...
    def write_summary(self, summary: Summary) -> None: ...
```

## Compatibility

Readers must reject unknown incompatible schema versions with `SchemaVersionError`. Compatible additions should be ignored by older readers where possible.

## Memory Rules

- Never require an entire run's activations in memory.
- Store activations by layer, checkpoint, and sample range.
- Prefer sequential reads for scan and diagnostic workflows.
- Cache summaries separately from raw arrays.
