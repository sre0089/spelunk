# PyPI Release Prep

This project is prepared for a `0.1.0a1` pre-alpha release, but publishing must be explicitly approved.

## Build

```bash
python -m build
```

Expected artifacts:

- `dist/spelunk-0.1.0a1.tar.gz`
- `dist/spelunk-0.1.0a1-py3-none-any.whl`

## Metadata Check

```bash
python -m twine check dist/spelunk-0.1.0a1*
```

## TestPyPI

Use TestPyPI before the real upload:

```bash
python -m twine upload --repository testpypi dist/spelunk-0.1.0a1*
```

Verify install:

```bash
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ spelunk==0.1.0a1
spelunk --version
spelunk doctor
```

## PyPI

Publish only after TestPyPI verification:

```bash
python -m twine upload dist/spelunk-0.1.0a1*
```

Verify install:

```bash
python -m pip install spelunk==0.1.0a1
spelunk --version
spelunk doctor
```

## Release Notes

Use `CHANGELOG.md` section `0.1.0a1` as the release notes source.

## Do Not Publish Until

- owner approves the publish
- `pytest`, `ruff`, `mypy`, `build`, and `twine check` pass
- clean install verification is current
- GitHub repo state is pushed and clean
