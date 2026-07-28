# Final Build Validation

Validated for `0.1.0a2`.

## Checks

- `python -m pytest`: 100 passed
- `python -m ruff check .`: passed
- `python -m mypy`: passed
- `python -m build`: built wheel and sdist
- `python -m twine check dist/spelunk_ml-0.1.0a2*`: passed

## Artifacts

- `dist/spelunk_ml-0.1.0a2.tar.gz`
- `dist/spelunk_ml-0.1.0a2-py3-none-any.whl`

## Wheel Contents

Confirmed:

- `spelunk` package modules
- `spelunk/py.typed`
- console script metadata for `spelunk`
- MIT license metadata

## Clean Install Smoke

Installed the `spelunk-ml` wheel into `/tmp/spelunk-ml-clean-venv` and verified:

- `spelunk --version` prints `0.1.0a1`
- `spelunk doctor` reports the package importable
- `spelunk capture --help` exposes config-free capture flags
- `import spelunk` exposes `spelunk.capture`
- `pip show spelunk-ml` reports `Name: spelunk-ml`

## TestPyPI Smoke

TestPyPI upload and install were validated with temporary distribution name `spelunk-sre0089` because `spelunk` is already owned by another account on TestPyPI.

Verified after installing `spelunk-sre0089==0.1.0a1` from TestPyPI:

- `spelunk --version`
- `spelunk doctor`
- `spelunk capture --help`
- `import spelunk`

## Publish Gate

## PyPI Smoke

Published to real PyPI as `spelunk-ml==0.1.0a1`.

Installed from PyPI into `/tmp/spelunk-pypi-venv` and verified:

- `spelunk --version` prints `0.1.0a1`
- `spelunk doctor` reports the package importable
- `spelunk capture --help` exposes config-free capture flags
- `import spelunk` exposes `spelunk.capture`

## Remaining Release Work

## Homebrew Smoke

Published tap: `sre0089/homebrew-spelunk`

Validated locally:

- `brew style /tmp/homebrew-spelunk/Formula/spelunk-ml.rb`
- `brew audit --new sre0089/spelunk/spelunk-ml`
- `brew install --build-from-source sre0089/spelunk/spelunk-ml`
- `/opt/homebrew/Cellar/spelunk-ml/0.1.0a1/bin/spelunk --version`
- `/opt/homebrew/Cellar/spelunk-ml/0.1.0a1/bin/spelunk doctor`

Local validation could not link `/opt/homebrew/bin/spelunk` because an existing pip-installed `spelunk` command already owned that path. The Homebrew Cellar binary itself was verified.
