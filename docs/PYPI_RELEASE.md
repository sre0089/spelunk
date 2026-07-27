# PyPI Release Prep

Spelunk was published to PyPI as `spelunk-ml==0.1.0a1`.

## Build

```bash
python -m build
```

Expected artifacts:

- `dist/spelunk_ml-0.1.0a1.tar.gz`
- `dist/spelunk_ml-0.1.0a1-py3-none-any.whl`

## Metadata Check

```bash
python -m twine check dist/spelunk_ml-0.1.0a1*
```

## TestPyPI

The `spelunk` name is already owned by another account on TestPyPI. TestPyPI validation used temporary distribution name `spelunk-sre0089`. The real PyPI distribution name is `spelunk-ml`; the CLI and import name remain `spelunk`.

Use TestPyPI before the real upload:

```bash
python -m twine upload --repository testpypi dist/spelunk_ml-0.1.0a1*
```

Verify install:

```bash
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ spelunk-ml==0.1.0a1
spelunk --version
spelunk doctor
```

For the validated temporary TestPyPI name:

```bash
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ spelunk-sre0089==0.1.0a1
```

## PyPI

Published with:

```bash
python -m twine upload dist/spelunk_ml-0.1.0a1*
```

Verify install:

```bash
python -m pip install spelunk-ml==0.1.0a1
spelunk --version
spelunk doctor
```

## Release Notes

Use `CHANGELOG.md` section `0.1.0a1` as the release notes source.

## Publish Requirements

- owner approves the publish
- `pytest`, `ruff`, `mypy`, `build`, and `twine check` pass
- clean install verification is current
- GitHub repo state is pushed and clean
