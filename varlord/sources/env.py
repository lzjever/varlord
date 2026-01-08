"""
Environment variable source.

Loads configuration from environment variables, filtered by model fields.
"""

from __future__ import annotations

import os
from typing import Any, Mapping, Optional, Type

from varlord.metadata import get_all_field_keys
from varlord.sources.base import Source, normalize_key


class Env(Source):
    """Source that loads configuration from environment variables.

    Only loads environment variables that map to fields defined in the model.
    Model is required and will be auto-injected by Config if not provided.

    Example:
        >>> @dataclass
        ... class Config:
        ...     api_key: str = field()  # Required by default
        >>> # Environment: API_KEY=value1 OTHER_VAR=ignored
        >>> source = Env(model=Config)
        >>> source.load()
        {'api_key': 'value1'}  # OTHER_VAR is ignored
    """

    def __init__(
        self,
        model: Optional[Type[Any]] = None,
        prefix: Optional[str] = None,
        source_id: Optional[str] = None,
    ):
        """Initialize Env source.

        Args:
            model: Optional model to filter environment variables.
                  Only variables that map to model fields will be loaded.
                  If None, model will be auto-injected by Config when used in Config.
                  If provided, this model will be used (allows override).
            prefix: Optional prefix for environment variables (e.g., "TITAN__").
                   If None, matches all environment variables that map to model fields.
                   If provided, only variables starting with this prefix (uppercase) are considered.
            source_id: Optional unique identifier (default: "env" or "env:{prefix}")

        Note:
            - Prefix filtering is optional. If prefix is None, all env vars are checked against model fields.
            - Recommended: Omit model parameter when used in Config (auto-injected).
            - Advanced: Provide model explicitly if using source independently.
        """
        super().__init__(model=model, source_id=source_id or (f"env:{prefix}" if prefix else "env"))
        self._prefix = prefix.upper() if prefix else None

    @property
    def name(self) -> str:
        """Return source name."""
        return "env"

    def _generate_id(self) -> str:
        """Generate unique ID for Env source."""
        if self._prefix:
            return f"env:{self._prefix}"
        return "env"

    def load(self) -> Mapping[str, Any]:
        """Load configuration from environment variables, filtered by model fields.

        Returns:
            A mapping of normalized keys to environment variable values.
            Only includes variables that map to model fields.

        Raises:
            ValueError: If model is not provided
        """
        # Reset status
        self._load_status = "unknown"
        self._load_error = None

        try:
            if not self._model:
                raise ValueError(
                    "Env source requires model. "
                    "When used in Config, model is auto-injected. "
                    "When used independently, provide model explicitly: Env(model=AppConfig)"
                )

            # Get all valid field keys from model
            valid_keys = get_all_field_keys(self._model)

            result: dict[str, Any] = {}
            for env_key, env_value in os.environ.items():
                # Check prefix if specified (case-insensitive)
                if self._prefix:
                    # Compare in uppercase for case-insensitive matching
                    if not env_key.upper().startswith(self._prefix):
                        continue
                    # Remove prefix (preserve original case for normalization)
                    key_without_prefix = env_key[len(self._prefix) :]
                    normalized_key = normalize_key(key_without_prefix)
                else:
                    # Normalize env var name (no prefix filtering)
                    normalized_key = normalize_key(env_key)

                # Only load if it matches a model field
                if normalized_key in valid_keys:
                    result[normalized_key] = env_value

            self._load_status = "success"
            return result
        except Exception as e:
            self._load_status = "failed"
            self._load_error = str(e)
            raise

    def __repr__(self) -> str:
        """Return string representation."""
        if self._prefix:
            return f"<Env(prefix={self._prefix!r})>"
        return "<Env(model-based)>"
