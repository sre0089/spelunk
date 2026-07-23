"""Typed Textual messages for Spelunk screens and widgets."""

from __future__ import annotations

from dataclasses import dataclass

from textual.message import Message

from spelunk.domain import FeatureId, LayerId, RunId


@dataclass
class RunOpened(Message):
    run_id: RunId


@dataclass
class LayerSelected(Message):
    layer_id: LayerId


@dataclass
class FeatureSelected(Message):
    feature_id: FeatureId


@dataclass
class CommandInvoked(Message):
    command: str

