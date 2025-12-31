"""
Command-line argument source.

Loads configuration from command-line arguments using argparse.
"""

from __future__ import annotations
import sys
import argparse
from typing import Mapping, Any, Optional, List

from varlord.sources.base import Source, normalize_key


class CLI(Source):
    """Source that loads configuration from command-line arguments.

    Uses argparse to parse command-line arguments. Supports:
    - Automatic type inference from model fields
    - Boolean flags (--flag / --no-flag)
    - Nested keys via --db-host style arguments (maps to db.host)

    Keys are normalized to dot notation for consistency with other sources:
    - --db-host → db.host (not db_host)
    - --api-timeout → api.timeout (not api_timeout)

    Example:
        >>> # Command line: python app.py --host 0.0.0.0 --port 9000 --debug
        >>> source = CLI()
        >>> source.load()
        {'host': '0.0.0.0', 'port': 9000, 'debug': True}

        >>> # Command line: python app.py --db-host localhost --db-port 5432
        >>> source = CLI()
        >>> source.load()
        {'db.host': 'localhost', 'db.port': 5432}
    """

    def __init__(
        self,
        argv: Optional[List[str]] = None,
        model: Optional[type] = None,
        prefix: str = "--",
    ):
        """Initialize CLI source.

        Args:
            argv: Command-line arguments (default: sys.argv[1:])
            model: Optional dataclass model for type inference
            prefix: Argument prefix (default: "--")
        """
        self._argv = argv
        self._model = model
        self._prefix = prefix

    @property
    def name(self) -> str:
        """Return source name."""
        return "cli"

    def _get_field_types(self) -> dict[str, type]:
        """Get field types from model if available.

        Returns a flat dict with dot-notation keys for nested fields.
        Example: {"host": str, "db.host": str, "db.port": int}
        """
        if not self._model:
            return {}

        from dataclasses import fields, is_dataclass

        if not is_dataclass(self._model):
            return {}

        result = {}
        for field in fields(self._model):
            if is_dataclass(field.type):
                # Recursively get nested field types
                nested_fields = fields(field.type)
                for nested_field in nested_fields:
                    nested_key = f"{field.name}.{nested_field.name}"
                    result[nested_key] = nested_field.type
            else:
                # Flat field
                result[field.name] = field.type
        return result

    def load(self) -> Mapping[str, Any]:
        """Load configuration from command-line arguments.

        Returns:
            A mapping of normalized keys (using dot notation) to their values.
            Keys are normalized: underscores are converted to dots for nested structure.
            Example: --db-host → db.host
        """
        field_types = self._get_field_types()
        parser = argparse.ArgumentParser(allow_abbrev=False)

        # Build mapping: normalized_key (dot notation) -> argparse dest key
        # For nested keys like "db.host", we use "db_host" as argparse dest
        key_mapping = {}  # normalized_key -> argparse_dest_key

        # Add arguments based on model fields
        for field_key, field_type in field_types.items():
            # Normalize field key using unified rules
            normalized_key = normalize_key(field_key)
            # Convert normalized key to argument names: support both - and _
            arg_name_hyphen = normalized_key.replace(".", "-").replace("_", "-")
            arg_name_underscore = normalized_key.replace(".", "_")
            # Use underscore for argparse dest (argparse doesn't like dots)
            argparse_dest = normalized_key.replace(".", "_")
            key_mapping[normalized_key] = argparse_dest

            try:
                if field_type == bool:
                    # Boolean flags: --flag and --no-flag (support both - and _)
                    parser.add_argument(
                        f"--{arg_name_hyphen}",
                        action="store_true",
                        default=None,
                        dest=argparse_dest,
                    )
                    if arg_name_hyphen != arg_name_underscore:
                        parser.add_argument(
                            f"--{arg_name_underscore}",
                            action="store_true",
                            default=None,
                            dest=argparse_dest,
                        )
                    parser.add_argument(
                        f"--no-{arg_name_hyphen}",
                        dest=argparse_dest,
                        action="store_false",
                        default=None,
                    )
                    if arg_name_hyphen != arg_name_underscore:
                        parser.add_argument(
                            f"--no-{arg_name_underscore}",
                            dest=argparse_dest,
                            action="store_false",
                            default=None,
                        )
                else:
                    # Use a wrapper to handle type conversion errors gracefully
                    def make_type_converter(ftype):
                        def converter(value):
                            try:
                                return ftype(value)
                            except (ValueError, TypeError):
                                # If conversion fails, return as string
                                return value

                        return converter

                    parser.add_argument(
                        f"--{arg_name_hyphen}",
                        type=make_type_converter(field_type),
                        default=None,
                        dest=argparse_dest,
                    )
                    if arg_name_hyphen != arg_name_underscore:
                        parser.add_argument(
                            f"--{arg_name_underscore}",
                            type=make_type_converter(field_type),
                            default=None,
                            dest=argparse_dest,
                        )
            except Exception:
                # If adding argument fails, skip it
                pass

        # Parse only known arguments to avoid errors
        argv = self._argv if self._argv is not None else sys.argv[1:]
        args, _ = parser.parse_known_args(argv)

        # Convert to dict with normalized keys
        result = {}
        for normalized_key, argparse_dest in key_mapping.items():
            value = getattr(args, argparse_dest, None)
            if value is not None:
                result[normalized_key] = value

        return result

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<CLI(prefix={self._prefix!r})>"
