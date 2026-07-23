import asyncio
from pathlib import Path

from pytest import MonkeyPatch
from textual.widgets import Label, ListView, Static

from spelunk.capture import ActivationBatch
from spelunk.config import remember_recent_run
from spelunk.domain import CheckpointId, DatasetId, DatasetRef, LayerId, ModelId, ModelRef, SampleId
from spelunk.services import Session
from spelunk.storage import NumpyShardActivationStore
from spelunk.tui import SpelunkApp


def test_tui_project_picker_renders(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SPELUNK_CONFIG_HOME", str(tmp_path / "config"))

    async def scenario() -> None:
        app = SpelunkApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.title == "Spelunk"
            assert "Open a run with `spelunk open RUN`" in str(
                app.query_one("#primary-copy", Static).render()
            )
            assert app.query_one("#project-actions", ListView).index == 0

    asyncio.run(scenario())


def test_tui_project_picker_renders_recent_runs(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPELUNK_CONFIG_HOME", str(tmp_path / "config"))
    run = _run_with_activations(tmp_path)
    remember_recent_run(run)

    async def scenario() -> None:
        app = SpelunkApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            content = str(app.query_one("#primary-copy", Static).render())
            titles = [str(widget.render()) for widget in app.screen.query(Label)]
            assert str(run.resolve()) in content
            assert any(str(run.resolve()) in title for title in titles)

    asyncio.run(scenario())


def test_tui_project_picker_prunes_stale_recent_runs(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPELUNK_CONFIG_HOME", str(tmp_path / "config"))
    stale = tmp_path / "missing.spelunk"
    remember_recent_run(stale)

    async def scenario() -> None:
        app = SpelunkApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            content = str(app.query_one("#primary-copy", Static).render())
            assert "Open a run with `spelunk open RUN`" in content
            assert str(stale.resolve()) not in content

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


def test_tui_renders_loaded_run_scan(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SPELUNK_CONFIG_HOME", str(tmp_path / "config"))
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


def test_tui_navigation_switches_loaded_run_views(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPELUNK_CONFIG_HOME", str(tmp_path / "config"))
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


def test_tui_generate_reports_action_writes_artifacts(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPELUNK_CONFIG_HOME", str(tmp_path / "config"))
    run = _run_with_activations(tmp_path)

    async def scenario() -> None:
        app = SpelunkApp(run_path=run)
        async with app.run_test() as pilot:
            await pilot.press("r")
            await pilot.pause()
            content = str(app.query_one("#primary-copy", Static).render())
            details = str(app.query_one("#details-copy", Static).render())
            assert "# Spelunk report for run-001" in content
            assert "## Diagnostics" in content
            assert "Generated report.md and report.json" in details
            assert "Markdown:" in details
            assert "JSON:" in details

    asyncio.run(scenario())
    assert (run / "reports" / "report.md").exists()
    assert (run / "reports" / "report.json").exists()


def test_tui_inspect_feature_action_renders_stats(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPELUNK_CONFIG_HOME", str(tmp_path / "config"))
    run = _run_with_activations(tmp_path)

    async def scenario() -> None:
        app = SpelunkApp(run_path=run)
        async with app.run_test() as pilot:
            await pilot.press("i")
            await pilot.pause()
            title = str(app.query_one("#primary-title", Static).render())
            content = str(app.query_one("#primary-copy", Static).render())
            details = str(app.query_one("#details-copy", Static).render())
            assert title == "Inspect Feature"
            assert "Layer: encoder" in content
            assert "Feature: 0" in content
            assert "activation_mean" in content
            assert "Top examples" in details

    asyncio.run(scenario())


def test_tui_compare_action_uses_other_recent_run(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPELUNK_CONFIG_HOME", str(tmp_path / "config"))
    left = _run_with_activations(tmp_path / "left", array=[[1.0, 2.0], [3.0, 4.0]])
    right = _run_with_activations(tmp_path / "right", array=[[2.0, 4.0], [6.0, 8.0]])
    remember_recent_run(right)

    async def scenario() -> None:
        app = SpelunkApp(run_path=left)
        async with app.run_test() as pilot:
            await pilot.press("c")
            await pilot.pause()
            title = str(app.query_one("#primary-title", Static).render())
            content = str(app.query_one("#primary-copy", Static).render())
            details = str(app.query_one("#details-copy", Static).render())
            assert title == "Compare Runs"
            assert "Layer matches: 1" in content
            assert "Metric deltas" in details
            assert "Layer        Metric" in details
            assert "activation_mean" in details

    asyncio.run(scenario())


def test_tui_compare_ignores_stale_recent_run(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPELUNK_CONFIG_HOME", str(tmp_path / "config"))
    run = _run_with_activations(tmp_path)
    remember_recent_run(tmp_path / "deleted.spelunk")

    async def scenario() -> None:
        app = SpelunkApp(run_path=run)
        async with app.run_test() as pilot:
            await pilot.press("c")
            await pilot.pause()
            content = str(app.query_one("#primary-copy", Static).render())
            assert "No other recent run is available to compare" in content
            assert "Comparison failed" not in content

    asyncio.run(scenario())


def test_tui_renders_open_error(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = SpelunkApp(run_path=tmp_path / "missing.spelunk")
        async with app.run_test() as pilot:
            await pilot.pause()
            content = str(app.query_one("#primary-copy", Static).render())
            assert "Could not open run" in content

    asyncio.run(scenario())


def _run_with_activations(
    tmp_path: Path,
    *,
    array: list[list[float]] | None = None,
) -> Path:
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
            array=array or [[0.0, 0.0], [0.0, 0.0]],
            shape=(2, 2),
            dtype="float32",
        )
    )
    return root
