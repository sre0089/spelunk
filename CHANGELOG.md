# Changelog

## 0.1.0a1

First pre-alpha release candidate.

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
- CLI commands for capture, scan, inspect, report, compare, doctor, and TUI launch.
- Textual TUI shell with recent runs, overview, layers, diagnostics, inspect, compare, and report generation actions.
- Public Python API from `spelunk`.
- Runnable example smoke workflow.

### Known Limitations

- Capture requires a local Python model factory returning a `torch.nn.Module`.
- TUI inspect and compare workflows use deterministic shortcut actions instead of full input forms.
- Checkpoint file loading is not implemented yet.
- Diagnostics are limited to activation health.
- No PyPI or Homebrew publish has been performed yet.
