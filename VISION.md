# Vision

Spelunk is an IDE for learned representations.

It helps researchers explore, diagnose, compare, and explain what neural networks have learned. The product should feel like a scientific instrument: focused, precise, local-first, and built for repeated research work.

## Product Identity

Go spelunking inside your models.

Neural representation spaces are hidden, layered, and difficult to inspect directly. Spelunk gives researchers a controlled way to move from high-level conclusions to evidence and raw statistics without falling back to ad hoc notebooks.

## Product Surfaces

- `spelunk`: polished terminal-native TUI.
- `spelunk scan`, `spelunk capture`, `spelunk compare`: scriptable CLI commands.
- `from spelunk import Session`: public Python API.
- Future local API and graphical clients.

All surfaces share the same application services and typed domain model.

## Initial Scope

The first useful product supports:

- autoencoders
- sparse autoencoders
- generic PyTorch modules
- Spelunk-owned dataset loading
- activation capture
- local storage
- feature and layer statistics
- built-in diagnostics
- Markdown and JSON reports

## Non-Goals For Early Milestones

- distributed execution
- hosted storage
- notebook-first workflows
- generic plugin marketplace
- mandatory web server
- TUI-only backend logic
