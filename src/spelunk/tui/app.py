"""Textual application shell for Spelunk."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

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

    def _load_run(self, run_path: str | Path) -> None:
        try:
            scan_result = Session.open(run_path).scan()
        except Exception as error:  # noqa: BLE001
            self.app_state.error_message = str(error)
            self.app_state.selected_mode = "project"
            self.app_state.breadcrumbs = ("Projects", "Open failed")
            return
        self._apply_scan_result(scan_result)

    def _apply_scan_result(self, scan_result: ScanResult) -> None:
        self.app_state.scan_result = scan_result
        self.app_state.current_run_id = scan_result.run.run_id
        self.app_state.selected_mode = "scan"
        self.app_state.breadcrumbs = ("Projects", str(scan_result.run.run_id), "Scan")

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
            ListItem(Label("Overview")),
            ListItem(Label("Layers")),
            ListItem(Label("Diagnostics")),
            ListItem(Label("Reports")),
            id="project-actions",
        )

    def _content(self) -> ComposeResult:
        if self.app_state.error_message is not None:
            yield Static("Project Picker", classes="panel-title")
            yield Static(f"Could not open run: {self.app_state.error_message}", id="primary-copy")
            return
        if self.app_state.scan_result is None:
            yield Static("Project Picker", classes="panel-title")
            yield Static(
                "Select a run or create a capture plan. "
                "Backend services are ready for manifest-backed runs.",
                id="primary-copy",
            )
            return

        scan = self.app_state.scan_result
        yield Static(f"Run {scan.run.run_id}", classes="panel-title")
        yield Static(
            "\n".join(
                [
                    f"Model: {scan.run.model.name}",
                    f"Architecture: {scan.run.model.architecture_family}",
                    f"Dataset: {scan.run.dataset.name}",
                    f"Storage: {scan.run.storage_backend}",
                    f"Layers with activations: {len(scan.layers)}",
                    f"Diagnostics: {len(scan.diagnostics)}",
                ]
            ),
            id="primary-copy",
        )
        yield Static(_layer_summary_text(scan), id="layer-summary")

    def _details(self) -> ComposeResult:
        yield Static("Details", classes="panel-title")
        if self.app_state.scan_result is None:
            yield Static("No run selected.", id="details-copy")
            return
        yield Static(_diagnostic_summary_text(self.app_state.scan_result), id="details-copy")


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


def _diagnostic_summary_text(scan: ScanResult) -> str:
    if not scan.diagnostics:
        return "No diagnostics available."
    lines = ["Diagnostics"]
    for diagnostic in scan.diagnostics:
        lines.append(f"- {diagnostic.severity.upper()}: {diagnostic.conclusion}")
    return "\n".join(lines)
