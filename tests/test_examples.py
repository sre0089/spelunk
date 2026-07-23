import json
from pathlib import Path
from typing import Any, cast

import pytest


def test_example_generator_writes_expected_numpy_shape(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    namespace: dict[str, Any] = {}
    script = Path("examples/generate_samples.py")
    exec(script.read_text(), namespace)  # noqa: S102
    write_samples = cast(Any, namespace["write_samples"])
    output = tmp_path / "samples.npy"

    write_samples(output)

    samples = np.load(output)
    assert samples.shape == (4, 8)
    assert str(samples.dtype) == "float32"


def test_example_capture_config_points_to_generated_samples() -> None:
    payload = json.loads(Path("examples/capture.json").read_text())

    assert payload["run"] == "../runs/tiny-autoencoder.spelunk"
    assert payload["model"]["path"] == "model_factory.py"
    assert payload["dataset"]["source"] == "samples.npy"
