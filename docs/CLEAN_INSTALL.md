# Clean Install Verification

Verified for `0.1.0a1` with Python 3.11.

Build artifacts:

```bash
python -m build
```

Expected artifacts:

- `dist/spelunk-0.1.0a1.tar.gz`
- `dist/spelunk-0.1.0a1-py3-none-any.whl`

Create a clean environment and install the wheel:

```bash
python3.11 -m venv /tmp/spelunk-clean-venv-311
/tmp/spelunk-clean-venv-311/bin/python -m pip install dist/spelunk-0.1.0a1-py3-none-any.whl
```

Verify console script:

```bash
/tmp/spelunk-clean-venv-311/bin/spelunk --version
```

Expected:

```text
0.1.0a1
```

Verify doctor:

```bash
/tmp/spelunk-clean-venv-311/bin/spelunk doctor
```

Expected:

```text
Spelunk doctor
Version: 0.1.0a1
Python package: importable
```

Verify import:

```bash
/tmp/spelunk-clean-venv-311/bin/python -c "from spelunk import Session, __version__; print(__version__, Session.__name__)"
```

Expected:

```text
0.1.0a1 Session
```

Note: optional capture workflows require installing the relevant extras, such as `pytorch`, `arrays`, and `datasets`.
