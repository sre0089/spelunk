# Public Install 0.1.0a2 Gate

Checked on 2026-07-28.

## Public PyPI Status

Command:

```bash
/tmp/spelunk-a2-install-smoke/venv/bin/python -m pip install spelunk-ml==0.1.0a2
```

Result:

```text
ERROR: Could not find a version that satisfies the requirement spelunk-ml==0.1.0a2 (from versions: 0.1.0a1)
ERROR: No matching distribution found for spelunk-ml==0.1.0a2
```

Public install validation is blocked until `dist/spelunk_ml-0.1.0a2*` is uploaded to PyPI.

## Local Wheel Smoke

Clean venv:

```bash
/opt/homebrew/bin/python3.11 -m venv /tmp/spelunk-a2-install-smoke/venv
/tmp/spelunk-a2-install-smoke/venv/bin/python -m pip install dist/spelunk_ml-0.1.0a2-py3-none-any.whl
```

Verified:

```bash
/tmp/spelunk-a2-install-smoke/venv/bin/spelunk --version
/tmp/spelunk-a2-install-smoke/venv/bin/spelunk doctor
/tmp/spelunk-a2-install-smoke/venv/bin/python -c 'import spelunk; print(spelunk.__version__); print(callable(spelunk.capture))'
/tmp/spelunk-a2-install-smoke/venv/bin/spelunk capture --help
```

Observed:

- `spelunk --version` printed `0.1.0a2`
- `spelunk doctor` reported the package importable
- `import spelunk` exposed version `0.1.0a2`
- `spelunk.capture` was callable
- `spelunk capture --help` exposed `--checkpoint-path`

## Post-Publish Commands

After uploading to PyPI, rerun:

```bash
rm -rf /tmp/spelunk-a2-public-smoke
/opt/homebrew/bin/python3.11 -m venv /tmp/spelunk-a2-public-smoke/venv
/tmp/spelunk-a2-public-smoke/venv/bin/python -m pip install "spelunk-ml[pytorch,arrays,datasets]==0.1.0a2"
/tmp/spelunk-a2-public-smoke/venv/bin/spelunk --version
/tmp/spelunk-a2-public-smoke/venv/bin/spelunk doctor
```
