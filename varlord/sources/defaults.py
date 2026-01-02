"""
Defaults source.

Loads default values from dataclass model fields.
This is now an internal source used automatically by Config.
"""

from __future__ import annotations
from typing import Mapping, Any, Type, Optional
from dataclasses import is_dataclass

from varlord.sources.base import Source
from varlord.metadata import get_all_fields_info


class Defaults(Source):
    """Source that loads default values from a dataclass model.

    This source extracts default values from dataclass field definitions.
    It is automatically used by Config as the first source (base layer).

    Example:
        >>> @dataclass
        ... class Config:
        ...     host: str = "localhost"
        ...     port: int = 8000
        ...
        >>> source = Defaults(model=Config)
        >>> source.load()
        {'host': 'localhost', 'port': 8000}
    """

    def __init__(self, model: Type[Any]):
        """Initialize Defaults source.

        Args:
            model: The dataclass model to extract defaults from.

        Raises:
            TypeError: If model is not a dataclass
        """
        super().__init__(model=model)

        if not is_dataclass(model):
            raise TypeError(f"Model must be a dataclass, got {type(model)}")

        # Support precomputed defaults (for performance)
        self._precomputed_defaults: Optional[dict[str, Any]] = None

    @property
    def name(self) -> str:
        """Return source name."""
        return "defaults"

    def load(self) -> Mapping[str, Any]:
        """Load default values from the model.

        Returns:
            A mapping of normalized keys to their default values.
            Fields without defaults are excluded.
            Supports nested fields (e.g., {"db.host": "localhost"}).
        """
        # Use precomputed defaults if available
        if self._precomputed_defaults is not None:
            return self._precomputed_defaults.copy()

        # Extract defaults from model
        result: dict[str, Any] = {}
        field_infos = get_all_fields_info(self._model)

        for field_info in field_infos:
            # Check for default value
            if field_info.default is not ...:
                result[field_info.normalized_key] = field_info.default
            # Check for default_factory
            elif field_info.default_factory is not ...:
                try:
                    result[field_info.normalized_key] = field_info.default_factory()
                except Exception:
                    pass  # Skip if factory fails

        return result

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Defaults(model={self._model.__name__})>"
