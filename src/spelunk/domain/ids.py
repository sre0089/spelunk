"""Typed identifiers used across Spelunk domain objects."""

from __future__ import annotations

from typing import NewType

ModelId = NewType("ModelId", str)
DatasetId = NewType("DatasetId", str)
RunId = NewType("RunId", str)
CheckpointId = NewType("CheckpointId", str)
LayerId = NewType("LayerId", str)
FeatureId = NewType("FeatureId", str)
SampleId = NewType("SampleId", str)
DiagnosticId = NewType("DiagnosticId", str)
ReportId = NewType("ReportId", str)

