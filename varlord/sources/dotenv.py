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
        source_id: Optional[str] = None,
    ):
        """Initialize DotEnv source.

        Args:
            dotenv_path: Path to .env file
            model: Model to filter .env variables.
                  Only variables that map to model fields will be loaded.
                  Model is required and will be auto-injected by Config.
            encoding: File encoding (default: None, uses system default)
            source_id: Optional unique identifier (default: auto-generated from path)

        Raises:
            ImportError: If python-dotenv is not installed
        """
        if dotenv_values is None:
            raise ImportError(
                "python-dotenv is required for DotEnv source. "
                "Install it with: pip install varlord[dotenv]"
            )
        # Generate ID before calling super() if not provided
        if source_id is None:
            source_id = f"dotenv:{dotenv_path}"
        super().__init__(model=model, source_id=source_id)
        self._dotenv_path = dotenv_path
        self._encoding = encoding

    @property
    def name(self) -> str:
        """Return source name."""
        return "dotenv"

    def _generate_id(self) -> str:
        """Generate unique ID for DotEnv source."""
        return f"dotenv:{self._dotenv_path}"

    def load(self) -> Mapping[str, Any]:
        """Load configuration from .env file, filtered by model fields.

        Returns:
            A mapping of normalized keys to their values.
            Only includes variables that map to model fields.

        Raises:
            ValueError: If model is not provided
        """
        # Reset status
        self._load_status = "unknown"
        self._load_error = None

        try:
            if not self._model:
                raise ValueError("DotEnv source requires model (should be auto-injected by Config)")

            if dotenv_values is None:
                self._load_status = "failed"
                self._load_error = "python-dotenv not installed"
                return {}

            # Check if file exists
            import os

            if not os.path.exists(self._dotenv_path) or not os.path.isfile(self._dotenv_path):
                self._load_status = "not_found"
                self._load_error = None  # File not found is normal
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

            self._load_status = "success"
            return result
        except FileNotFoundError:
            self._load_status = "not_found"
            self._load_error = None  # File not found is normal
            return {}
        except Exception as e:
            self._load_status = "failed"
            self._load_error = str(e)
            if isinstance(e, ValueError):
                raise
            return {}

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<DotEnv(path={self._dotenv_path!r})>"
