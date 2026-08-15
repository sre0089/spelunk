# Architecture

Spelunk is local-first. The CLI, TUI, and Python API all use the same service layer, so the backend can be tested without opening the terminal UI.

## Main Packages

```text
src/spelunk/
  cli/           Typer command line interface
  tui/           Textual terminal interface
  api/           public Python helpers
  services/      scan, capture, compare, report, and inspect workflows
  capture/       dataset loading and capture pipeline objects
  adapters/      framework-specific model integration, currently PyTorch
  storage/       local manifests and activation persistence
  analysis/      statistics over captured activations
  diagnostics/   activation health checks
  domain/        typed data objects shared across the project
  config/        capture configs and recent-run history
```

## Dependency Shape

```text
CLI / TUI / Python API
    -> services
        -> capture / analysis / diagnostics / storage
            -> domain

adapters/pytorch
    -> capture interfaces and domain descriptions
```

The important rule is that UI code should not own analysis logic. For example, the TUI asks a `Session` to scan a run and then renders the returned `ScanResult`; it does not read activation shards or calculate diagnostics itself.

## Boundaries Worth Keeping

- `domain` should stay free of Typer, Textual, Rich, PyTorch, and storage implementations.
- `diagnostics` and `analysis` should not depend on CLI or TUI code.
- PyTorch-specific code should stay under `adapters/pytorch` or the capture boundary.
- CLI and TUI commands should call services rather than duplicating workflow logic.

## Run Data

A capture writes a local `.spelunk` directory containing metadata, activation shards, diagnostics, statistics, and generated reports. See [Storage Format](STORAGE_FORMAT.md) for the on-disk layout.
