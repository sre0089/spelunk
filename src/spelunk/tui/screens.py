"""Textual screens for the Spelunk terminal application."""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

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
                ListItem(Label("Open project")),
                ListItem(Label("Scan run")),
                ListItem(Label("Generate report")),
                ListItem(Label("Settings")),
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
                    "/       search",
                    "?       shortcuts",
                    "q       quit",
                ]
            ),
            id="shortcuts",
        )

    def on_key(self, event: events.Key) -> None:
        if event.key in {"escape", "question_mark"}:
            self.dismiss()


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
