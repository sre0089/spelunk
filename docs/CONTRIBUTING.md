# Contributing

Spelunk is still early, but contributions should keep the project easy to run, test, and understand.

## Setup

```bash
python -m pip install -e ".[dev,pytorch,arrays,datasets,tui]"
```

## Checks

Run these before opening a pull request:

```bash
python -m pytest
python -m ruff check .
python -m mypy
```

For docs-only changes, at least run the focused tests that touch examples or imports:

```bash
python -m pytest tests/test_examples.py tests/test_package_import.py
```

## Code Guidelines

- Keep CLI and TUI code thin; put workflow logic in `services/`.
- Keep PyTorch-specific behavior in `adapters/pytorch/` or capture code.
- Keep domain objects independent from UI and framework libraries.
- Prefer small tests with temporary data over tests that depend on local files.
- Update docs when command behavior, output, or public APIs change.

## Public Docs

Write docs for someone seeing the repository for the first time. Prefer short examples, direct explanations, and real commands over design notes or planning language.
