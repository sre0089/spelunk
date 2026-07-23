# Contributing

Spelunk is planned as a long-term software product, not a notebook or demo.

## Engineering Rules

- Keep domain and analysis code independent from UI and framework adapters.
- Prefer typed domain objects over dictionaries.
- Keep PyTorch-specific code under `spelunk/adapters/pytorch/` and the capture boundary.
- Keep CLI and TUI logic thin.
- Use application services for product workflows.
- Every milestone must include tests and documentation.
- Coordinate remote and release changes with the project owner.

## Quality Bar

Before a change is complete:

- tests pass
- types pass where configured
- docs reflect changed behavior
- examples still work
- no unrelated refactors are included

## Documentation

Record meaningful architecture decisions in `DECISIONS.md`. Record unresolved choices instead of silently choosing arbitrary defaults.
