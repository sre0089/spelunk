# Homebrew 0.1.0a2 Refresh Prep

Prepared on 2026-07-28.

## Local Package Artifact

Built from the main repo:

```bash
/opt/homebrew/bin/python3.11 -m build
/opt/homebrew/bin/python3.11 -m twine check dist/spelunk_ml-0.1.0a2*
```

Result:

- `dist/spelunk_ml-0.1.0a2.tar.gz`: passed `twine check`
- `dist/spelunk_ml-0.1.0a2-py3-none-any.whl`: passed `twine check`

Local sdist SHA256:

```text
9d7b03adf127c6b461b0266809b239d661e0ebc3c5a6f0357d01823b7e782aa1
```

## Formula Change

After `spelunk-ml==0.1.0a2` is uploaded to PyPI, update the tap formula:

```ruby
url "<exact files.pythonhosted.org source URL for spelunk_ml-0.1.0a2.tar.gz>"
sha256 "9d7b03adf127c6b461b0266809b239d661e0ebc3c5a6f0357d01823b7e782aa1"
```

Do not use the generic PyPI source URL in the formula. `brew style` rejects it and asks for the exact source URL from the PyPI files page.

## Validation Commands

Run in the tap repo after the final URL is known:

```bash
brew style Formula/spelunk-ml.rb
brew audit --new Formula/spelunk-ml.rb
brew install --build-from-source Formula/spelunk-ml.rb
/opt/homebrew/Cellar/spelunk-ml/0.1.0a2/bin/spelunk --version
/opt/homebrew/Cellar/spelunk-ml/0.1.0a2/bin/spelunk doctor
```
