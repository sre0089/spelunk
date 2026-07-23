# TUI_DESIGN.md

# Spelunk Terminal Experience

## Core Philosophy

Spelunk is NOT a command line utility.

Spelunk is a terminal-native application.

Users should feel like they have launched a scientific instrument dedicated to exploring learned representations.

The experience should resemble:
- lazygit
- k9s
- yazi
- btop
- Claude Code
- Macroscope

rather than a traditional CLI.

---

## Product Identity

A cave is dark, hidden, and must be explored deliberately.

A neural network's representation space shares these properties.

The interface should reinforce this metaphor through language, layout, motion, and subtle atmosphere.

Never become gimmicky.

The goal is premium engineering software.

---

# Presentation Architecture

```text
Typer CLI      Textual TUI      Future clients
    \             |             /
          Application services
                  |
          Spelunk backend
```

The TUI is a flagship client, not the backend. It receives typed service objects and progress events.

Why these tools:

Typer
- modern CLI
- autocomplete
- excellent command hierarchy

Textual
- modern TUI framework
- layouts
- keyboard navigation
- animations
- reactive widgets
- CSS styling
- panels
- trees
- tables

Rich
- markdown
- syntax highlighting
- trees
- progress bars
- tracebacks
- beautiful logging

Avoid:
- curses
- npyscreen
- urwid
- prompt-toolkit as the primary UI

---

# User Experience Principles

Every screen answers ONE question.

Prefer:

Diagnosis
↓
Explanation
↓
Evidence
↓
Statistics

Never overwhelm users with charts.

Whitespace is a feature.

Color has semantic meaning only.

Animations communicate state changes.

Keyboard-first.

Mouse-friendly.

---

# Application Flow

spelunk

↓

Project picker

↓

Run selection or capture setup

↓

Representation summary

↓

Interactive navigation

↓

Deep investigation

No scrolling logs.

Everything updates in-place.

---

# Navigation

Arrow keys move selection.

Enter opens.

Esc goes back.

Tab cycles panes.

Ctrl+P opens command palette.

/ starts search.

? opens shortcuts.

q quits.

---

# Layout

Persistent layout:

Header

Breadcrumbs

Left navigation

Center content

Right details

Bottom status bar

Status bar includes:

Model
GPU
Memory
Capture status
Layer
Feature
Keyboard shortcuts

The status bar must consume typed state such as `RunSummary`, `CaptureProgress`, and selected IDs. It must not inspect storage files directly.

---

# Modes

Explorer Mode
- browse layers/features

Scan Mode
- summarize model health

Compare Mode
- compare checkpoints

Explain Mode
- explain a feature

Report Mode
- generate reports

Project Mode
- choose recent projects and runs
- create a new local run

---

# Animations

Subtle only.

Examples:

- loading spinner
- torch flicker
- rotating crystal
- compass
- progress transitions
- panel fade
- smooth selection changes

Never distract the user.

---

# ASCII Art

ASCII is decorative only.

Startup logo.

Idle watermark.

Loading illustrations.

Small cave motifs.

No large animated banners during normal work.

---

# Command Palette

Ctrl+P

Everything searchable:

commands
layers
features
diagnostics
reports
settings

## Data Contract

TUI screens consume:

- `RunSummary`
- `LayerSummary`
- `FeatureSummary`
- `DiagnosticResult`
- `RunComparison`
- `CaptureProgress`
- `Report`

TUI screens do not consume arbitrary dictionaries as their primary data model.

---

# Themes

Support eventually:

Spelunk Dark
Spelunk Cave
Tokyo Night
Gruvbox
Catppuccin
Nord
Monokai

Never hardcode colors.

---

# Milestone Recommendation

M0 Architecture

M1 Repository

M2 TUI shell

M3 Navigation

M4 Layout

M5 Animation system

M6 Capture backend

M7 Diagnostics

M8 Dashboard

M9 Reports

---

# Engineering Rules

Every screen should feel intentional.

Every animation should communicate state.

Every keyboard shortcut should reduce friction.

The terminal should feel alive without becoming noisy.

The user should forget they are "using a CLI."

Instead, they should feel like they are operating an instrument.
