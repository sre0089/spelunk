"""Session service for local Spelunk runs."""

from __future__ import annotations

import json
from pathlib import Path

from spelunk.analysis import summarize_layers
from spelunk.diagnostics import ActivationHealthDiagnostic, DiagnosticContext
from spelunk.domain import (
    Checkpoint,
    DatasetRef,
    ModelRef,
    Report,
    ReportFormat,
    ReportId,
    ReportSection,
    RunId,
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
        raise UnsupportedOperationError(
            f"Run comparison is not implemented yet for '{self.run_id}' and '{other.run_id}'. "
            "See M11 in docs/ROADMAP.md."
        )

    def report(self, *, format: ReportFormat = "markdown") -> ReportResult:
        if format == "markdown":
            content = self._report_markdown()
        elif format == "json":
            content = self._report_json()
        else:
            raise UnsupportedOperationError(f"Unsupported report format: {format}")

        report = Report(
            id=ReportId(f"{self.run_id}-summary"),
            run_id=self.run_id,
            title=f"Spelunk summary for {self.run_id}",
            sections=(ReportSection(title="Run Summary", body=content),),
            formats=frozenset({format}),
        )
        return ReportResult(report=report, format=format, content=content)

    def _report_markdown(self) -> str:
        summary = self.summary()
        return "\n".join(
            [
                f"# Spelunk summary for {summary.run_id}",
                "",
                f"- Model: {summary.model.name}",
                f"- Architecture: {summary.model.architecture_family}",
                f"- Framework: {summary.model.framework}",
                f"- Dataset: {summary.dataset.name}",
                f"- Checkpoints: {summary.checkpoint_count}",
                f"- Layers: {summary.layer_count}",
                "",
            ]
        )

    def _report_json(self) -> str:
        summary = self.summary()
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
            },
            indent=2,
            sort_keys=True,
        )


def _manifest_path(location: Path) -> Path:
    if location.is_dir() or location.suffix == ".spelunk":
        return location / MANIFEST_FILENAME
    return location


def _store_root(root: Path, manifest: RunManifest) -> Path:
    return root / manifest.storage.root
