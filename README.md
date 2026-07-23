# Spelunk

Spelunk is an IDE for learned representations.

Rather than visualizing tensors, Spelunk helps researchers understand what a model has learned through diagnostics, feature exploration, checkpoint comparison, activation statistics, and representation mapping.

Spelunk is terminal-native. Running `spelunk` launches an interactive application, not a log-heavy command script. The CLI, TUI, Python API, and future graphical clients all use the same application-service layer.

## Vision

Explore, diagnose, and explain neural representations.

## Long-term goals

- PyTorch-first
- Representation-agnostic (CNNs, Transformers, SAEs, CLIP, Diffusion)
- Local-first
- Polished terminal application
- CLI + Python API + future desktop/web clients
- PyPI package
- Homebrew distribution

## Initial Scope

The first implementation targets:

- autoencoders
- sparse autoencoders
- generic PyTorch modules
- local datasets owned and loaded by Spelunk
- Markdown and JSON reports
- local storage with streamable activation arrays

## Documentation

The authoritative planning documents are:

- `docs/VISION.md`
- `docs/ARCHITECTURE.md`
- `docs/DOMAIN_MODEL.md`
- `docs/CAPTURE_ARCHITECTURE.md`
- `docs/STORAGE_FORMAT.md`
- `docs/TUI_DESIGN.md`
- `docs/TUI_COMPONENTS.md`
- `docs/DESIGN_LANGUAGE.md`
- `docs/CLI_SPEC.md`
- `docs/TESTING_STRATEGY.md`
- `docs/ROADMAP.md`
- `docs/CONTRIBUTING.md`
- `docs/DECISIONS.md`

## Development

Spelunk targets Python 3.11+.

Install locally once dependencies are available:

```bash
python -m pip install -e ".[dev,tui,arrays]"
```

PyTorch support is optional:

```bash
python -m pip install -e ".[pytorch]"
```

Run checks:

```bash
pytest
ruff check .
mypy
```
