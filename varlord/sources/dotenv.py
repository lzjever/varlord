"""
DotEnv source.

Loads configuration from .env files using python-dotenv.
This is an optional source that requires the 'dotenv' extra.
"""

from __future__ import annotations
from typing import Mapping, Any, Optional

try:
    from dotenv import dotenv_values
except ImportError:
    dotenv_values = None  # type: ignore

from varlord.sources.base import Source, normalize_key


class DotEnv(Source):
    """Source that loads configuration from .env files.

    Requires the 'dotenv' extra: pip install varlord[dotenv]

    Keys are normalized to lowercase for consistency with other sources.
    Note: For nested keys and advanced normalization, use Env source with DotEnv.

    Example:
        >>> # .env file:
        >>> # HOST=0.0.0.0
        >>> # PORT=9000
        >>> source = DotEnv(".env")
        >>> source.load()
        {'host': '0.0.0.0', 'port': '9000'}

        >>> # For nested keys, use with Env source:
        >>> # .env: APP_DB__HOST=localhost
        >>> sources = [DotEnv(".env"), Env(prefix="APP_", separator="__")]
    """

    def __init__(self, dotenv_path: str = ".env", encoding: Optional[str] = None):
        """Initialize DotEnv source.

        Args:
            dotenv_path: Path to .env file
            encoding: File encoding (default: None, uses system default)

        Raises:
            ImportError: If python-dotenv is not installed
        """
        if dotenv_values is None:
            raise ImportError(
                "python-dotenv is required for DotEnv source. "
                "Install it with: pip install varlord[dotenv]"
            )
        self._dotenv_path = dotenv_path
        self._encoding = encoding

    @property
    def name(self) -> str:
        """Return source name."""
        return "dotenv"

    def load(self) -> Mapping[str, Any]:
        """Load configuration from .env file.

        Returns:
            A mapping of normalized keys (lowercase, dot notation) to their values.
            Keys are normalized to lowercase for consistency with other sources.
        """
        if dotenv_values is None:
            return {}
        raw_values = dotenv_values(self._dotenv_path, encoding=self._encoding) or {}

        # Normalize keys using unified rules
        result = {}
        for key, value in raw_values.items():
            normalized_key = normalize_key(key)
            result[normalized_key] = value

        return result

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<DotEnv(path={self._dotenv_path!r})>"
