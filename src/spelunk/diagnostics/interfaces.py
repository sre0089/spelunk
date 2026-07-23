"""Diagnostic interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from spelunk.domain import DiagnosticResult
from spelunk.storage import ActivationQuery, ActivationStore


@dataclass(frozen=True, slots=True)
class DiagnosticContext:
    store: ActivationStore
    query: ActivationQuery | None = None


class Diagnostic(Protocol):
    id: str
    name: str

    def run(self, context: DiagnosticContext) -> tuple[DiagnosticResult, ...]:
        """Run a diagnostic and return typed results."""

