"""Shared Spelunk exception types."""

from __future__ import annotations


class SpelunkError(Exception):
    """Base class for user-facing Spelunk errors."""


class SchemaVersionError(SpelunkError):
    """Raised when a stored schema version cannot be read safely."""

