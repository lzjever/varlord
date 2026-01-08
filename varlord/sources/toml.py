"""
TOML source.

Loads configuration from TOML files.
Only loads keys that map to fields defined in the model.
"""

from __future__ import annotations

import sys
from typing import Any, Optional, Type

try:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib
except ImportError:
    tomllib = None  # type: ignore

from varlord.sources.file_base import FileSource


class TOML(FileSource):
    """Source that loads configuration from TOML files.

    Requires the 'toml' extra for Python < 3.11: pip install varlord[toml]
    Python 3.11+ has built-in tomllib support.

    Only loads keys that map to fields defined in the model.
    Model is required and will be auto-injected by Config.

    Example:
        >>> @dataclass
        ... class Config:
        ...     host: str = field()
        >>> # config.toml: host = "0.0.0.0"
        >>> source = TOML("config.toml", model=Config)
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
        """Initialize TOML source.

        Args:
            file_path: Path to TOML file
            model: Optional model for field filtering
            source_id: Optional unique identifier (default: auto-generated from path)
            required: If True, raise error when file not found

        Raises:
            ImportError: If tomli is not installed (Python < 3.11)
        """
        if tomllib is None:
            raise ImportError(
                "tomli is required for TOML source (Python < 3.11). "
                "Install it with: pip install varlord[toml]"
            )
        super().__init__(file_path, model=model, source_id=source_id, required=required)

    @property
    def name(self) -> str:
        """Return source name."""
        return "toml"

    def _load_file_content(self) -> Any:
        """Load and parse TOML file.

        Returns:
            Parsed TOML content (dict)

        Raises:
            FileNotFoundError: If file not found
            tomllib.TOMLDecodeError: If TOML is invalid
        """
        with open(self._file_path, "rb") as f:
            return tomllib.load(f) or {}
