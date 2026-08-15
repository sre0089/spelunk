# Spelunk

Spelunk is a terminal tool for inspecting what PyTorch models are doing internally.
It captures activations from selected layers, stores them in a local `.spelunk` run, runs a few sanity checks, and lets you inspect the results from the CLI or a TUI.

It is built for people who train or debug neural networks and want a faster path from “the model ran” to “I can see what changed inside it.”

## Install

The package name is `spelunk-ml`. The command and Python import are both `spelunk`.

```bash
python -m pip install "spelunk-ml[pytorch,arrays,datasets]"
```

Homebrew is also supported:

```bash
brew install sre0089/spelunk/spelunk-ml
```

Check the install:

```bash
spelunk --version
spelunk doctor
```

## Quickstart

Generate the bundled tiny dataset:

```bash
python examples/generate_samples.py
```

List captureable layers from the example model:

```bash
spelunk layers --model-path examples/model_factory.py --factory build_model
```

Capture activations, scan the run, and write reports:

```bash
spelunk quickstart \
  --run runs/tiny-autoencoder.spelunk \
  --model-path examples/model_factory.py \
  --factory build_model \
  --dataset examples/samples.npy \
  --layers encoder
```

Open the TUI:

```bash
spelunk open runs/tiny-autoencoder.spelunk
```

Useful TUI shortcuts:

```text
i   inspect a feature
c   compare with another recent run
r   generate and preview reports
?   show shortcuts
q   quit
```

## Use Your Own Model

Spelunk loads models through a small Python factory function:

```python
# model_factory.py
import torch


def build_model() -> torch.nn.Module:
    return torch.nn.Sequential(...)
```

Then run:

```bash
spelunk quickstart \
  --run runs/experiment.spelunk \
  --model-path model_factory.py \
  --factory build_model \
  --dataset samples.npy \
  --layers encoder \
  --layers bottleneck
```

If your weights are saved separately, add:

```bash
--checkpoint-path weights.pt
```

## What Spelunk Shows

- layer statistics such as activation mean, standard deviation, min, and max
- activation health diagnostics for sparsity, dead features, saturation, and outliers
- feature-level statistics and top examples
- Markdown and JSON reports
- metric deltas between two captured runs
- a local TUI for browsing runs, diagnostics, reports, and comparisons

## Current Scope

Spelunk is an early local-first tool. It currently focuses on PyTorch models, local datasets, local run folders, and terminal workflows. It does not require a server, hosted storage, or notebook integration.

The main rough edge is that you need to provide a Python model factory and choose the layers you want to capture. Use `spelunk layers` first if you are unsure what the layer names are.

## Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [Install](docs/INSTALL.md)
- [CLI Reference](docs/CLI_REFERENCE.md)
- [Capture Configs](docs/CAPTURE_CONFIG.md)
- [Diagnostics](docs/DIAGNOSTICS.md)
- [Python API](docs/PYTHON_API.md)
- [Storage Format](docs/STORAGE_FORMAT.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Support](SUPPORT.md)
- [Security](SECURITY.md)

## Development

```bash
python -m pip install -e ".[dev,pytorch,arrays,datasets,tui]"
python -m pytest
python -m ruff check .
python -m mypy
```
