"""
YAML source.

Loads configuration from YAML files.
Only loads keys that map to fields defined in the model.
"""

from __future__ import annotations

from typing import Any, Optional, Type

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from varlord.sources.file_base import FileSource


class YAML(FileSource):
    """Source that loads configuration from YAML files.

    Requires the 'yaml' extra: pip install varlord[yaml]

    Only loads keys that map to fields defined in the model.
    Model is required and will be auto-injected by Config.

    Example:
        >>> @dataclass
        ... class Config:
        ...     host: str = field()
        >>> # config.yaml: host: 0.0.0.0
        >>> source = YAML("config.yaml", model=Config)
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
        """Initialize YAML source.

        Args:
            file_path: Path to YAML file
            model: Optional model for field filtering
            source_id: Optional unique identifier (default: auto-generated from path)
            required: If True, raise error when file not found

        Raises:
            ImportError: If pyyaml is not installed
        """
        if yaml is None:
            raise ImportError(
                "pyyaml is required for YAML source. Install it with: pip install varlord[yaml]"
            )
        super().__init__(file_path, model=model, source_id=source_id, required=required)

    @property
    def name(self) -> str:
        """Return source name."""
        return "yaml"

    def _load_file_content(self) -> Any:
        """Load and parse YAML file.

        Returns:
            Parsed YAML content (dict, list, etc.)

        Raises:
            FileNotFoundError: If file not found
            yaml.YAMLError: If YAML is invalid
        """
        with open(self._file_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
