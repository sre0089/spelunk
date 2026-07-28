# Changelog

## 0.1.0a2

TUI polish and release hardening patch alpha.

### Added

- Native TUI prompts for feature inspection and recent-run comparison.
- PyTorch checkpoint loading through `--checkpoint-path` and `model.checkpoint_path`.
- Feature-level activation health diagnostics for dead features.
- Diagnostics documentation for activation health evidence and severity.
- Public-channel smoke documentation and TUI release QA notes.

### Changed

- Inspect and compare shortcuts now open explicit selection flows before running.
- README status and docs now reflect checkpoint support and richer diagnostics.

## 0.1.0a1

First published pre-alpha release.

### Added

- Local run manifests and session services.
- JSON/TOML capture config execution.
- PyTorch activation capture through selected forward hooks.
- Spelunk-owned dataset loading for NumPy, CSV, JSONL, and image folders.
- NumPy shard and Zarr activation stores.
- Layer statistics, feature statistics, and top examples.
- Activation health diagnostics.
- Run comparison with metric deltas.
- Markdown and JSON reports.
- CLI commands for layer discovery, capture, quickstart, init, scan, inspect, report, compare, doctor, and TUI launch.
- Flag-based capture for first runs without writing config files.
- Starter config generation with `spelunk init`.
- One-shot `spelunk quickstart` workflow for capture, scan, and report generation.
- Python capture helper with `spelunk.capture(...)`.
- Textual TUI shell with recent runs, overview, layers, diagnostics, inspect, compare, and report generation actions.
- Native TUI Markdown report preview, JSON summary, compare bars, and capture-planning guidance.
- Public Python API from `spelunk`.
- Runnable example smoke workflow.

### Known Limitations

- Capture requires a local Python model factory returning a `torch.nn.Module`.
- TUI inspect and compare workflows use deterministic shortcut actions instead of full input forms.
- Checkpoint file loading is not implemented yet.
- Diagnostics are limited to activation health.
- PyPI distribution name is `spelunk-ml`; the CLI and import name remain `spelunk`.
- Published to PyPI as `spelunk-ml`.
- Published Homebrew tap `sre0089/spelunk` with formula `spelunk-ml`.
