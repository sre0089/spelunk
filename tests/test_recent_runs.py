from pathlib import Path

from spelunk.config import (
    is_valid_run_path,
    load_recent_runs,
    prune_stale_recent_runs,
    remember_recent_run,
)


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


def test_prune_stale_recent_runs_keeps_only_manifest_backed_runs(tmp_path: Path) -> None:
    storage = tmp_path / "recent-runs.json"
    valid = tmp_path / "valid.spelunk"
    stale = tmp_path / "stale.spelunk"
    valid.mkdir()
    (valid / "manifest.json").write_text("{}")
    remember_recent_run(stale, path=storage)
    remember_recent_run(valid, path=storage)

    assert prune_stale_recent_runs(storage) == (valid.resolve(),)
    assert load_recent_runs(storage) == (valid.resolve(),)
    assert is_valid_run_path(valid)
    assert not is_valid_run_path(stale)
