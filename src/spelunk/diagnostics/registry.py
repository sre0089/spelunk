"""Small built-in diagnostic registry."""

from __future__ import annotations

from dataclasses import dataclass

from spelunk.diagnostics.interfaces import Diagnostic, DiagnosticContext
from spelunk.domain import DiagnosticResult


@dataclass(slots=True)
class DiagnosticRegistry:
    diagnostics: tuple[Diagnostic, ...]

    def run_all(self, context: DiagnosticContext) -> tuple[DiagnosticResult, ...]:
        results: list[DiagnosticResult] = []
        for diagnostic in self.diagnostics:
            results.extend(diagnostic.run(context))
        return tuple(results)
