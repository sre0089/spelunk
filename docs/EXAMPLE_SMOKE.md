# Example Smoke Workflow

This workflow exercises Spelunk end to end using the files in `examples/`.

## Quickstart Path

Generate the example dataset:

```bash
python examples/generate_samples.py
```

Discover layers:

```bash
spelunk layers --model-path examples/model_factory.py --factory build_model
```

Capture, scan, and generate reports:

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

## CLI Checks

```bash
spelunk scan runs/tiny-autoencoder.spelunk
spelunk inspect runs/tiny-autoencoder.spelunk --layer encoder --feature 0
spelunk report runs/tiny-autoencoder.spelunk --format markdown
spelunk report runs/tiny-autoencoder.spelunk --format json
```

## Config Path

The examples also include JSON and TOML capture configs:

```bash
spelunk capture examples/capture.json
spelunk capture examples/capture.toml
```

Each capture config writes to its configured `run` path. The run path must not already exist.
