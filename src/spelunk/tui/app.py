"""Textual application shell for Spelunk."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from spelunk.config import is_valid_run_path, prune_stale_recent_runs, remember_recent_run
from spelunk.errors import SpelunkError
from spelunk.services import Session
from spelunk.services.results import ScanResult
from spelunk.tui.screens import CommandPaletteScreen, ShortcutOverlayScreen
from spelunk.tui.state import AppState
from spelunk.tui.widgets import Breadcrumbs, StatusBar


class SpelunkApp(App[None]):
    """Terminal-native application for representation exploration."""

    CSS = """
    Screen {
        background: #101418;
        color: #d8dee9;
    }

    Breadcrumbs {
        dock: top;
        height: 1;
        padding: 0 1;
        background: #151b20;
        color: #8fb3ff;
    }

    #shell {
        height: 1fr;
    }

    #nav {
        width: 28;
        border-right: solid #2e3a44;
        padding: 1;
    }

    #content {
        width: 1fr;
        padding: 1 2;
    }

    #details {
        width: 32;
        border-left: solid #2e3a44;
        padding: 1;
    }

    StatusBar {
        dock: bottom;
        height: 1;
        padding: 0 1;
        background: #151b20;
        color: #a3be8c;
    }

    .brand {
        text-style: bold;
        color: #f0c674;
        margin-bottom: 1;
    }

    .panel-title {
        text-style: bold;
        color: #d8dee9;
        margin-bottom: 1;
    }

    ListView {
        height: auto;
    }

    ListView:focus {
        border: tall #8fb3ff;
    }
    """

    TITLE = "Spelunk"
    BINDINGS = [
        ("ctrl+p", "command_palette", "Command Palette"),
        ("?", "shortcuts", "Shortcuts"),
        ("c", "compare_recent_run", "Compare"),
        ("i", "inspect_feature", "Inspect Feature"),
        ("r", "generate_reports", "Generate Reports"),
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        state: AppState | None = None,
        *,
        run_path: str | Path | None = None,
    ) -> None:
        super().__init__()
        self.app_state = state or AppState()
        self.session: Session | None = None
        if state is None:
            self.app_state.recent_runs = prune_stale_recent_runs()
        if run_path is not None:
            self._load_run(run_path)
        self.breadcrumbs = Breadcrumbs()
        self.status = StatusBar()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        self.breadcrumbs.update_state(self.app_state)
        yield self.breadcrumbs
        with Horizontal(id="shell"):
            with Vertical(id="nav"):
                yield Static("Spelunk", classes="brand")
                yield self._navigation()
            with Vertical(id="content"):
                yield from self._content()
            with Vertical(id="details"):
                yield from self._details()
        self.status.update_state(self.app_state)
        yield self.status
        yield Footer()

    def action_command_palette(self) -> None:
        self.push_screen(CommandPaletteScreen())

    def action_shortcuts(self) -> None:
        self.push_screen(ShortcutOverlayScreen())

    def action_generate_reports(self) -> None:
        if self.session is None or self.app_state.scan_result is None:
            return
        try:
            markdown = self.session.report(format="markdown")
            json_report = self.session.report(format="json")
        except SpelunkError as error:
            self.app_state.report_message = f"Report generation failed: {error}"
        else:
            self.app_state.report_message = (
                f"Generated {markdown.path.name} and {json_report.path.name}"
            )
        self.app_state.selected_mode = "reports"
        self.app_state.breadcrumbs = (
            "Projects",
            str(self.app_state.scan_result.run.run_id),
            "Reports",
        )
        self._refresh_loaded_run_view()

    def action_inspect_feature(self) -> None:
        if self.session is None or self.app_state.scan_result is None:
            return
        if not self.app_state.scan_result.layers:
            self.app_state.report_message = "No activation layers are available to inspect."
            self.app_state.selected_mode = "inspect"
            self._refresh_loaded_run_view()
            return
        layer_id = self.app_state.selected_layer_id or self.app_state.scan_result.layers[0].layer_id
        feature_id = self.app_state.selected_feature_id or "0"
        try:
            result = self.session.inspect_feature(
                layer_id=str(layer_id),
                feature_id=str(feature_id),
            )
        except SpelunkError as error:
            self.app_state.report_message = f"Feature inspection failed: {error}"
        else:
            self.app_state.feature_inspection = result
            self.app_state.selected_layer_id = result.feature.layer_id
            self.app_state.selected_feature_id = result.feature.feature_id
            self.app_state.report_message = ""
        self.app_state.selected_mode = "inspect"
        self.app_state.breadcrumbs = (
            "Projects",
            str(self.app_state.scan_result.run.run_id),
            "Inspect",
        )
        self._refresh_loaded_run_view()

    def action_compare_recent_run(self) -> None:
        if self.session is None or self.app_state.scan_result is None:
            return
        target_path = _comparison_target(self.session.root, self.app_state.recent_runs)
        if target_path is None:
            self.app_state.report_message = "No other recent run is available to compare."
            self.app_state.selected_mode = "compare"
            self._refresh_loaded_run_view()
            return
        try:
            target = Session.open(target_path)
            result = self.session.compare(target)
        except SpelunkError as error:
            self.app_state.report_message = f"Comparison failed: {error}"
        else:
            self.app_state.comparison_result = result
            self.app_state.report_message = ""
        self.app_state.selected_mode = "compare"
        self.app_state.breadcrumbs = (
            "Projects",
            str(self.app_state.scan_result.run.run_id),
            "Compare",
        )
        self._refresh_loaded_run_view()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id != "project-actions" or self.app_state.scan_result is None:
            return
        selected_mode = _mode_from_item_id(event.item.id)
        if selected_mode is None:
            return
        self.app_state.selected_mode = selected_mode
        self.app_state.breadcrumbs = (
            "Projects",
            str(self.app_state.scan_result.run.run_id),
            selected_mode.title(),
        )
        self._refresh_loaded_run_view()

    def _refresh_loaded_run_view(self) -> None:
        self.breadcrumbs.update_state(self.app_state)
        self.status.update_state(self.app_state)
        self.query_one("#primary-title", Static).update(_primary_title_text(self.app_state))
        self.query_one("#primary-copy", Static).update(_primary_copy_text(self.app_state))
        self.query_one("#layer-summary", Static).update(_secondary_content_text(self.app_state))
        self.query_one("#details-copy", Static).update(_details_text(self.app_state))

    def _load_run(self, run_path: str | Path) -> None:
        try:
            self.session = Session.open(run_path)
            scan_result = self.session.scan()
        except Exception as error:  # noqa: BLE001
            self.session = None
            self.app_state.error_message = str(error)
            self.app_state.selected_mode = "project"
            self.app_state.breadcrumbs = ("Projects", "Open failed")
            return
        remember_recent_run(self.session.root)
        self.app_state.recent_runs = prune_stale_recent_runs()
        self._apply_scan_result(scan_result)

    def _apply_scan_result(self, scan_result: ScanResult) -> None:
        self.app_state.scan_result = scan_result
        self.app_state.current_run_id = scan_result.run.run_id
        self.app_state.selected_mode = "overview"
        self.app_state.breadcrumbs = ("Projects", str(scan_result.run.run_id), "Overview")

    def _navigation(self) -> ListView:
        if self.app_state.scan_result is None:
            recent_items = [
                ListItem(Label(str(path)), id=f"recent-run-{index}")
                for index, path in enumerate(self.app_state.recent_runs)
            ]
            if not recent_items:
                recent_items = [ListItem(Label("No recent runs"), id="no-recent-runs")]
            return ListView(*recent_items, id="project-actions")
        return ListView(
            ListItem(Label("Overview"), id="overview-action"),
            ListItem(Label("Layers"), id="layers-action"),
            ListItem(Label("Diagnostics"), id="diagnostics-action"),
            ListItem(Label("Inspect"), id="inspect-action"),
            ListItem(Label("Compare"), id="compare-action"),
            ListItem(Label("Reports"), id="reports-action"),
            id="project-actions",
        )

    def _content(self) -> ComposeResult:
        if self.app_state.error_message is not None:
            yield Static("Project Picker", classes="panel-title", id="primary-title")
            yield Static(f"Could not open run: {self.app_state.error_message}", id="primary-copy")
            return
        if self.app_state.scan_result is None:
            yield Static("Project Picker", classes="panel-title", id="primary-title")
            yield Static(
                _project_picker_text(self.app_state),
                id="primary-copy",
            )
            return

        yield Static(_primary_title_text(self.app_state), classes="panel-title", id="primary-title")
        yield Static(_primary_copy_text(self.app_state), id="primary-copy")
        yield Static(_secondary_content_text(self.app_state), id="layer-summary")

    def _details(self) -> ComposeResult:
        yield Static("Details", classes="panel-title")
        yield Static(_details_text(self.app_state), id="details-copy")


def run_tui(run_path: str | Path | None = None) -> None:
    """Launch the Spelunk TUI."""
    SpelunkApp(run_path=run_path).run()


def _layer_summary_text(scan: ScanResult) -> str:
    if not scan.layers:
        return "No stored activation layers yet."
    lines = ["Layers"]
    for summary in scan.layers:
        lines.append(
            f"- {summary.layer_id}: activations={summary.activation_count}, "
            f"features={summary.feature_count}"
        )
    return "\n".join(lines)


def _project_picker_text(state: AppState) -> str:
    if not state.recent_runs:
        return "Open a run with `spelunk open RUN` to add it to recent runs."
    lines = ["Recent runs"]
    for path in state.recent_runs:
        lines.append(f"- {path}")
    return "\n".join(lines)


def _primary_title_text(state: AppState) -> str:
    scan = state.scan_result
    if scan is None:
        return "Project Picker"
    if state.selected_mode == "layers":
        return "Layers"
    if state.selected_mode == "diagnostics":
        return "Diagnostics"
    if state.selected_mode == "inspect":
        return "Inspect Feature"
    if state.selected_mode == "compare":
        return "Compare Runs"
    if state.selected_mode == "reports":
        return "Reports"
    return f"Run {scan.run.run_id}"


def _primary_copy_text(state: AppState) -> str:
    scan = state.scan_result
    if scan is None:
        return "No run selected."
    if state.selected_mode == "layers":
        return _layer_summary_text(scan)
    if state.selected_mode == "diagnostics":
        return _diagnostic_summary_text(scan)
    if state.selected_mode == "inspect":
        return _feature_inspection_text(state)
    if state.selected_mode == "compare":
        return _comparison_summary_text(state)
    if state.selected_mode == "reports":
        return "\n".join(
            [
                "Available exports",
                "- Markdown: narrative scan report",
                "- JSON: machine-readable scan report",
            ]
        )
    return "\n".join(
        [
            f"Model: {scan.run.model.name}",
            f"Architecture: {scan.run.model.architecture_family}",
            f"Dataset: {scan.run.dataset.name}",
            f"Storage: {scan.run.storage_backend}",
            f"Layers with activations: {len(scan.layers)}",
            f"Diagnostics: {len(scan.diagnostics)}",
        ]
    )


def _secondary_content_text(state: AppState) -> str:
    scan = state.scan_result
    if scan is None:
        return ""
    if state.selected_mode == "overview":
        return _layer_summary_text(scan)
    if state.selected_mode == "layers":
        return _statistics_summary_text(scan)
    if state.selected_mode == "diagnostics":
        return _diagnostic_evidence_text(scan)
    if state.selected_mode == "inspect":
        return _feature_examples_text(state)
    if state.selected_mode == "compare":
        return _comparison_delta_text(state)
    if state.selected_mode == "reports":
        return state.report_message or "Reports have not been generated in this TUI session."
    return ""


def _details_text(state: AppState) -> str:
    scan = state.scan_result
    if scan is None:
        return "No run selected."
    if state.selected_mode == "diagnostics":
        return _diagnostic_evidence_text(scan)
    if state.selected_mode == "layers":
        return _statistics_summary_text(scan)
    if state.selected_mode == "inspect":
        return _feature_examples_text(state)
    if state.selected_mode == "compare":
        return _comparison_delta_text(state)
    if state.selected_mode == "reports":
        return state.report_message or _diagnostic_summary_text(scan)
    return _diagnostic_summary_text(scan)


def _statistics_summary_text(scan: ScanResult) -> str:
    if not scan.layers:
        return "No layer statistics available."
    lines = ["Statistics"]
    for summary in scan.layers:
        if not summary.statistics:
            lines.append(f"- {summary.layer_id}: no statistics")
            continue
        for statistic in summary.statistics:
            lines.append(
                f"- {summary.layer_id} {statistic.metric}: "
                f"{statistic.value:.6g} over {statistic.sample_count} samples"
            )
    return "\n".join(lines)


def _diagnostic_evidence_text(scan: ScanResult) -> str:
    if not scan.diagnostics:
        return "No diagnostic evidence available."
    lines = ["Evidence"]
    for diagnostic in scan.diagnostics:
        if not diagnostic.evidence:
            lines.append(f"- {diagnostic.id}: no evidence")
            continue
        for item in diagnostic.evidence:
            lines.append(f"- {diagnostic.id} {item.label}: {item.value}")
    return "\n".join(lines)


def _diagnostic_summary_text(scan: ScanResult) -> str:
    if not scan.diagnostics:
        return "No diagnostics available."
    lines = ["Diagnostics"]
    for diagnostic in scan.diagnostics:
        lines.append(f"- {diagnostic.severity.upper()}: {diagnostic.conclusion}")
    return "\n".join(lines)


def _feature_inspection_text(state: AppState) -> str:
    if state.report_message:
        return state.report_message
    result = state.feature_inspection
    if result is None:
        return "Press `i` to inspect feature 0 on the first activation layer."
    lines = [
        f"Layer: {result.feature.layer_id}",
        f"Feature: {result.feature.feature_id}",
        "Statistics",
    ]
    for statistic in result.feature.statistics:
        lines.append(
            f"- {statistic.metric}: {statistic.value:.6g} "
            f"over {statistic.sample_count} samples"
        )
    return "\n".join(lines)


def _feature_examples_text(state: AppState) -> str:
    if state.report_message:
        return state.report_message
    result = state.feature_inspection
    if result is None:
        return "No feature inspected yet."
    if not result.feature.top_examples:
        return "No top examples available."
    examples = "\n".join(f"- {sample_id}" for sample_id in result.feature.top_examples)
    return f"Top examples\n{examples}"


def _comparison_target(current_root: Path, recent_runs: tuple[Path, ...]) -> Path | None:
    current = current_root.expanduser().resolve()
    for path in recent_runs:
        candidate = path.expanduser().resolve()
        if candidate != current and is_valid_run_path(candidate):
            return candidate
    return None


def _comparison_summary_text(state: AppState) -> str:
    if state.report_message:
        return state.report_message
    result = state.comparison_result
    if result is None:
        return "Press `c` to compare this run with another recent run."
    comparison = result.comparison
    return "\n".join(
        [
            f"Left: {comparison.left_run_id}",
            f"Right: {comparison.right_run_id}",
            f"Layer matches: {len(comparison.layer_matches)}",
            f"Metric deltas: {len(comparison.metric_deltas)}",
            f"Diagnostics: {len(comparison.diagnostics)}",
        ]
    )


def _comparison_delta_text(state: AppState) -> str:
    if state.report_message:
        return state.report_message
    result = state.comparison_result
    if result is None:
        return "No comparison has been run yet."
    deltas = result.comparison.metric_deltas
    if not deltas:
        return "No metric deltas found."
    lines = ["Metric deltas"]
    for delta in deltas[:8]:
        lines.append(
            f"- {delta.subject_id} {delta.metric}: "
            f"{delta.left_value} -> {delta.right_value} ({delta.delta})"
        )
    return "\n".join(lines)


def _mode_from_item_id(item_id: str | None) -> str | None:
    if item_id is None:
        return None
    return {
        "overview-action": "overview",
        "layers-action": "layers",
        "diagnostics-action": "diagnostics",
        "inspect-action": "inspect",
        "compare-action": "compare",
        "reports-action": "reports",
    }.get(item_id)
