# GitHub Release Notes

## v0.1.0a1

Spelunk is now available as a pre-alpha release for local PyTorch activation capture and representation inspection.

## Install

```bash
python -m pip install spelunk-ml
```

Or with Homebrew:

```bash
brew install sre0089/spelunk/spelunk-ml
```

The package name is `spelunk-ml`. The command and Python import are both `spelunk`.

## Quickstart

```bash
python examples/generate_samples.py

spelunk quickstart \
  --run runs/tiny-autoencoder.spelunk \
  --model-path examples/model_factory.py \
  --factory build_model \
  --dataset examples/samples.npy \
  --layers encoder

spelunk open runs/tiny-autoencoder.spelunk
```

## Highlights

- PyTorch activation capture from selected layers.
- Layer discovery with `spelunk layers`.
- Config-free capture with CLI flags.
- One-shot `spelunk quickstart`.
- JSON/TOML capture configs for reproducible workflows.
- NumPy shard and Zarr storage backends.
- Layer statistics, feature statistics, and top examples.
- Activation health diagnostics.
- Run comparison with metric deltas.
- Markdown and JSON report generation.
- Textual TUI with overview, layers, diagnostics, inspect, compare, and reports.
- Python API helper: `spelunk.capture(...)`.

## Known Limitations

- Capture expects a local Python model factory returning a `torch.nn.Module`.
- Checkpoint file loading is not included in this release.
- TUI inspect and compare flows are still shortcut-driven.
- Diagnostics focus on activation health.

## Links

- PyPI: `spelunk-ml`
- Homebrew tap: `sre0089/spelunk`
- Docs: `docs/README.md`
