# GitHub Release Notes

## v0.1.0a2

Spelunk `0.1.0a2` is a polish and hardening alpha focused on making the TUI and capture workflow feel less like a prototype.

## Install

```bash
python -m pip install spelunk-ml==0.1.0a2
```

Or with Homebrew after the tap formula refresh:

```bash
brew install sre0089/spelunk/spelunk-ml
```

The package name is `spelunk-ml`. The command and Python import are both `spelunk`.

## Highlights

- TUI inspect and compare shortcuts now open native selection prompts.
- Capture supports PyTorch checkpoint loading through `--checkpoint-path`.
- Capture configs support `model.checkpoint_path`.
- Activation health diagnostics now report feature-level dead activations.
- Diagnostics docs explain evidence fields and severity levels.
- Public-channel, TUI, and build-validation docs were refreshed for release hardening.

## Validation

- `python -m pytest`: 100 passed
- `python -m ruff check .`: passed
- `python -m mypy`: passed
- `python -m build`: built wheel and sdist
- `python -m twine check dist/spelunk_ml-0.1.0a2*`: passed

## Notes

- PyPI upload requires maintainer credentials and should use the already-built `dist/spelunk_ml-0.1.0a2*` artifacts.
- Homebrew formula refresh should happen after PyPI exposes the exact source URL for `spelunk_ml-0.1.0a2.tar.gz`.

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
