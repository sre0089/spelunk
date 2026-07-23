# Architecture

Spelunk is a local-first, terminal-native IDE for learned representations.

The architecture separates model integration, activation capture, storage, statistics, diagnostics, application services, CLI, TUI, and future API clients. The backend must remain usable without the TUI.

## Dependency Direction

```text
CLI / TUI / future clients
    -> application services
        -> diagnostics / analysis / capture / storage
            -> domain models

capture
    -> framework adapter interfaces

adapters/pytorch
    -> capture interfaces + domain descriptions
```

The TUI must not call PyTorch hooks, read raw activation files directly, or calculate diagnostics. It consumes typed objects such as `DiagnosticResult`, `FeatureSummary`, `LayerSummary`, `RunComparison`, and `CaptureProgress`.

## Packages

```text
src/spelunk/
  domain/        Pure typed domain objects.
  services/      Application use cases shared by CLI, TUI, and API.
  capture/       Framework-neutral activation capture pipeline.
  adapters/      Framework-specific integration.
  storage/       Local manifests and activation array persistence.
  analysis/      Statistics, reducers, summaries.
  diagnostics/   Built-in diagnostic checks and registry.
  cli/           Typer command surface.
  tui/           Textual application and widgets.
  api/           Future API boundary over services.
  config/        Settings and project/user config loading.
```

## Forbidden Imports

- `domain` must not import Textual, Typer, Rich, PyTorch, or storage implementations.
- `analysis` and `diagnostics` must not depend on Textual or Typer.
- `tui` must not import `torch`.
- PyTorch-specific concepts must stay under `spelunk/adapters/pytorch/` or the capture boundary.

## Public Python API

```python
from spelunk import CapturePlan, Session

session = Session.open("runs/run-001")
scan = session.scan()
report = session.report(format="markdown")

session = Session.create("runs/run-002", model=model_ref, dataset=dataset_ref)
plan = CapturePlan(layers=("encoder.*",), dataset="mnist-sample")
capture = session.capture(plan)
```

PyTorch adapters are introduced behind the capture boundary in later milestones.

## Local API Layer

An API layer is in scope, but early milestones should expose an in-process Python API first. REST or RPC should be added only when the local product has stable service contracts.

## Repository Layout

```text
spelunk/
  pyproject.toml
  README.md
  docs/
  examples/
  src/spelunk/
  tests/
```

Every milestone must leave the repository importable, testable, documented, and usable.
