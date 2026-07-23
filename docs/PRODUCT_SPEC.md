# Product Specification

## Problem
Researchers repeatedly build ad-hoc notebooks to inspect learned representations.

## Solution
Provide a unified toolkit for:
- Feature exploration
- Activation statistics
- Representation diagnostics
- Checkpoint comparison
- Concept discovery (future)
- Report generation

## Guiding Principle
The product should answer questions, not merely display metrics.

Diagnosis -> Explanation -> Evidence -> Raw statistics.

## Product Shape

Spelunk has four product surfaces:

- terminal-native TUI launched by `spelunk`
- scriptable CLI commands
- public Python API
- future graphical/API clients

All surfaces must use the same application-service layer.

## Initial Product Commitments

- `spelunk` opens a project picker.
- Spelunk owns dataset loading for capture workflows.
- The first supported model classes are autoencoders, sparse autoencoders, and generic PyTorch modules.
- Reports export to Markdown and JSON.
- Local-first storage is required.
- REST/API remains in scope, but early milestones must not require a server.
