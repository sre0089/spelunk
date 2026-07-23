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

- `VISION.md`
- `ARCHITECTURE.md`
- `DOMAIN_MODEL.md`
- `CAPTURE_ARCHITECTURE.md`
- `STORAGE_FORMAT.md`
- `TUI_DESIGN.md`
- `TUI_COMPONENTS.md`
- `DESIGN_LANGUAGE.md`
- `CLI_SPEC.md`
- `TESTING_STRATEGY.md`
- `ROADMAP.md`
- `CONTRIBUTING.md`
- `DECISIONS.md`
- `PROJECT_STATE.md`
