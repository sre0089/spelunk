import json
from pathlib import Path
from typing import Any, cast

import pytest

from spelunk.capture import DatasetLoader, DatasetSpec
from spelunk.domain import DatasetId


def test_csv_dataset_loader_streams_rows(tmp_path: Path) -> None:
    path = tmp_path / "samples.csv"
    path.write_text("label,value\ncat,1\ndog,2\n")
    spec = DatasetSpec(id=DatasetId("csv-001"), name="csv", kind="csv", source=path)

    samples = list(DatasetLoader(spec).iter_samples())

    assert [sample.id for sample in samples] == ["0", "1"]
    assert samples[0].data == {"label": "cat", "value": "1"}
    assert samples[1].metadata["index"] == 1


def test_jsonl_dataset_loader_streams_records(tmp_path: Path) -> None:
    path = tmp_path / "samples.jsonl"
    path.write_text(json.dumps({"text": "alpha"}) + "\n\n" + json.dumps({"text": "beta"}) + "\n")
    spec = DatasetSpec(id=DatasetId("jsonl-001"), name="jsonl", kind="jsonl", source=path)

    samples = list(DatasetLoader(spec).iter_samples())

    assert [sample.id for sample in samples] == ["0", "2"]
    assert samples[0].data == {"text": "alpha"}
    assert samples[1].data == {"text": "beta"}


def test_numpy_dataset_loader_streams_array_rows(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    path = tmp_path / "samples.npy"
    np.save(path, np.array([[1, 2], [3, 4]]))
    spec = DatasetSpec(id=DatasetId("numpy-001"), name="numpy", kind="numpy", source=path)

    samples = list(DatasetLoader(spec).iter_samples())

    assert [sample.id for sample in samples] == ["0", "1"]
    first_row = cast(Any, samples[0].data)
    second_row = cast(Any, samples[1].data)
    assert first_row.tolist() == [1, 2]
    assert second_row.tolist() == [3, 4]


def test_image_folder_dataset_loader_streams_images(tmp_path: Path) -> None:
    pillow = pytest.importorskip("PIL.Image")
    image_path = tmp_path / "sample.png"
    pillow.new("RGB", (3, 2), color=(255, 0, 0)).save(image_path)
    (tmp_path / "notes.txt").write_text("ignored")
    spec = DatasetSpec(
        id=DatasetId("images-001"),
        name="images",
        kind="image-folder",
        source=tmp_path,
    )

    samples = list(DatasetLoader(spec).iter_samples())

    assert [sample.id for sample in samples] == ["0"]
    image = cast(Any, samples[0].data)
    source = cast(str, samples[0].metadata["source"])
    assert image.size == (3, 2)
    assert source.endswith("sample.png")
