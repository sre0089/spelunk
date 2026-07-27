# Spelunk Examples

This directory contains a tiny end-to-end workflow:

- `generate_samples.py`: writes `samples.npy`
- `model_factory.py`: returns a small PyTorch autoencoder
- `capture.json`: JSON capture config
- `capture.toml`: TOML capture config

Run the example from the repository root:

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

For reproducible config-driven capture:

```bash
spelunk capture examples/capture.json
```
