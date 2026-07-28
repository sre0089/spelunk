# Homebrew Release

Spelunk is published through the tap:

```text
https://github.com/sre0089/homebrew-spelunk
```

One-line install:

```bash
brew install sre0089/spelunk/spelunk-ml
```

Or tap first:

```bash
brew tap sre0089/spelunk
brew install spelunk-ml
```

Verify:

```bash
spelunk --version
spelunk doctor
```

The formula installs the PyPI distribution `spelunk-ml`. The command and Python import name remain `spelunk`.

For the `0.1.0a2` formula refresh, see [Homebrew 0.1.0a2 Refresh Prep](HOMEBREW_A2_REFRESH.md).

## Validation Notes

The formula was validated locally with:

```bash
brew style /tmp/homebrew-spelunk/Formula/spelunk-ml.rb
brew audit --new sre0089/spelunk/spelunk-ml
brew install --build-from-source sre0089/spelunk/spelunk-ml
```

The local install built successfully. Linking was blocked on this machine because `/opt/homebrew/bin/spelunk` already existed from a pip install; the Cellar binary was verified directly.
