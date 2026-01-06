"""
DotEnv source.

Loads configuration from .env files using python-dotenv.
Only loads variables that map to fields defined in the model.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Type

try:
    from dotenv import dotenv_values
except ImportError:
    dotenv_values = None  # type: ignore

from varlord.metadata import get_all_field_keys
from varlord.sources.base import Source, normalize_key


class DotEnv(Source):
    """Source that loads configuration from .env files.

    Requires the 'dotenv' extra: pip install varlord[dotenv]

    Only loads variables that map to fields defined in the model.
    Model is required and will be auto-injected by Config.

    Example:
        >>> @dataclass
        ... class Config:
        ...     api_key: str = field()  # Required by default
        >>> # .env file: API_KEY=value1 OTHER_VAR=ignored
        >>> source = DotEnv(".env", model=Config)
        >>> source.load()
        {'api_key': 'value1'}  # OTHER_VAR is ignored
    """

    def __init__(
        self,
        dotenv_path: str = ".env",
        model: Optional[Type[Any]] = None,
        encoding: Optional[str] = None,
    ):
        """Initialize DotEnv source.

        Args:
            dotenv_path: Path to .env file
            model: Model to filter .env variables.
                  Only variables that map to model fields will be loaded.
                  Model is required and will be auto-injected by Config.
            encoding: File encoding (default: None, uses system default)

        Raises:
            ImportError: If python-dotenv is not installed
        """
        super().__init__(model=model)
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
        """Load configuration from .env file, filtered by model fields.

        Returns:
            A mapping of normalized keys to their values.
            Only includes variables that map to model fields.

        Raises:
            ValueError: If model is not provided
        """
        if not self._model:
            raise ValueError("DotEnv source requires model (should be auto-injected by Config)")

        if dotenv_values is None:
            return {}

        # Load all variables from .env file
        raw_values = dotenv_values(self._dotenv_path, encoding=self._encoding) or {}

        # Get all valid field keys from model
        valid_keys = get_all_field_keys(self._model)

        # Filter by model fields
        result = {}
        for env_key, env_value in raw_values.items():
            normalized_key = normalize_key(env_key)
            if normalized_key in valid_keys:
                result[normalized_key] = env_value

        return result

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<DotEnv(path={self._dotenv_path!r})>"
