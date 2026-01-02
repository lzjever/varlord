"""
Environment variable source.

Loads configuration from environment variables, filtered by model fields.
"""

from __future__ import annotations
import os
from typing import Mapping, Any, Optional, Type

from varlord.sources.base import Source, normalize_key
from varlord.metadata import get_all_field_keys


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

    def __init__(self, model: Optional[Type[Any]] = None):
        """Initialize Env source.

        Args:
            model: Optional model to filter environment variables.
                  Only variables that map to model fields will be loaded.
                  If None, model will be auto-injected by Config when used in Config.
                  If provided, this model will be used (allows override).

        Note:
            - Prefix filtering is removed. All env vars are checked against model fields.
            - Recommended: Omit model parameter when used in Config (auto-injected).
            - Advanced: Provide model explicitly if using source independently.
        """
        super().__init__(model=model)

    @property
    def name(self) -> str:
        """Return source name."""
        return "env"

    def load(self) -> Mapping[str, Any]:
        """Load configuration from environment variables, filtered by model fields.

        Returns:
            A mapping of normalized keys to environment variable values.
            Only includes variables that map to model fields.

        Raises:
            ValueError: If model is not provided
        """
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
            # Normalize env var name (no prefix filtering)
            normalized_key = normalize_key(env_key)

            # Only load if it matches a model field
            if normalized_key in valid_keys:
                result[normalized_key] = env_value

        return result

    def __repr__(self) -> str:
        """Return string representation."""
        return "<Env(model-based)>"
