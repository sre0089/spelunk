import asyncio

from textual.widgets import ListView, Static

from spelunk.tui import SpelunkApp


def test_tui_project_picker_renders() -> None:
    async def scenario() -> None:
        app = SpelunkApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.title == "Spelunk"
            assert "Select a run" in str(app.query_one("#primary-copy", Static).render())
            assert app.query_one("#project-actions", ListView).index == 0

    asyncio.run(scenario())


def test_tui_command_palette_opens() -> None:
    async def scenario() -> None:
        app = SpelunkApp()
        async with app.run_test() as pilot:
            await pilot.press("ctrl+p")
            await pilot.pause()
            titles = [str(widget.render()) for widget in app.screen.query(Static)]
            assert "Command Palette" in titles

    asyncio.run(scenario())
