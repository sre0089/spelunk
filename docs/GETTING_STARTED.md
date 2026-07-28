# Getting Started

This guide takes you from a model factory and dataset to a local Spelunk run.

## Install

```bash
python -m pip install "spelunk-ml[pytorch,arrays,datasets]"
```

Or install with Homebrew:

```bash
brew install sre0089/spelunk/spelunk-ml
```

## 1. Prepare A Model Factory

Spelunk loads PyTorch models through a Python function that takes no arguments and returns a `torch.nn.Module`.

```python
# model_factory.py
import torch


def build_model():
    return torch.nn.Sequential(
        torch.nn.Linear(8, 4),
        torch.nn.ReLU(),
        torch.nn.Linear(4, 8),
    )
```

For named layers, use module attributes or an `OrderedDict`.

## 2. Prepare Data

Spelunk can load:

- NumPy `.npy`
- CSV
- JSONL
- image folders

For the bundled example:

```bash
python examples/generate_samples.py
```

## 3. Discover Layers

```bash
spelunk layers --model-path examples/model_factory.py --factory build_model
```

Use the printed layer names in capture commands.

## 4. Capture And Report

```bash
spelunk quickstart \
  --run runs/tiny-autoencoder.spelunk \
  --model-path examples/model_factory.py \
  --factory build_model \
  --dataset examples/samples.npy \
  --layers encoder
```

If your factory creates the architecture but weights live in a checkpoint file, add `--checkpoint-path weights.pt`.

This captures activations, scans the run, generates Markdown and JSON reports, and prints the TUI command.

## 5. Open The TUI

```bash
spelunk open runs/tiny-autoencoder.spelunk
```

Shortcuts:

```text
i   inspect a feature
c   compare with another recent run
r   generate and preview reports
?   shortcuts
q   quit
```

## Reproducible Configs

For repeatable runs, generate a config:

```bash
spelunk init \
  --output spelunk.json \
  --run runs/experiment.spelunk \
  --model-path model_factory.py \
  --dataset samples.npy \
  --layers encoder
```

Then run it:

```bash
spelunk capture spelunk.json
```
