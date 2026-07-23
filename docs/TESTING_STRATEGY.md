# Testing Strategy

Every milestone must leave the repository testable and usable.

## Test Layers

- domain unit tests
- storage manifest round-trip tests
- activation storage read/write tests
- analysis and diagnostic tests
- service integration tests
- Typer CLI tests
- Textual smoke tests
- PyTorch adapter tests with tiny models
- report golden-output tests for Markdown and JSON

## Boundary Tests

Add tests or static checks that prevent forbidden dependencies:

- domain must not import PyTorch, Textual, Typer, or Rich
- TUI must not import PyTorch
- CLI and TUI must use services for scan/capture/compare/report workflows

## Fixtures

Use small deterministic fixtures:

- tiny autoencoder
- tiny sparse autoencoder
- generic multilayer PyTorch module
- small local dataset
- prebuilt activation shards

## TUI Verification

The first TUI tests should verify:

- `spelunk` launches
- project picker renders
- command palette opens
- pane focus changes
- service errors render without crashing

Visual polish can be tested more deeply after the core interaction model stabilizes.
