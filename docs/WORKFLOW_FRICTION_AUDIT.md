# Workflow Friction Audit

Spelunk's first-use workflow should give engineers useful results before they need to learn the full capture config schema.

## Current Required Steps

1. Write a Python model factory.
2. Prepare a supported dataset file or folder.
3. Write JSON or TOML with run, model, dataset, storage, checkpoint, and capture fields.
4. Manually identify valid layer names.
5. Run capture, scan, report, and TUI commands separately.

## Friction To Remove

- Config files are too early in the workflow.
- Layer names require guessing or reading model code.
- Capture config validation errors are useful but schema-oriented.
- The quickest useful path still requires several commands.
- The TUI can consume runs well, but it cannot yet help create capture inputs.

## Release Workflow Target

Config files remain the reproducible path, but users should also be able to:

```bash
spelunk layers --model-path model_factory.py --factory build_model

spelunk capture \
  --run runs/experiment.spelunk \
  --model-path model_factory.py \
  --factory build_model \
  --dataset samples.npy \
  --layers encoder

spelunk quickstart \
  --run runs/experiment.spelunk \
  --model-path model_factory.py \
  --factory build_model \
  --dataset samples.npy \
  --layers encoder
```

The first release should support discovery, flag-based capture, quickstart, and a starter config generator.
