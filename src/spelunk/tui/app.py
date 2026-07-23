"""Textual application shell for Spelunk."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

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
        self._apply_scan_result(scan_result)

    def _apply_scan_result(self, scan_result: ScanResult) -> None:
        self.app_state.scan_result = scan_result
        self.app_state.current_run_id = scan_result.run.run_id
        self.app_state.selected_mode = "overview"
        self.app_state.breadcrumbs = ("Projects", str(scan_result.run.run_id), "Overview")

    def _navigation(self) -> ListView:
        if self.app_state.scan_result is None:
            return ListView(
                ListItem(Label("Recent runs")),
                ListItem(Label("Create capture run")),
                ListItem(Label("Open run directory")),
                ListItem(Label("Settings")),
                id="project-actions",
            )
        return ListView(
            ListItem(Label("Overview"), id="overview-action"),
            ListItem(Label("Layers"), id="layers-action"),
            ListItem(Label("Diagnostics"), id="diagnostics-action"),
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
                "Select a run or create a capture plan. "
                "Backend services are ready for manifest-backed runs.",
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


def _primary_title_text(state: AppState) -> str:
    scan = state.scan_result
    if scan is None:
        return "Project Picker"
    if state.selected_mode == "layers":
        return "Layers"
    if state.selected_mode == "diagnostics":
        return "Diagnostics"
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


def _mode_from_item_id(item_id: str | None) -> str | None:
    if item_id is None:
        return None
    return {
        "overview-action": "overview",
        "layers-action": "layers",
        "diagnostics-action": "diagnostics",
        "reports-action": "reports",
    }.get(item_id)
