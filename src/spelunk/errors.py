"""Shared Spelunk exception types."""

from __future__ import annotations


class SpelunkError(Exception):
    """Base class for user-facing Spelunk errors."""


class SchemaVersionError(SpelunkError):
    """Raised when a stored schema version cannot be read safely."""


class ManifestError(SpelunkError):
    """Raised when a stored manifest is malformed."""


class StorageError(SpelunkError):
    """Raised when local storage cannot be read or written."""


class UnsupportedOperationError(SpelunkError):
    """Raised when a service contract exists but its implementation is not available yet."""
