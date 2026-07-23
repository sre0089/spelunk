# Capture Configs

Capture configs describe one local activation capture run. Spelunk owns dataset loading and uses the configured model factory to build a PyTorch model.

## Supported Formats

Spelunk accepts JSON and TOML:

```bash
spelunk capture examples/capture.json
spelunk capture examples/capture.toml
```

## Required Fields

Top-level fields:

- `run`: output run directory, usually ending in `.spelunk`
- `storage_backend`: `numpy-shards` or `zarr`
- `model`: model identity and factory loading settings
- `dataset`: dataset identity and source
- `capture`: selected layers and batching settings

Model fields:

- `id`: stable model identifier
- `name`: display name
- `framework`: currently `pytorch`
- `factory`: callable name returning a `torch.nn.Module`
- `path`: Python file containing the factory
- `module`: importable Python module containing the factory

Use either `model.path` or `model.module`.

Dataset fields:

- `kind`: `numpy`, `csv`, `jsonl`, or `image-folder`
- `source`: local path to the dataset

Capture fields:

- `layers`: PyTorch module paths to hook, such as `encoder` or `blocks.0.mlp`
- `checkpoint_id`: stable checkpoint identifier
- `checkpoint_label`: display label
- `batch_size`: positive integer
- `max_samples`: optional positive integer

## Model Factory Contract

The factory must be callable with no arguments and return a `torch.nn.Module`.

```python
import torch


def build_model() -> torch.nn.Module:
    return torch.nn.Sequential(...)
```

Layer names come from `model.named_modules()`. If `layers = ["encoder"]`, the returned model must have a named module at `encoder`.

## Workflow

Capture activations:

```bash
spelunk capture examples/capture.json
```

Scan a run:

```bash
spelunk scan runs/tiny-autoencoder.spelunk
spelunk scan runs/tiny-autoencoder.spelunk --json
```

Inspect a feature:

```bash
spelunk inspect runs/tiny-autoencoder.spelunk --layer encoder --feature 0
```

Generate reports:

```bash
spelunk report runs/tiny-autoencoder.spelunk --format markdown
spelunk report runs/tiny-autoencoder.spelunk --format json
```

Compare runs:

```bash
spelunk compare runs/baseline.spelunk runs/experiment.spelunk
spelunk compare runs/baseline.spelunk runs/experiment.spelunk --json
```
