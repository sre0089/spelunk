# Public Channel Smoke Test

Validated after publishing `spelunk-ml==0.1.0a1`.

## PyPI

Fresh venv:

```bash
python -m venv /tmp/spelunk-public-smoke/pypi-venv
/tmp/spelunk-public-smoke/pypi-venv/bin/python -m pip install "spelunk-ml[pytorch,arrays,datasets]==0.1.0a1"
```

Verified:

```bash
spelunk --version
spelunk layers --model-path model_factory.py --factory build_model
spelunk quickstart --run runs/pypi-smoke.spelunk --model-path model_factory.py --factory build_model --dataset samples.npy --layers encoder --layers bottleneck --batch-size 2
```

Result:

- version: `0.1.0a1`
- layer discovery printed `encoder`, `bottleneck`, and `decoder`
- quickstart captured 4 samples
- quickstart generated Markdown and JSON reports

## Homebrew

Validated formula:

```bash
brew info sre0089/spelunk/spelunk-ml
/opt/homebrew/Cellar/spelunk-ml/0.1.0a1/bin/spelunk --version
/opt/homebrew/Cellar/spelunk-ml/0.1.0a1/bin/spelunk doctor
```

Result:

- formula version: `0.1.0a1`
- `spelunk --version`: `0.1.0a1`
- `spelunk doctor`: package importable

Local caveat: this machine already has a pip-installed `/opt/homebrew/bin/spelunk`, so Homebrew cannot link its own `spelunk` executable without `brew link --overwrite spelunk-ml`. Fresh Homebrew users should not hit that conflict.
