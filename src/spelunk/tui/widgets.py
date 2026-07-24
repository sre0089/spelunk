"""Reusable Textual widgets for the Spelunk shell."""

from __future__ import annotations

from typing import Any

from rich.markdown import Markdown
from textual.widgets import Static

from spelunk.tui.state import AppState


class Breadcrumbs(Static):
    def update_state(self, state: AppState) -> None:
        self.update(" / ".join(state.breadcrumbs))


class StatusBar(Static):
    def update_state(self, state: AppState) -> None:
        run = state.current_run_id or "no run"
        self.update(
            f"mode={state.selected_mode} | run={run} | capture={state.capture_status} | ? help"
        )


class MarkdownViewer(Static):
    """Static pane that can switch between plain text and Rich Markdown."""

    def __init__(self, content: str = "", **kwargs: Any) -> None:
        super().__init__(content, **kwargs)
        self.markdown_source = ""

    def update_text(self, text: str) -> None:
        self.markdown_source = ""
        self.update(text)

    def update_markdown(self, source: str) -> None:
        self.markdown_source = source
        self.update(Markdown(source))
