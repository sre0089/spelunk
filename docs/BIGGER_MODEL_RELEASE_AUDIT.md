# Bigger-Model Release Audit

Audit workspace: `/tmp/spelunk-release-audit-m47`

## Covered Workflows

- Generated a 512 sample, 16-dimensional NumPy dataset.
- Discovered layers with `spelunk layers --model-path model_factory.py --factory build_model`.
- Generated a starter config with `spelunk init`.
- Captured from the generated config with `spelunk capture generated-spelunk.json`.
- Captured directly from flags with `spelunk capture --run ... --model-path ... --dataset ... --layers ...`.
- Ran `spelunk quickstart` to capture, scan, generate Markdown and JSON reports, and print the TUI handoff.
- Scanned larger runs with `spelunk scan --json`.
- Inspected a feature with `spelunk inspect --json`.
- Generated Markdown reports with `spelunk report --format markdown`.
- Compared baseline and variant runs with `spelunk compare --json`.
- Captured a Zarr-backed run with `--storage-backend zarr`.
- Verified duplicate-run protection.
- Verified invalid layer errors.
- Captured from Python with `spelunk.capture(...)`.
- Re-ran focused TUI, Python API, and recent-run automated tests.

## Finding

`spelunk quickstart` originally completed capture/report generation but could crash while remembering a recent run if user config storage was unavailable. Recent-run writes are now best-effort, matching stale-run pruning behavior, so workflow commands do not fail only because local TUI history cannot be written.

## Result

The low-friction workflow is ready for final package/build validation.
