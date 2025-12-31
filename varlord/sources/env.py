"""
Environment variable source.

Loads configuration from environment variables with optional prefix
and key normalization.
"""

from __future__ import annotations
import os
from typing import Mapping, Any, Optional, Callable

from varlord.sources.base import Source, normalize_key


class Env(Source):
    """Source that loads configuration from environment variables.

    Supports:
    - Prefix filtering (e.g., ``"APP_"`` to only load APP_* variables)
    - Key normalization (e.g., ``"APP_DB__HOST"`` -> ``"db.host"``)
    - Custom key transformation

    Example:
        >>> # Environment: APP_HOST=0.0.0.0 APP_PORT=9000
        >>> source = Env(prefix="APP_")
        >>> source.load()
        {'host': '0.0.0.0', 'port': '9000'}

        >>> # With nested key support
        >>> # Environment: APP_DB__HOST=localhost
        >>> source = Env(prefix="APP_")
        >>> source.load()
        {'db.host': 'localhost'}
    """

    def __init__(
        self,
        prefix: str = "",
        normalize_key: Optional[Callable[[str], str]] = None,
    ):
        """Initialize Env source.

        Args:
            prefix: Prefix to filter environment variables (e.g., ``"APP_"``)
            normalize_key: Optional function to normalize keys.
                          If None, uses unified normalization (__ -> ., _ preserved, lowercase)
        """
        self._prefix = prefix
        self._normalize_key = normalize_key or self._default_normalize

    @property
    def name(self) -> str:
        """Return source name."""
        return "env"

    def _default_normalize(self, key: str) -> str:
        """Default key normalization.

        Converts "APP_DB__HOST" -> "db.host" (assuming prefix="APP_")
        Uses unified normalization: __ -> ., _ preserved, lowercase
        """
        # Remove prefix
        if self._prefix and key.startswith(self._prefix):
            key = key[len(self._prefix) :]

        # Apply unified normalization
        return normalize_key(key)

    def load(self) -> Mapping[str, Any]:
        """Load configuration from environment variables.

        Returns:
            A mapping of normalized keys to environment variable values.
        """
        result: dict[str, Any] = {}
        for key, value in os.environ.items():
            # Filter by prefix
            if self._prefix and not key.startswith(self._prefix):
                continue

            # Normalize key
            normalized_key = self._normalize_key(key)

            # Store value
            result[normalized_key] = value

        return result

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Env(prefix={self._prefix!r})>"
