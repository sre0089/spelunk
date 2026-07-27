# Final Build Validation

Validated for `0.1.0a1`.

## Checks

- `python -m pytest`: 97 passed
- `python -m ruff check .`: passed
- `python -m mypy`: passed
- `python -m build`: built wheel and sdist
- `python -m twine check dist/spelunk-0.1.0a1*`: passed

## Artifacts

- `dist/spelunk-0.1.0a1.tar.gz`
- `dist/spelunk-0.1.0a1-py3-none-any.whl`

## Wheel Contents

Confirmed:

- `spelunk` package modules
- `spelunk/py.typed`
- console script metadata for `spelunk`
- MIT license metadata

## Clean Install Smoke

Installed the wheel into `/tmp/spelunk-m48-clean-venv` and verified:

- `spelunk --version` prints `0.1.0a1`
- `spelunk doctor` reports the package importable
- `spelunk capture --help` exposes config-free capture flags
- `import spelunk` exposes `spelunk.capture`

## TestPyPI Smoke

TestPyPI upload and install were validated with temporary distribution name `spelunk-sre0089` because `spelunk` is already owned by another account on TestPyPI.

Verified after installing `spelunk-sre0089==0.1.0a1` from TestPyPI:

- `spelunk --version`
- `spelunk doctor`
- `spelunk capture --help`
- `import spelunk`

## Publish Gate

No real PyPI upload has been performed. Publishing requires explicit owner approval and credentials.
