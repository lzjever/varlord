"""
Base class for file-based sources (YAML, JSON, TOML).

Provides common functionality:
- Path expansion (~, relative paths)
- File existence checking
- Error handling
- Nested structure flattening
"""

from __future__ import annotations

import os
from typing import Any, Mapping, Optional, Type

from varlord.metadata import get_all_field_keys
from varlord.sources.base import Source


class FileSource(Source):
    """Base class for file-based sources (YAML, JSON, TOML).

    Provides common functionality:
    - Path expansion (~, relative paths)
    - File existence checking
    - Error handling
    - Nested structure flattening to dot notation
    """

    def __init__(
        self,
        file_path: str,
        model: Optional[Type[Any]] = None,
        source_id: Optional[str] = None,
        required: bool = False,
    ):
        """Initialize FileSource.

        Args:
            file_path: Path to configuration file
            model: Optional model for field filtering
            source_id: Optional unique identifier (default: auto-generated from path)
            required: If True, raise error when file not found. If False, return empty dict.

        Note:
            - If required=False and file not found, returns empty dict (normal case)
            - If required=True and file not found, raises FileNotFoundError
        """
        # Expand path before generating ID
        expanded_path = self._expand_path(file_path)
        if source_id is None:
            source_id = f"{self._get_type_name()}:{expanded_path}"
        super().__init__(model=model, source_id=source_id)
        self._file_path = expanded_path
        self._required = required

    def _expand_path(self, path: str) -> str:
        """Expand file path (handle ~, relative paths).

        Args:
            path: File path (may contain ~ or be relative)

        Returns:
            Expanded absolute path
        """
        # Expand ~
        path = os.path.expanduser(path)
        # Convert to absolute path
        path = os.path.abspath(path)
        return path

    def _file_exists(self) -> bool:
        """Check if file exists.

        Returns:
            True if file exists, False otherwise
        """
        return os.path.exists(self._file_path) and os.path.isfile(self._file_path)

    def _load_file_content(self) -> Any:
        """Load and parse file content.

        Subclasses must implement this method.

        Returns:
            Parsed content (dict, list, etc.)

        Raises:
            FileNotFoundError: If file not found and required=True
            ValueError: If file content is invalid
        """
        raise NotImplementedError("Subclasses must implement _load_file_content()")

    def load(self) -> Mapping[str, Any]:
        """Load configuration from file.

        Returns:
            Mapping of normalized keys to values.
            Returns empty dict if file not found and required=False.

        Raises:
            FileNotFoundError: If file not found and required=True
            ValueError: If file content is invalid
        """
        # Reset status
        self._load_status = "unknown"
        self._load_error = None

        try:
            # Check file existence
            if not self._file_exists():
                if self._required:
                    raise FileNotFoundError(f"Required file not found: {self._file_path}")
                # 文件不存在是正常情况（如本地没有 .env 文件），不记录为错误
                self._load_status = "not_found"
                self._load_error = None  # 不记录错误信息，因为这是正常情况
                return {}

            # Load and parse file
            content = self._load_file_content()

            # Convert nested structure to flat dot notation
            flat_dict = self._flatten_dict(content)

            # Filter by model if provided
            if self._model:
                valid_keys = get_all_field_keys(self._model)
                flat_dict = {k: v for k, v in flat_dict.items() if k in valid_keys}

            self._load_status = "success"
            return flat_dict

        except FileNotFoundError:
            # 文件不存在是正常情况（如本地没有 .env 文件），不记录为错误
            self._load_status = "not_found"
            self._load_error = None  # 不记录错误信息，因为这是正常情况
            if self._required:
                raise
            return {}
        except Exception as e:
            # 真正的错误（如文件格式错误、权限问题等）
            self._load_status = "failed"
            self._load_error = str(e)
            if self._required:
                raise
            return {}

    def _flatten_dict(self, d: dict, parent_key: str = "", sep: str = ".") -> dict:
        """Flatten nested dictionary to dot notation.

        Args:
            d: Nested dictionary
            parent_key: Parent key prefix (for recursion)
            sep: Separator for nested keys (default: ".")

        Returns:
            Flattened dictionary with dot notation keys

        Example:
            >>> source = FileSource("test.yaml")
            >>> source._flatten_dict({"db": {"host": "localhost", "port": 5432}})
            {'db.host': 'localhost', 'db.port': 5432}
        """
        items = []
        for k, v in d.items():
            # Normalize key name using normalize_key function
            from varlord.sources.base import normalize_key

            normalized_k = normalize_key(str(k))

            new_key = f"{parent_key}{sep}{normalized_k}" if parent_key else normalized_k

            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))

        return dict(items)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<{self.__class__.__name__}(path={self._file_path!r}, status={self._load_status})>"
