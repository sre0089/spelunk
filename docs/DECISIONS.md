# Decisions

## Accepted

### Local-first architecture

Spelunk runs locally by default. Early milestones must not require distributed systems, hosted storage, background workers, or a web service.

### Shared application-service layer

The CLI, TUI, Python API, and future clients all use the same application services.

### Terminal-native product

Running `spelunk` opens a polished terminal application with a project picker.

### Initial model scope

The first supported targets are autoencoders, sparse autoencoders, and generic PyTorch modules.

### Dataset ownership

Spelunk owns dataset loading for capture workflows.

### Storage formats

Spelunk supports both NumPy shard files and Zarr chunked array storage behind one storage interface.

### Initial dataset formats

The first dataset loaders should cover local NumPy arrays, CSV files, JSONL records, and image folders. Additional dataset integrations should wait until these paths are stable.

### First diagnostic

The first diagnostic is an activation health scan. It should detect inactive features, sparsity extremes, saturation, and strong activation outliers.

### Report formats

Reports export to Markdown and JSON.

### API scope

An API layer remains in scope. Early work starts with an in-process Python API; REST/RPC can be added after service contracts stabilize.

### Pre-release compatibility

Before `0.1.0`, Python APIs may change without backward compatibility guarantees. Storage schemas must still be versioned, and incompatible changes must be recorded in this file or migration notes.

## Architecture Decision Records

### ADR-001: Keep domain independent from UI and frameworks

Decision: domain objects must not depend on Textual, Typer, Rich, or PyTorch.

Reason: Spelunk must support multiple clients and future model frameworks.

### ADR-002: Treat TUI as a flagship client

Decision: the TUI receives typed service objects and does not own backend logic.

Reason: terminal polish matters, but analysis correctness must remain independent.

### ADR-003: Stream activations

Decision: activation capture and analysis operate on batches and shards.

Reason: representation datasets can exceed memory.

## Open

No open architecture decisions are currently blocking M2.
