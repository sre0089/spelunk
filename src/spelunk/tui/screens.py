"""Textual screens for the Spelunk terminal application."""

from __future__ import annotations

from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static

from spelunk.tui.state import AppState
from spelunk.tui.widgets import Breadcrumbs, StatusBar


class CommandPaletteScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    CommandPaletteScreen {
        align: center middle;
    }

    #palette {
        width: 64;
        height: auto;
        border: tall $accent;
        padding: 1 2;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="palette"):
            yield Static("Command Palette", classes="panel-title")
            yield ListView(
                ListItem(Label("Open recent run")),
                ListItem(Label("Inspect feature")),
                ListItem(Label("Compare recent run")),
                ListItem(Label("Generate reports")),
                ListItem(Label("Show shortcuts")),
            )

    def on_key(self, event: events.Key) -> None:
        if event.key in {"escape", "ctrl+p"}:
            self.dismiss()


class ShortcutOverlayScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    ShortcutOverlayScreen {
        align: center middle;
    }

    #shortcuts {
        width: 58;
        height: auto;
        border: round $accent;
        padding: 1 2;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(
            "\n".join(
                [
                    "Shortcuts",
                    "",
                    "arrows  move selection",
                    "enter   open",
                    "tab     cycle panes",
                    "ctrl+p  command palette",
                    "i       inspect feature",
                    "c       compare recent run",
                    "r       generate reports",
                    "?       shortcuts",
                    "q       quit",
                ]
            ),
            id="shortcuts",
        )

    def on_key(self, event: events.Key) -> None:
        if event.key in {"escape", "question_mark"}:
            self.dismiss()


class InspectFeatureScreen(ModalScreen[tuple[str, str] | None]):
    BINDINGS = [
        ("enter", "submit", "Inspect"),
        ("escape", "cancel", "Cancel"),
    ]
    DEFAULT_CSS = """
    InspectFeatureScreen {
        align: center middle;
    }

    #inspect-feature-panel {
        width: 72;
        height: auto;
        border: tall $accent;
        padding: 1 2;
        background: $surface;
    }

    #inspect-layer-list {
        height: auto;
        margin-bottom: 1;
    }

    #inspect-feature-input {
        margin-top: 1;
    }
    """

    def __init__(
        self,
        layers: tuple[str, ...],
        *,
        selected_layer_id: str | None = None,
        selected_feature_id: str | None = None,
    ) -> None:
        super().__init__()
        self.layer_ids = layers
        self.selected_layer_id = selected_layer_id
        self.selected_feature_id = selected_feature_id or "0"

    def compose(self) -> ComposeResult:
        items = [
            ListItem(Label(layer_id), id=f"inspect-layer-{index}")
            for index, layer_id in enumerate(self.layer_ids)
        ]
        with Vertical(id="inspect-feature-panel"):
            yield Static("Inspect Feature", classes="panel-title")
            yield Static("Choose a layer, enter a feature id, then press Enter.")
            yield ListView(*items, id="inspect-layer-list")
            yield Input(
                value=self.selected_feature_id,
                placeholder="Feature id, for example 0",
                id="inspect-feature-input",
            )

    def on_mount(self) -> None:
        if not self.layer_ids:
            return
        layer_list = self.query_one("#inspect-layer-list", ListView)
        selected_index = 0
        if self.selected_layer_id in self.layer_ids:
            selected_index = self.layer_ids.index(str(self.selected_layer_id))
        layer_list.index = selected_index

    def action_submit(self) -> None:
        if not self.layer_ids:
            self.dismiss(None)
            return
        layer_list = self.query_one("#inspect-layer-list", ListView)
        selected_index = layer_list.index or 0
        selected_index = max(0, min(selected_index, len(self.layer_ids) - 1))
        feature_input = self.query_one("#inspect-feature-input", Input)
        feature_id = feature_input.value.strip() or "0"
        self.dismiss((self.layer_ids[selected_index], feature_id))

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "inspect-layer-list":
            event.stop()
            self.action_submit()


class CompareRunScreen(ModalScreen[Path | None]):
    BINDINGS = [
        ("enter", "submit", "Compare"),
        ("escape", "cancel", "Cancel"),
    ]
    DEFAULT_CSS = """
    CompareRunScreen {
        align: center middle;
    }

    #compare-run-panel {
        width: 82;
        height: auto;
        border: tall $accent;
        padding: 1 2;
        background: $surface;
    }

    #compare-run-list {
        height: auto;
    }
    """

    def __init__(self, run_paths: tuple[Path, ...]) -> None:
        super().__init__()
        self.run_paths = run_paths

    def compose(self) -> ComposeResult:
        items = [
            ListItem(Label(f"{path.stem}  {path}"), id=f"compare-run-{index}")
            for index, path in enumerate(self.run_paths)
        ]
        with Vertical(id="compare-run-panel"):
            yield Static("Compare Run", classes="panel-title")
            yield Static("Choose a recent run to compare with this run.")
            yield ListView(*items, id="compare-run-list")

    def action_submit(self) -> None:
        if not self.run_paths:
            self.dismiss(None)
            return
        run_list = self.query_one("#compare-run-list", ListView)
        selected_index = run_list.index or 0
        selected_index = max(0, min(selected_index, len(self.run_paths) - 1))
        self.dismiss(self.run_paths[selected_index])

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "compare-run-list":
            event.stop()
            self.action_submit()


class ProjectPickerScreen(Screen[None]):
    BINDINGS = [
        ("ctrl+p", "command_palette", "Command Palette"),
        ("?", "shortcuts", "Shortcuts"),
        ("q", "app.quit", "Quit"),
    ]

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.app_state = state
        self.breadcrumbs = Breadcrumbs()
        self.status = StatusBar()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        self.breadcrumbs.update_state(self.app_state)
        yield self.breadcrumbs
        with Horizontal(id="shell"):
            with Vertical(id="nav"):
                yield Static("Spelunk", classes="brand")
                yield ListView(
                    ListItem(Label("Recent runs")),
                    ListItem(Label("Create capture run")),
                    ListItem(Label("Open run directory")),
                    ListItem(Label("Settings")),
                    id="project-actions",
                )
            with Vertical(id="content"):
                yield Static("Project Picker", classes="panel-title")
                yield Static(
                    "Select a run or create a capture plan. "
                    "Backend services are ready for manifest-backed runs.",
                    id="primary-copy",
                )
            with Vertical(id="details"):
                yield Static("Details", classes="panel-title")
                yield Static("No run selected.")
        self.status.update_state(self.app_state)
        yield self.status
        yield Footer()

    def action_command_palette(self) -> None:
        self.app.push_screen(CommandPaletteScreen())

    def action_shortcuts(self) -> None:
        self.app.push_screen(ShortcutOverlayScreen())
