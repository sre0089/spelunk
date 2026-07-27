from collections import OrderedDict
from pathlib import Path

import pytest

import spelunk
from spelunk.services import Session


def test_python_api_capture_accepts_in_memory_dataset(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    torch = pytest.importorskip("torch")

    model = torch.nn.Sequential(
        OrderedDict([("encoder", torch.nn.Linear(2, 2, bias=False))])
    )
    samples = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)

    result = spelunk.capture(
        model=model,
        dataset=samples,
        layers=["encoder"],
        run=tmp_path / "api-run.spelunk",
        batch_size=2,
    )

    assert result.run.run_id == "api-run"
    assert result.captured_samples == 2
    assert result.captured_layers == ("encoder",)
    scan = Session.open(tmp_path / "api-run.spelunk").scan()
    assert scan.layers[0].layer_id == "encoder"
    assert scan.layers[0].activation_count == 2


def test_python_api_capture_requires_layers(tmp_path: Path) -> None:
    torch = pytest.importorskip("torch")

    with pytest.raises(spelunk.SpelunkError, match="At least one layer is required"):
        spelunk.capture(
            model=torch.nn.Linear(2, 2),
            dataset=[[1.0, 2.0]],
            layers=[],
            run=tmp_path / "api-run.spelunk",
        )
