"""Diagnostics that turn statistics into conclusions and evidence."""

from spelunk.diagnostics.builtin import ActivationHealthDiagnostic
from spelunk.diagnostics.interfaces import Diagnostic, DiagnosticContext
from spelunk.diagnostics.registry import DiagnosticRegistry

__all__ = [
    "ActivationHealthDiagnostic",
    "Diagnostic",
    "DiagnosticContext",
    "DiagnosticRegistry",
]
