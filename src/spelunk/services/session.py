"""Session service for local Spelunk runs."""

from __future__ import annotations

import json
from pathlib import Path

from spelunk.analysis import summarize_layers
from spelunk.diagnostics import ActivationHealthDiagnostic, DiagnosticContext
from spelunk.domain import (
    Checkpoint,
    DatasetRef,
    Layer,
    LayerMatch,
    LayerSummary,
    ModelRef,
    Report,
    ReportFormat,
    ReportId,
    ReportSection,
    RunComparison,
    RunId,
    Statistic,
    StatisticDelta,
)
from spelunk.errors import StorageError, UnsupportedOperationError
from spelunk.services.results import (
    CapturePlan,
    CaptureResult,
    ComparisonResult,
    ReportResult,
    RunSummary,
    ScanResult,
)
from spelunk.storage import (
    ActivationStore,
    NumpyShardActivationStore,
    RunManifest,
    StorageBackend,
    StorageBackendSpec,
    ZarrActivationStore,
    read_manifest,
    write_manifest,
)

MANIFEST_FILENAME = "manifest.json"


class Session:
    """Application-service entrypoint for one local Spelunk run."""

    def __init__(self, root: Path, manifest: RunManifest) -> None:
        self._root = root
        self._manifest = manifest

    @property
    def root(self) -> Path:
        return self._root

    @property
    def manifest(self) -> RunManifest:
        return self._manifest

    @classmethod
    def open(cls, location: str | Path) -> Session:
        root = Path(location)
        manifest_path = _manifest_path(root)
        if not manifest_path.exists():
            raise StorageError(f"No Spelunk manifest found at {manifest_path}")
        return cls(root=manifest_path.parent, manifest=read_manifest(manifest_path))

    @classmethod
    def create(
        cls,
        location: str | Path,
        *,
        model: ModelRef,
        dataset: DatasetRef,
        checkpoints: tuple[Checkpoint, ...] = (),
        layers: tuple[Layer, ...] = (),
        storage_backend: StorageBackend = "numpy-shards",
    ) -> Session:
        root = Path(location)
        root.mkdir(parents=True, exist_ok=True)
        (root / "activations").mkdir(exist_ok=True)
        (root / "reports").mkdir(exist_ok=True)

        manifest = RunManifest.create(
            model=model,
            dataset=dataset,
            checkpoints=checkpoints,
            layers=layers,
            storage=StorageBackendSpec(kind=storage_backend, root="activations"),
        )
        write_manifest(root / MANIFEST_FILENAME, manifest)
        return cls(root=root, manifest=manifest)

    @property
    def run_id(self) -> RunId:
        name = self._root.name
        if name.endswith(".spelunk"):
            name = name[: -len(".spelunk")]
        return RunId(name)

    def summary(self) -> RunSummary:
        return RunSummary(
            run_id=self.run_id,
            model=self._manifest.model,
            dataset=self._manifest.dataset,
            created_at=self._manifest.created_at,
            storage_uri=str(self._root),
            storage_backend=self._manifest.storage.kind,
            checkpoint_count=len(self._manifest.checkpoints),
            layer_count=len(self._manifest.layers),
        )

    def _activation_store(self) -> ActivationStore:
        root = _store_root(self._root, self._manifest)
        if self._manifest.storage.kind == "numpy-shards":
            return NumpyShardActivationStore(root)
        if self._manifest.storage.kind == "zarr":
            return ZarrActivationStore(root)
        raise StorageError(f"Unsupported activation storage backend: {self._manifest.storage.kind}")

    def activation_sink(self) -> ActivationStore:
        """Return the configured activation sink for capture execution."""
        return self._activation_store()

    def scan(self) -> ScanResult:
        store = self._activation_store()
        layers = summarize_layers(store)
        diagnostics = ActivationHealthDiagnostic().run(DiagnosticContext(store=store))
        return ScanResult(run=self.summary(), layers=layers, diagnostics=diagnostics)

    def capture(self, plan: CapturePlan) -> CaptureResult:
        raise UnsupportedOperationError(
            f"Capture is not implemented yet for dataset '{plan.dataset}'. "
            "See M7 in docs/ROADMAP.md."
        )

    def compare(self, other: Session) -> ComparisonResult:
        left = self.scan()
        right = other.scan()
        left_layers = {summary.layer_id: summary for summary in left.layers}
        right_layers = {summary.layer_id: summary for summary in right.layers}
        shared_layer_ids = sorted(left_layers.keys() & right_layers.keys())
        layer_matches = tuple(
            LayerMatch(left_layer_id=layer_id, right_layer_id=layer_id, confidence=1.0)
            for layer_id in shared_layer_ids
        )
        metric_deltas = tuple(
            delta
            for layer_id in shared_layer_ids
            for delta in _layer_metric_deltas(left_layers[layer_id], right_layers[layer_id])
        )
        diagnostics = tuple(
            diagnostic
            for diagnostic in (*left.diagnostics, *right.diagnostics)
            if diagnostic.severity in ("warning", "critical")
        )
        return ComparisonResult(
            comparison=RunComparison(
                left_run_id=left.run.run_id,
                right_run_id=right.run.run_id,
                layer_matches=layer_matches,
                metric_deltas=metric_deltas,
                diagnostics=diagnostics,
            )
        )

    def report(self, *, format: ReportFormat = "markdown") -> ReportResult:
        scan = self.scan()
        if format == "markdown":
            content = self._report_markdown(scan)
            path = self._root / "reports" / "report.md"
        elif format == "json":
            content = self._report_json(scan)
            path = self._root / "reports" / "report.json"
        else:
            raise UnsupportedOperationError(f"Unsupported report format: {format}")

        path.write_text(content)
        report = Report(
            id=ReportId(f"{self.run_id}-summary"),
            run_id=self.run_id,
            title=f"Spelunk summary for {self.run_id}",
            sections=(ReportSection(title="Run Summary", body=content),),
            formats=frozenset({format}),
        )
        return ReportResult(report=report, format=format, content=content, path=path)

    def _report_markdown(self, scan: ScanResult) -> str:
        summary = scan.run
        lines = [
            f"# Spelunk report for {summary.run_id}",
            "",
            "## Run",
            "",
            f"- Model: {summary.model.name}",
            f"- Architecture: {summary.model.architecture_family}",
            f"- Framework: {summary.model.framework}",
            f"- Dataset: {summary.dataset.name}",
            f"- Storage: {summary.storage_backend}",
            f"- Checkpoints: {summary.checkpoint_count}",
            f"- Manifest layers: {summary.layer_count}",
            f"- Activation layers: {len(scan.layers)}",
            f"- Diagnostics: {len(scan.diagnostics)}",
            "",
            "## Layers",
            "",
        ]
        if not scan.layers:
            lines.extend(["No stored activation layers.", ""])
        for layer in scan.layers:
            lines.extend(
                [
                    f"### {layer.layer_id}",
                    "",
                    f"- Activations: {layer.activation_count}",
                    f"- Features: {layer.feature_count}",
                ]
            )
            for statistic in layer.statistics:
                lines.append(
                    f"- {statistic.metric}: {statistic.value:.6g} "
                    f"({statistic.sample_count} samples)"
                )
            lines.append("")

        lines.extend(["## Diagnostics", ""])
        if not scan.diagnostics:
            lines.extend(["No diagnostics available.", ""])
        for diagnostic in scan.diagnostics:
            lines.extend(
                [
                    f"### {diagnostic.name}",
                    "",
                    f"- Severity: {diagnostic.severity.upper()}",
                    f"- Subject: {diagnostic.subject_type} `{diagnostic.subject_id}`",
                    f"- Conclusion: {diagnostic.conclusion}",
                    f"- Explanation: {diagnostic.explanation}",
                ]
            )
            if diagnostic.evidence:
                lines.append("- Evidence:")
                for item in diagnostic.evidence:
                    lines.append(f"  - {item.label}: {item.value}")
            lines.append("")
        return "\n".join(lines)

    def _report_json(self, scan: ScanResult) -> str:
        summary = scan.run
        return json.dumps(
            {
                "run_id": summary.run_id,
                "model": {
                    "id": summary.model.id,
                    "name": summary.model.name,
                    "architecture_family": summary.model.architecture_family,
                    "framework": summary.model.framework,
                },
                "dataset": {
                    "id": summary.dataset.id,
                    "name": summary.dataset.name,
                    "kind": summary.dataset.kind,
                    "source_uri": summary.dataset.source_uri,
                },
                "checkpoint_count": summary.checkpoint_count,
                "layer_count": summary.layer_count,
                "activation_layer_count": len(scan.layers),
                "layers": [
                    {
                        "id": layer.layer_id,
                        "activation_count": layer.activation_count,
                        "feature_count": layer.feature_count,
                        "statistics": [
                            {
                                "metric": statistic.metric,
                                "value": statistic.value,
                                "sample_count": statistic.sample_count,
                            }
                            for statistic in layer.statistics
                        ],
                    }
                    for layer in scan.layers
                ],
                "diagnostics": [
                    {
                        "id": diagnostic.id,
                        "name": diagnostic.name,
                        "subject_id": diagnostic.subject_id,
                        "subject_type": diagnostic.subject_type,
                        "severity": diagnostic.severity,
                        "conclusion": diagnostic.conclusion,
                        "explanation": diagnostic.explanation,
                        "evidence": [
                            {"label": item.label, "value": item.value}
                            for item in diagnostic.evidence
                        ],
                    }
                    for diagnostic in scan.diagnostics
                ],
            },
            indent=2,
            sort_keys=True,
        ) + "\n"


