# Install Spelunk

Spelunk is published as the package `spelunk-ml`.

The installed command is:

```bash
spelunk
```

The Python import is:

```python
import spelunk
```

## pip

```bash
python -m pip install spelunk-ml
```

For local capture workflows with PyTorch and array datasets:

```bash
python -m pip install "spelunk-ml[pytorch,arrays,datasets]"
```

Verify:

```bash
spelunk --version
spelunk doctor
```

## Homebrew

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

## From Source

```bash
git clone https://github.com/sre0089/spelunk.git
cd spelunk
python -m pip install -e ".[dev,arrays,datasets,tui]"
```

Add PyTorch support when needed:

```bash
python -m pip install -e ".[pytorch]"
```
