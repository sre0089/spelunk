"""Recent run path storage."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from spelunk.errors import ManifestError

DEFAULT_LIMIT = 10


def recent_runs_path() -> Path:
    config_home = os.environ.get("SPELUNK_CONFIG_HOME")
    if config_home:
        return Path(config_home) / "recent-runs.json"
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / "spelunk" / "recent-runs.json"
    return Path.home() / ".config" / "spelunk" / "recent-runs.json"


def load_recent_runs(path: Path | None = None) -> tuple[Path, ...]:
    storage_path = path or recent_runs_path()
    if not storage_path.exists():
        return ()
    try:
        payload: Any = json.loads(storage_path.read_text())
    except json.JSONDecodeError as error:
        raise ManifestError(f"Recent runs file is not valid JSON: {storage_path}") from error
    if not isinstance(payload, list):
        raise ManifestError(f"Recent runs file must contain a JSON array: {storage_path}")
    runs: list[Path] = []
    for item in payload:
        if isinstance(item, str) and item:
            runs.append(Path(item))
    return tuple(runs)


def remember_recent_run(
    run: str | Path,
    *,
    path: Path | None = None,
    limit: int = DEFAULT_LIMIT,
) -> None:
    storage_path = path or recent_runs_path()
    normalized = Path(run).expanduser().resolve()
    existing = [item for item in load_recent_runs(storage_path) if item != normalized]
    updated = (normalized, *existing[: max(limit - 1, 0)])
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_text(json.dumps([str(item) for item in updated], indent=2) + "\n")
