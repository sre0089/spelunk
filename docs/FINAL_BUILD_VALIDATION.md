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

## Publish Gate

No TestPyPI or PyPI upload has been performed. Publishing requires explicit owner approval and credentials.
