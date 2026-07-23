"""Typed state for the terminal application."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from spelunk.domain import CheckpointId, FeatureId, LayerId, RunId
from spelunk.services.results import ScanResult


@dataclass(slots=True)
class AppState:
    active_project: str | None = None
    current_run_id: RunId | None = None
    selected_layer_id: LayerId | None = None
    selected_feature_id: FeatureId | None = None
    selected_checkpoint_id: CheckpointId | None = None
    selected_mode: str = "project"
    breadcrumbs: tuple[str, ...] = ("Projects",)
    capture_status: str = "idle"
    filters: tuple[str, ...] = ()
    search_query: str = ""
    theme: str = "spelunk-dark"
    scan_result: ScanResult | None = None
    error_message: str | None = None
    report_message: str = ""
    recent_runs: tuple[Path, ...] = ()
