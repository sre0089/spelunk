# Release Checklist

This checklist is for the first pre-alpha release.

## Version

- Set `pyproject.toml` project version.
- Set `src/spelunk/_version.py` to the same value.
- Use `0.1.0a1` for the first installable alpha.

## Checks

Run:

```bash
python -m pytest
python -m ruff check .
python -m mypy
python -m build
```

## Package Contents

Confirm the wheel contains:

- `spelunk` package modules
- `spelunk/py.typed`
- console script metadata for `spelunk`

Confirm public docs and examples are tracked in git:

- `README.md`
- `docs/`
- `examples/`

## Smoke Test

From a clean virtual environment:

```bash
python -m pip install dist/spelunk-*.whl
spelunk --version
spelunk doctor
```

Optional extras:

```bash
python -m pip install "spelunk[pytorch,arrays,datasets]"
```

## Release Notes

Include:

- supported workflows
- known limitations
- Python version support
- optional dependency groups