def _manifest_path(location: Path) -> Path:
    if location.is_dir() or location.suffix == ".spelunk":
        return location / MANIFEST_FILENAME
    return location


def _store_root(root: Path, manifest: RunManifest) -> Path:
    return root / manifest.storage.root


def _layer_metric_deltas(
    left: LayerSummary,
    right: LayerSummary,
) -> tuple[StatisticDelta, ...]:
    right_statistics = {
        statistic.metric: statistic
        for statistic in right.statistics
        if isinstance(statistic.value, int | float)
    }
    deltas: list[StatisticDelta] = []
    for left_statistic in left.statistics:
        right_statistic = right_statistics.get(left_statistic.metric)
        if right_statistic is None or not isinstance(left_statistic.value, int | float):
            continue
        deltas.append(_statistic_delta(left_statistic, right_statistic))
    if left.activation_count != right.activation_count:
        deltas.append(
            StatisticDelta(
                subject_id=str(left.layer_id),
                metric="activation_count",
                left_value=left.activation_count,
                right_value=right.activation_count,
                delta=float(right.activation_count - left.activation_count),
            )
        )
    if left.feature_count != right.feature_count:
        deltas.append(
            StatisticDelta(
                subject_id=str(left.layer_id),
                metric="feature_count",
                left_value=left.feature_count if left.feature_count is not None else "unknown",
                right_value=right.feature_count if right.feature_count is not None else "unknown",
                delta=_optional_number_delta(left.feature_count, right.feature_count),
            )
        )
    return tuple(deltas)


def _statistic_delta(left: Statistic, right: Statistic) -> StatisticDelta:
    left_value = float(left.value)
    right_value = float(right.value)
    return StatisticDelta(
        subject_id=left.subject_id,
        metric=left.metric,
        left_value=left.value,
        right_value=right.value,
        delta=right_value - left_value,
    )


def _optional_number_delta(left: int | None, right: int | None) -> float | None:
    if left is None or right is None:
        return None
    return float(right - left)
