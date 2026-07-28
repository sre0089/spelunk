# Spelunk Documentation

Start here if you are using Spelunk for the first time.

## User Guides

- [Getting Started](GETTING_STARTED.md): install, capture, report, and open the TUI.
- [Install](INSTALL.md): pip, Homebrew, and source installs.
- [CLI Reference](CLI_REFERENCE.md): command-by-command usage.
- [Capture Configs](CAPTURE_CONFIG.md): JSON/TOML config format for reproducible runs.
- [Diagnostics](DIAGNOSTICS.md): activation health warnings and metrics.
- [Python API](PYTHON_API.md): use Spelunk from notebooks and scripts.
- [Storage Format](STORAGE_FORMAT.md): what a `.spelunk` run contains.
- [Homebrew Release](HOMEBREW_RELEASE.md): Homebrew install and validation notes.
- [GitHub Release Notes](GITHUB_RELEASE.md): release notes for the current alpha.

## Examples

- [Example Smoke Workflow](EXAMPLE_SMOKE.md): runnable local workflow using `examples/`.
- [`examples/README.md`](../examples/README.md): quick map of bundled example files.
- [`examples/model_factory.py`](../examples/model_factory.py): tiny PyTorch model factory.
- [`examples/generate_samples.py`](../examples/generate_samples.py): tiny NumPy dataset generator.
- [`examples/capture.json`](../examples/capture.json): JSON capture config.
- [`examples/capture.toml`](../examples/capture.toml): TOML capture config.

## Design And Architecture

- [Architecture](ARCHITECTURE.md)
- [Domain Model](DOMAIN_MODEL.md)
- [Capture Architecture](CAPTURE_ARCHITECTURE.md)
- [TUI Design](TUI_DESIGN.md)
- [TUI Components](TUI_COMPONENTS.md)
- [Design Principles](DESIGN_PRINCIPLES.md)
- [Design Language](DESIGN_LANGUAGE.md)
- [Decisions](DECISIONS.md)

## Maintainer Notes

These files are useful for release work and project planning, but most users do not need them on day one.

- [Release Checklist](RELEASE.md)
- [PyPI Release Prep](PYPI_RELEASE.md)
- [Clean Install Verification](CLEAN_INSTALL.md)
- [Public Channel Smoke Test](PUBLIC_CHANNEL_SMOKE.md)
- [Final Build Validation](FINAL_BUILD_VALIDATION.md)
- [Bigger-Model Release Audit](BIGGER_MODEL_RELEASE_AUDIT.md)
- [TUI Smoke Test](TUI_SMOKE.md)
- [Testing Strategy](TESTING_STRATEGY.md)
- [Roadmap](ROADMAP.md)
- [Milestones](MILESTONES.md)
- [Workflow Friction Audit](WORKFLOW_FRICTION_AUDIT.md)
- [Product Spec](PRODUCT_SPEC.md)
- [Vision](VISION.md)

## Contributing

See [Contributing](CONTRIBUTING.md).
