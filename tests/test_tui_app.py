import asyncio
from pathlib import Path

from textual.widgets import ListView, Static

from spelunk.capture import ActivationBatch
from spelunk.domain import CheckpointId, DatasetId, DatasetRef, LayerId, ModelId, ModelRef, SampleId
from spelunk.services import Session
from spelunk.storage import NumpyShardActivationStore
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


def test_tui_renders_loaded_run_scan(tmp_path: Path) -> None:
    run = _run_with_activations(tmp_path)

    async def scenario() -> None:
        app = SpelunkApp(run_path=run)
        async with app.run_test() as pilot:
            await pilot.pause()
            content = str(app.query_one("#primary-copy", Static).render())
            details = str(app.query_one("#details-copy", Static).render())
            layers = str(app.query_one("#layer-summary", Static).render())
            assert "Model: Tiny AE" in content
            assert "Layers with activations: 1" in content
            assert "encoder: activations=2" in layers
            assert "CRITICAL" in details
            assert "inactive" in details

    asyncio.run(scenario())


def test_tui_navigation_switches_loaded_run_views(tmp_path: Path) -> None:
    run = _run_with_activations(tmp_path)

    async def scenario() -> None:
        app = SpelunkApp(run_path=run)
        async with app.run_test() as pilot:
            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()
            title = str(app.query_one("#primary-title", Static).render())
            content = str(app.query_one("#primary-copy", Static).render())
            details = str(app.query_one("#details-copy", Static).render())
            assert title == "Layers"
            assert "encoder: activations=2" in content
            assert "Statistics" in details

    asyncio.run(scenario())


def test_tui_renders_open_error(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = SpelunkApp(run_path=tmp_path / "missing.spelunk")
        async with app.run_test() as pilot:
            await pilot.pause()
            content = str(app.query_one("#primary-copy", Static).render())
            assert "Could not open run" in content

    asyncio.run(scenario())


def _run_with_activations(tmp_path: Path) -> Path:
    root = tmp_path / "run-001.spelunk"
    session = Session.create(
        root,
        model=ModelRef(
            id=ModelId("model-001"),
            name="Tiny AE",
            architecture_family="autoencoder",
            framework="pytorch",
        ),
        dataset=DatasetRef(
            id=DatasetId("dataset-001"),
            name="sample",
            source_uri="file://sample.npy",
            kind="numpy",
        ),
    )
    store = NumpyShardActivationStore(session.root / "activations")
    store.write_batch(
        ActivationBatch(
            run_id=session.run_id,
            checkpoint_id=CheckpointId("ckpt-001"),
            layer_id=LayerId("encoder"),
            sample_ids=(SampleId("sample-0"), SampleId("sample-1")),
            array=[[0.0, 0.0], [0.0, 0.0]],
            shape=(2, 2),
            dtype="float32",
        )
    )
    return root
