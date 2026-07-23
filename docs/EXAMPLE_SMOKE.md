# Example Smoke Workflow

This workflow exercises the current pre-release path end to end.

Generate the example dataset:

```bash
python examples/generate_samples.py
```

Capture activations:

```bash
spelunk capture examples/capture.json
```

Scan the run:

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

Compare against a second run:

```bash
cp examples/capture.json examples/capture-2.json
python - <<'PY'
from pathlib import Path
path = Path("examples/capture-2.json")
text = path.read_text().replace(
    "../runs/tiny-autoencoder.spelunk",
    "../runs/tiny-autoencoder-2.spelunk",
)
path.write_text(text)
PY
spelunk capture examples/capture-2.json
spelunk compare runs/tiny-autoencoder.spelunk runs/tiny-autoencoder-2.spelunk
```

Open the TUI:

```bash
spelunk open runs/tiny-autoencoder.spelunk
```
