# CLI Specification

The CLI is scriptable access to the same application services used by the TUI.

## Commands

```text
spelunk
spelunk open RUN
spelunk scan RUN
spelunk scan RUN --json
spelunk capture CONFIG
spelunk compare RUN_A RUN_B
spelunk report RUN --format markdown
spelunk report RUN --format json
spelunk inspect RUN --layer LAYER --feature FEATURE
spelunk doctor
spelunk config show
```

## Default Command

`spelunk` opens the interactive project picker.

## Output

Human output should be concise and conclusion-first. Machine output uses JSON and typed schemas.

## Rules

- CLI commands must not duplicate service logic.
- CLI commands must not import Textual.
- CLI commands must not directly call PyTorch hooks.
- `--json` output must be stable enough for scripts.
- Errors should include actionable user messages.
