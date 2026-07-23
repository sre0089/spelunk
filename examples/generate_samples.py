"""Generate a tiny NumPy dataset for Spelunk examples."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate example Spelunk samples.")
    parser.add_argument(
        "output",
        nargs="?",
        default="examples/samples.npy",
        help="Output .npy path.",
    )
    args = parser.parse_args(argv)
    write_samples(Path(args.output))


def write_samples(path: Path) -> None:
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    samples = np.array(
        [
            [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
            [0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0],
            [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
    np.save(path, samples)


if __name__ == "__main__":
    main()
