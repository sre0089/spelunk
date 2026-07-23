from collections import OrderedDict

import torch


def build_model() -> torch.nn.Module:
    return torch.nn.Sequential(
        OrderedDict(
            [
                ("encoder", torch.nn.Linear(8, 4)),
                ("decoder", torch.nn.Linear(4, 8)),
            ]
        )
    )
