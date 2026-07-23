"""Reusable Textual widgets for the Spelunk shell."""

from __future__ import annotations

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

