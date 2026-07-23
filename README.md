# Spelunk

Spelunk is a terminal-native toolkit for inspecting learned representations. It captures PyTorch activations, stores them locally, computes layer and feature statistics, runs diagnostics, compares runs, and exports Markdown or JSON reports.

The current release target is a local-first pre-alpha for researchers who are comfortable using a Python model factory and CLI workflow.

## Install

From a checkout:

```bash
python -m pip install -e ".[dev,arrays,datasets,tui]"
```

Add PyTorch support when you want to capture activations:

```bash
python -m pip install -e ".[pytorch]"
```

Run checks:

```bash
python -m pytest
python -m ruff check .
python -m mypy
```

## Quickstart

Start from the example config:

```bash
spelunk capture examples/capture.json
```

Scan the captured run:

```bash
spelunk scan runs/tiny-autoencoder.spelunk
spelunk scan runs/tiny-autoencoder.spelunk --json
```

Inspect one feature:

```bash
spelunk inspect runs/tiny-autoencoder.spelunk --layer encoder --feature 0
spelunk inspect runs/tiny-autoencoder.spelunk --layer encoder --feature 0 --json
```

Generate reports:

```bash
spelunk report runs/tiny-autoencoder.spelunk --format markdown
spelunk report runs/tiny-autoencoder.spelunk --format json
```

Compare two runs:

```bash
spelunk compare runs/baseline.spelunk runs/experiment.spelunk
spelunk compare runs/baseline.spelunk runs/experiment.spelunk --json
```

Open the TUI:

```bash
spelunk
spelunk open runs/tiny-autoencoder.spelunk
```

## Capture Configs

Capture configs are JSON or TOML files. See:

- `examples/capture.json`
- `examples/capture.toml`
- `examples/model_factory.py`
- `docs/CAPTURE_CONFIG.md`
- `docs/EXAMPLE_SMOKE.md`

The model factory must be callable with no arguments and return a `torch.nn.Module`. Layer names in the capture config are PyTorch `named_modules()` paths.

## Python API

```python
from spelunk import Session

session = Session.open("runs/tiny-autoencoder.spelunk")
scan = session.scan()
feature = session.inspect_feature(layer_id="encoder", feature_id="0")
report = session.report(format="markdown")
```

See `docs/PYTHON_API.md`.

## What Works Today

- JSON and TOML capture configs
- Spelunk-owned dataset loading for NumPy, CSV, JSONL, and image folders
- PyTorch activation capture through selected forward hooks
- NumPy shard and Zarr activation stores
- layer statistics
- feature statistics and top examples
- activation health diagnostics
- run comparison
- Markdown and JSON reports
- Textual TUI shell with run overview, layers, diagnostics, reports, and report generation

## Current Limitations

- default `spelunk` project picker is still early
- TUI compare and feature-inspection workflows are not implemented yet
- capture requires a local PyTorch model factory
- model loading does not handle checkpoint files directly yet
- no packaged PyPI release has been cut yet
- diagnostics are intentionally limited to activation health for now

## Documentation

- `docs/VISION.md`
- `docs/ARCHITECTURE.md`
- `docs/DOMAIN_MODEL.md`
- `docs/PYTHON_API.md`
- `docs/CAPTURE_ARCHITECTURE.md`
- `docs/CAPTURE_CONFIG.md`
- `docs/EXAMPLE_SMOKE.md`
- `docs/STORAGE_FORMAT.md`
- `docs/TUI_DESIGN.md`
- `docs/TUI_COMPONENTS.md`
- `docs/DESIGN_LANGUAGE.md`
- `docs/CLI_SPEC.md`
- `docs/TESTING_STRATEGY.md`
- `docs/ROADMAP.md`
- `docs/RELEASE.md`
- `docs/CLEAN_INSTALL.md`
- `docs/CONTRIBUTING.md`
- `docs/DECISIONS.md`
