# Roadmap

## M0 Documentation And Architecture

Acceptance:

- authoritative docs exist
- package boundaries are explicit
- accepted decisions are recorded
- unresolved questions are listed
- no implementation code is required

## M1 Repository Bootstrap

Acceptance:

- `pyproject.toml` exists
- `src/spelunk` package imports
- ruff, mypy, pytest are configured
- no git initialization is performed

## M2 Domain Model And Storage Manifests

Acceptance:

- typed domain objects exist
- manifest schemas exist
- schema versioning exists
- round-trip tests pass

## M3 Application Service Skeleton

Acceptance:

- `Session.open`, `Session.create`, `scan`, `capture`, `compare`, and `report` service contracts exist
- services use typed objects
- tests cover basic service flows with fixtures

## M4 CLI Skeleton

Acceptance:

- command hierarchy exists
- `spelunk` launches the TUI entrypoint placeholder
- `spelunk scan --json` calls services
- `spelunk doctor` reports environment status

## M5 TUI Shell And Project Picker

Acceptance:

- `spelunk` opens a Textual project picker
- persistent layout exists
- command palette exists
- keyboard navigation works
- TUI consumes service objects or placeholders shaped like service objects

## M6 Dataset Loading And PyTorch Model Description

Acceptance:

- Spelunk-owned dataset loading works for NumPy arrays, CSV files, JSONL records, and image folders
- PyTorch adapter describes autoencoders, sparse autoencoders, and generic modules
- no PyTorch types leak into domain objects

## M7 Activation Capture Pipeline

Acceptance:

- selected layers can be captured through PyTorch hooks
- capture emits `CaptureProgress`
- activations stream to storage
- tests use tiny deterministic models

## M8 Storage Arrays And Statistics Engine

Acceptance:

- NumPy shards and chunked arrays are supported behind one interface
- large arrays can be iterated without full-memory loading
- layer and feature summaries are computed

## M9 Built-In Diagnostics

Acceptance:

- activation health diagnostics return `DiagnosticResult`
- each diagnostic includes conclusion, explanation, evidence, and statistics
- CLI and services expose scan results

## M10 TUI Data Integration

Acceptance:

- TUI shows real run summaries
- layers and features are selectable
- diagnostics display conclusion-first
- long-running operations update in place

## M11 Checkpoint And Run Comparison

Acceptance:

- two checkpoints or runs can be compared
- CLI emits human and JSON output
- TUI compare screen displays typed `RunComparison`

## M12 Markdown And JSON Reports

Acceptance:

- report service exports Markdown
- report service exports JSON
- reports include scan conclusions, evidence, and key statistics

## M13 Local API Boundary

Acceptance:

- public Python API is documented
- service contracts are stable enough for future REST/RPC work
- no server is required

## M14 Packaging

Acceptance:

- editable install works
- console scripts work
- optional extras are defined

## M15 PyPI

Acceptance:

- package metadata is complete
- release checklist exists
- package can be built locally

## M16 Homebrew

Acceptance:

- Homebrew formula plan exists
- packaged CLI/TUI behavior is verified
