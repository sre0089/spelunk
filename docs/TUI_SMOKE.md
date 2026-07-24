# TUI Smoke Test

Use this checklist before publishing a release candidate.

## Clean Launch

```bash
spelunk tui
```

Expected:

- Project picker opens.
- Stale recent runs are not shown.
- `?` opens shortcuts.
- `ctrl+p` opens the command palette.

## Run View

```bash
spelunk open /path/to/run.spelunk
```

Expected:

- Overview shows model, dataset, storage, activation layer count, and diagnostics count.
- Layers show activation-count bars.
- Diagnostics show severity-count bars.

## Interactive Actions

Inside a loaded run:

- Press `i` to inspect feature `0` on the selected or first layer.
- Press `c` to compare against another valid recent run.
- Press `r` to generate `report.md` and `report.json`.

Expected:

- Inspect shows feature statistics and top examples.
- Compare shows sorted metric deltas with magnitude bars.
- Reports shows a formatted Markdown preview, artifact paths, and a JSON summary.
