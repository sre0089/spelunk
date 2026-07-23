import subprocess
import sys


def test_domain_import_does_not_load_ui_or_framework_modules() -> None:
    script = (
        "import json, sys; "
        "import spelunk.domain; "
        "forbidden = {'rich', 'textual', 'typer', 'torch'}; "
        "print(json.dumps(sorted(forbidden.intersection(sys.modules))))"
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "[]"


def test_neutral_adapter_import_does_not_load_torch() -> None:
    script = (
        "import json, sys; "
        "import spelunk.adapters; "
        "print(json.dumps('torch' in sys.modules))"
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "false"
