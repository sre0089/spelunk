# CLI Reference

Spelunk installs the `spelunk` command.

## Core Commands

```bash
spelunk
spelunk open RUN
spelunk doctor
```

- `spelunk`: open the project picker TUI.
- `spelunk open RUN`: open a `.spelunk` run in the TUI.
- `spelunk doctor`: print environment and package status.

## Discover Layers

```bash
spelunk layers --model-path model_factory.py --factory build_model
```

Prints PyTorch `named_modules()` paths that can be passed to capture.

## Capture

Capture directly from flags:

```bash
spelunk capture \
  --run runs/experiment.spelunk \
  --model-path model_factory.py \
  --dataset samples.npy \
  --layers encoder
```

Capture from a config:

```bash
spelunk capture spelunk.json
```

Useful options:

- `--model-path`: Python file containing the factory
- `--model-module`: importable module containing the factory
- `--factory`: factory callable name, default `build_model`
- `--dataset`: dataset file or image folder
- `--dataset-kind`: `numpy`, `csv`, `jsonl`, or `image-folder`
- `--layers`: repeatable layer selector
- `--storage-backend`: `numpy-shards` or `zarr`
- `--batch-size`: capture batch size
- `--max-samples`: optional sample limit

## Quickstart

```bash
spelunk quickstart \
  --run runs/experiment.spelunk \
  --model-path model_factory.py \
  --dataset samples.npy \
  --layers encoder
```

Runs capture, scan, report generation, and prints the TUI handoff command.

## Config Generation

```bash
spelunk init \
  --output spelunk.json \
  --run runs/experiment.spelunk \
  --model-path model_factory.py \
  --dataset samples.npy \
  --layers encoder
```

Writes a JSON capture config. Use `--force` to overwrite an existing file.

## Scan, Inspect, Report, Compare

```bash
spelunk scan RUN
spelunk scan RUN --json

spelunk inspect RUN --layer encoder --feature 0
spelunk inspect RUN --layer encoder --feature 0 --json

spelunk report RUN --format markdown
spelunk report RUN --format json

spelunk compare LEFT_RUN RIGHT_RUN
spelunk compare LEFT_RUN RIGHT_RUN --json
```
