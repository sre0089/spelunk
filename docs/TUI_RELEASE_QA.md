# TUI Release QA

Validated on 2026-07-28 before the next alpha build.

## Automated TUI Coverage

```bash
/opt/homebrew/bin/python3.11 -m pytest tests/test_tui_app.py
```

Result: 14 passed.

Covered:

- project picker and recent run loading
- loaded run overview, layers, diagnostics, inspect, compare, and reports views
- inspect feature prompt opened with `i` and submitted with `Enter`
- compare run prompt opened with `c` and submitted with `Enter`
- Markdown report preview in the reports pane

## Local Source Smoke

Workspace: `/tmp/spelunk-m61-tui-qa`

```bash
/opt/homebrew/bin/python3.11 examples/generate_samples.py /tmp/spelunk-m61-tui-qa/samples.npy
PYTHONPATH=src /opt/homebrew/bin/python3.11 -c 'from spelunk.cli.app import app; app(prog_name="spelunk")' layers --model-path examples/model_factory.py --factory build_model
PYTHONPATH=src /opt/homebrew/bin/python3.11 -c 'from spelunk.cli.app import app; app(prog_name="spelunk")' quickstart --run /tmp/spelunk-m61-tui-qa/runs/tiny.spelunk --model-path examples/model_factory.py --factory build_model --dataset /tmp/spelunk-m61-tui-qa/samples.npy --layers encoder --layers decoder --batch-size 2
PYTHONPATH=src /opt/homebrew/bin/python3.11 -c 'from spelunk.cli.app import app; app(prog_name="spelunk")' inspect /tmp/spelunk-m61-tui-qa/runs/tiny.spelunk --layer encoder --feature 0
PYTHONPATH=src /opt/homebrew/bin/python3.11 -c 'from spelunk.cli.app import app; app(prog_name="spelunk")' scan /tmp/spelunk-m61-tui-qa/runs/tiny.spelunk --json
```

Observed:

- layer discovery listed `encoder` and `decoder`
- quickstart captured 4 samples across both layers
- reports were generated at `reports/report.md` and `reports/report.json`
- inspect returned feature statistics and top examples
- scan JSON included `dead_feature_count` and `dead_feature_fraction` evidence
