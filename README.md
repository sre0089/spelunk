# Spelunk

Spelunk is a terminal-native tool for inspecting learned representations. It captures PyTorch activations, stores them locally, computes layer and feature statistics, runs activation health diagnostics, compares runs, and opens everything in a TUI built for fast inspection.

Install the package named `spelunk-ml`; use the command and Python import named `spelunk`.

```bash
python -m pip install spelunk-ml
```

```bash
brew install sre0089/spelunk/spelunk-ml
```

## Quickstart

Create a tiny dataset and model from the examples:

```bash
python examples/generate_samples.py
```

Discover captureable PyTorch layer names:

```bash
spelunk layers --model-path examples/model_factory.py --factory build_model
```

Run capture, scan, and report generation in one command:

```bash
spelunk quickstart \
  --run runs/tiny-autoencoder.spelunk \
  --model-path examples/model_factory.py \
  --factory build_model \
  --dataset examples/samples.npy \
  --layers encoder
```

To load trained weights before capture, add `--checkpoint-path weights.pt`.

Open the TUI:

```bash
spelunk open runs/tiny-autoencoder.spelunk
```

Useful TUI shortcuts:

```text
i   inspect a feature
c   compare with another recent run
r   generate and preview reports
?   shortcuts
q   quit
```

## What You Can Do

- Discover valid PyTorch layer selectors before capture.
- Capture activations from CLI flags, JSON/TOML configs, or Python, including saved PyTorch checkpoints.
- Store activations as NumPy shards or Zarr.
- Scan runs for layer statistics and activation health diagnostics.
- Inspect feature statistics and top examples.
- Compare runs and see metric deltas.
- Generate Markdown and JSON reports.
- Browse runs, reports, comparisons, and diagnostics in the TUI.

## Common Workflows

Capture directly from flags:

```bash
spelunk capture \
  --run runs/experiment.spelunk \
  --model-path model_factory.py \
  --checkpoint-path weights.pt \
  --dataset samples.npy \
  --layers encoder \
  --layers bottleneck
```

Create a reproducible config:

```bash
spelunk init \
  --output spelunk.json \
  --run runs/experiment.spelunk \
  --model-path model_factory.py \
  --dataset samples.npy \
  --layers encoder

spelunk capture spelunk.json
```

Inspect from the CLI:

```bash
spelunk scan runs/experiment.spelunk
spelunk inspect runs/experiment.spelunk --layer encoder --feature 0
spelunk report runs/experiment.spelunk --format markdown
```

Capture from Python:

```python
import numpy as np
import spelunk

samples = np.load("samples.npy")

result = spelunk.capture(
    model=model,
    dataset=samples,
    layers=["encoder", "bottleneck"],
    run="runs/experiment.spelunk",
)
```

## Requirements

- Python 3.11+
- PyTorch for activation capture
- NumPy for NumPy datasets and local array statistics

Install optional capture dependencies with pip when needed:

```bash
python -m pip install "spelunk-ml[pytorch,arrays,datasets]"
```

## Status

Spelunk is a pre-alpha release. It is useful for local activation capture and inspection, but some workflows are intentionally early:

- Capture currently expects a local Python model factory returning a `torch.nn.Module`.
- Checkpoint file loading is not implemented yet.
- Diagnostics currently focus on activation health.
- TUI feature selection is still shortcut-driven rather than fully form-based.

## Documentation

- [Documentation Index](docs/README.md)
- [Install](docs/INSTALL.md)
- [Getting Started](docs/GETTING_STARTED.md)
- [CLI Reference](docs/CLI_REFERENCE.md)
- [Capture Configs](docs/CAPTURE_CONFIG.md)
- [Python API](docs/PYTHON_API.md)
- [Storage Format](docs/STORAGE_FORMAT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Support](SUPPORT.md)
- [Security](SECURITY.md)

## Development

```bash
python -m pip install -e ".[dev,arrays,datasets,tui]"
python -m pytest
python -m ruff check .
python -m mypy
```
