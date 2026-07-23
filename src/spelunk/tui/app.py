"""Textual application shell for Spelunk."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

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

    def __init__(self, state: AppState | None = None) -> None:
        super().__init__()
        self.app_state = state or AppState()
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
        self.push_screen(CommandPaletteScreen())

    def action_shortcuts(self) -> None:
        self.push_screen(ShortcutOverlayScreen())


def run_tui() -> None:
    """Launch the Spelunk TUI."""
    SpelunkApp().run()
