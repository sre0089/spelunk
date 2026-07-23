# Domain Model

The domain model is pure Python data. It must not depend on Textual, Typer, Rich, PyTorch, or storage implementations.

## Identity

Use typed IDs rather than unstructured strings at service boundaries:

- `ModelId`
- `RunId`
- `CheckpointId`
- `LayerId`
- `FeatureId`
- `SampleId`
- `DiagnosticId`
- `ReportId`

IDs should be stable, serializable, and readable enough for CLI output.

## Core Objects

```python
ModelRef:
    id: ModelId
    name: str
    architecture_family: str
    framework: str
    metadata: Mapping[str, JsonValue]

Run:
    id: RunId
    model: ModelRef
    dataset: DatasetRef
    checkpoints: list[Checkpoint]
    storage_uri: str
    created_at: datetime

Checkpoint:
    id: CheckpointId
    label: str
    step: int | None
    epoch: int | None
    source_uri: str | None

Layer:
    id: LayerId
    name: str
    path: str
    kind: str
    shape: Shape
    role: str | None

Feature:
    id: FeatureId
    layer_id: LayerId
    key: str
    kind: str
    label: str | None
    summary: FeatureSummary | None
```

## Analysis Objects

```python
ActivationRef:
    run_id: RunId
    checkpoint_id: CheckpointId
    layer_id: LayerId
    shard_uri: str
    shape: Shape
    dtype: str

Statistic:
    subject_id: str
    subject_type: str
    metric: str
    value: float | int | str | bool
    sample_count: int
    provenance: Provenance

LayerSummary:
    layer_id: LayerId
    activation_count: int
    feature_count: int | None
    statistics: list[Statistic]

FeatureSummary:
    feature_id: FeatureId
    layer_id: LayerId
    statistics: list[Statistic]
    top_examples: list[SampleId]
```

## Diagnostic Objects

```python
DiagnosticResult:
    id: DiagnosticId
    name: str
    subject_id: str
    subject_type: str
    severity: Literal["info", "warning", "critical"]
    conclusion: str
    explanation: str
    evidence: list[EvidenceItem]
    statistics: list[Statistic]
    provenance: Provenance
```

Diagnostics must answer a question. Raw metrics alone are not diagnostics.

## Comparison And Reports

```python
RunComparison:
    left_run_id: RunId
    right_run_id: RunId
    layer_matches: list[LayerMatch]
    feature_matches: list[FeatureMatch]
    metric_deltas: list[StatisticDelta]
    diagnostics: list[DiagnosticResult]

Report:
    id: ReportId
    run_id: RunId
    title: str
    sections: list[ReportSection]
    formats: set[Literal["markdown", "json"]]
```
