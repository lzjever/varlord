"""
Command-line argument source.

Loads configuration from command-line arguments using argparse.
Only parses arguments for fields defined in the model.
"""

from __future__ import annotations
import sys
import argparse
from typing import Mapping, Any, Optional, List, Type

from varlord.sources.base import Source
from varlord.metadata import get_all_field_keys, get_all_fields_info


class CLI(Source):
    """Source that loads configuration from command-line arguments.

    Uses argparse to parse command-line arguments. Only adds arguments for
    fields defined in the model. Model is required and will be auto-injected by Config.

    Supports:
    - Automatic type inference from model fields
    - Boolean flags (--flag / --no-flag)
    - Nested keys via --db-host style arguments (maps to db.host)
    - Help text from field metadata
    - Required arguments from field metadata

    Keys are normalized to dot notation for consistency with other sources:
    - --db-host → db.host (not db_host)
    - --api-timeout → api.timeout (not api_timeout)

    Example:
        >>> @dataclass
        ... class Config:
        ...     host: str = field(metadata={"required": True})
        >>> # Command line: python app.py --host 0.0.0.0
        >>> source = CLI(model=Config)
        >>> source.load()
        {'host': '0.0.0.0'}
    """

    def __init__(
        self,
        model: Optional[Type[Any]] = None,
        argv: Optional[List[str]] = None,
    ):
        """Initialize CLI source.

        Args:
            model: Model to filter CLI arguments.
                  Only arguments that map to model fields will be parsed.
                  Model is required and will be auto-injected by Config.
            argv: Command-line arguments (default: sys.argv[1:])
        """
        super().__init__(model=model)
        self._argv = argv

    @property
    def name(self) -> str:
        """Return source name."""
        return "cli"

    def load(self) -> Mapping[str, Any]:
        """Load configuration from command-line arguments, filtered by model fields.

        Returns:
            A mapping of normalized keys (using dot notation) to their values.
            Only includes arguments for model fields.

        Raises:
            ValueError: If model is not provided
        """
        if not self._model:
            raise ValueError("CLI source requires model (should be auto-injected by Config)")

        # Get all valid field keys and info from model
        valid_keys = get_all_field_keys(self._model)
        field_info_map = {info.normalized_key: info for info in get_all_fields_info(self._model)}

        parser = argparse.ArgumentParser(allow_abbrev=False)
        key_mapping = {}  # normalized_key -> argparse_dest_key

        # Only add arguments for model fields
        for normalized_key in valid_keys:
            if normalized_key not in field_info_map:
                continue

            field_info = field_info_map[normalized_key]
            field_type = field_info.type

            # Convert normalized key to argument names
            arg_name_hyphen = normalized_key.replace(".", "-").replace("_", "-")
            argparse_dest = normalized_key.replace(".", "_")
            key_mapping[normalized_key] = argparse_dest

            # Get help text from metadata
            help_text = field_info.help or field_info.description or ""
            required = field_info.required

            try:
                if field_type == bool:
                    # Boolean flags: --flag and --no-flag
                    parser.add_argument(
                        f"--{arg_name_hyphen}",
                        action="store_true",
                        default=None,
                        dest=argparse_dest,
                        help=help_text,
                        required=required,
                    )
                    parser.add_argument(
                        f"--no-{arg_name_hyphen}",
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
                        help=help_text,
                        required=required,
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
        return "<CLI()>"
