from pathlib import Path

from spelunk.config import load_recent_runs, remember_recent_run


def test_remember_recent_run_deduplicates_and_limits(tmp_path: Path) -> None:
    storage = tmp_path / "recent-runs.json"
    first = tmp_path / "first.spelunk"
    second = tmp_path / "second.spelunk"
    third = tmp_path / "third.spelunk"

    remember_recent_run(first, path=storage, limit=2)
    remember_recent_run(second, path=storage, limit=2)
    remember_recent_run(first, path=storage, limit=2)
    remember_recent_run(third, path=storage, limit=2)

    assert load_recent_runs(storage) == (third.resolve(), first.resolve())


def test_load_recent_runs_missing_file_returns_empty_tuple(tmp_path: Path) -> None:
    assert load_recent_runs(tmp_path / "missing.json") == ()
