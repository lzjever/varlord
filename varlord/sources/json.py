"""
JSON source.

Loads configuration from JSON files.
Only loads keys that map to fields defined in the model.
Uses standard library json module (no extra dependencies).
"""

from __future__ import annotations

import json
from typing import Any, Optional, Type

from varlord.sources.file_base import FileSource


class JSON(FileSource):
    """Source that loads configuration from JSON files.

    Uses standard library json module (no extra dependencies).

    Only loads keys that map to fields defined in the model.
    Model is required and will be auto-injected by Config.

    Example:
        >>> @dataclass
        ... class Config:
        ...     host: str = field()
        >>> # config.json: {"host": "0.0.0.0"}
        >>> source = JSON("config.json", model=Config)
        >>> source.load()
        {'host': '0.0.0.0'}
    """

    def __init__(
        self,
        file_path: str,
        model: Optional[Type[Any]] = None,
        source_id: Optional[str] = None,
        required: bool = False,
    ):
        """Initialize JSON source.

        Args:
            file_path: Path to JSON file
            model: Optional model for field filtering
            source_id: Optional unique identifier (default: auto-generated from path)
            required: If True, raise error when file not found
        """
        super().__init__(file_path, model=model, source_id=source_id, required=required)

    @property
    def name(self) -> str:
        """Return source name."""
        return "json"

    def _load_file_content(self) -> Any:
        """Load and parse JSON file.

        Returns:
            Parsed JSON content (dict, list, etc.)

        Raises:
            FileNotFoundError: If file not found
            json.JSONDecodeError: If JSON is invalid
        """
        with open(self._file_path, encoding="utf-8") as f:
            return json.load(f) or {}
