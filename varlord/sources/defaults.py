"""
Defaults source.

Loads default values from dataclass model fields.
"""

from __future__ import annotations
from typing import Mapping, Any, Type
from dataclasses import fields, is_dataclass

from varlord.sources.base import Source


class Defaults(Source):
    """Source that loads default values from a dataclass model.

    This source extracts default values from dataclass field definitions.
    It should typically be placed first in the sources list to provide
    baseline defaults that can be overridden by other sources.

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
        """
        if not is_dataclass(model):
            raise TypeError(f"Model must be a dataclass, got {type(model)}")
        self._model = model

    @property
    def name(self) -> str:
        """Return source name."""
        return "defaults"

    def load(self) -> Mapping[str, Any]:
        """Load default values from the model.

        Returns:
            A mapping of field names to their default values.
            Fields without defaults are excluded.
        """
        from dataclasses import _MISSING_TYPE

        result: dict[str, Any] = {}
        for field in fields(self._model):
            # Check if field has a default value
            # field.default is ... means no default
            # field.default is _MISSING_TYPE also means no default
            if field.default is not ... and not isinstance(field.default, _MISSING_TYPE):
                result[field.name] = field.default
            elif field.default_factory is not ... and not isinstance(
                field.default_factory, _MISSING_TYPE
            ):
                # Handle default_factory
                try:
                    result[field.name] = field.default_factory()
                except Exception:
                    # If factory fails, skip this field
                    pass
        return result

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Defaults(model={self._model.__name__})>"
