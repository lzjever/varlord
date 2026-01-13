"""
Command-line argument source.

Loads configuration from command-line arguments using argparse.
Only parses arguments for fields defined in the model.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, List, Mapping, Optional, Type

from varlord.metadata import get_all_field_keys, get_all_fields_info
from varlord.sources.base import Source


def normalized_key_to_cli_arg(normalized_key: str) -> str:
    """Convert normalized key to CLI argument format.

    Mapping rules:
    - Dots (.) become double dashes (--)
    - Underscores (_) become single dashes (-)

    Examples:
    - "host" -> "host"
    - "k8s_pod_name" -> "k8s-pod-name"
    - "db.host" -> "db--host"
    - "aaa.bbb.ccc_dd" -> "aaa--bbb--ccc-dd"
    """
    # Replace dots with double dashes, underscores with single dashes
    return normalized_key.replace(".", "--").replace("_", "-")


def cli_arg_to_normalized_key(cli_arg: str) -> str:
    """Convert CLI argument to normalized key.

    Mapping rules:
    - Double dashes (--) become dots (.)
    - Single dashes (-) become underscores (_)

    Examples:
    - "host" -> "host"
    - "k8s-pod-name" -> "k8s_pod_name"
    - "db--host" -> "db.host"
    - "aaa--bbb--ccc-dd" -> "aaa.bbb.ccc_dd"
    """
    # Split by double dashes first
    parts = cli_arg.split("--")
    # Replace single dashes with underscores in each part
    normalized_parts = [part.replace("-", "_") for part in parts]
    # Join with dots
    return ".".join(normalized_parts)


class CLI(Source):
    """Source that loads configuration from command-line arguments.

    Uses argparse to parse command-line arguments. Only adds arguments for
    fields defined in the model. Model is required and will be auto-injected by Config.

    Mapping rules:
    - Double dashes (--) in CLI arguments become dots (.) in normalized keys
    - Single dashes (-) in CLI arguments become underscores (_) in normalized keys

    Examples:
    - --host → host
    - --k8s-pod-name → k8s_pod_name
    - --db--host → db.host
    - --aaa--bbb--ccc-dd → aaa.bbb.ccc_dd

    Supports:
    - Automatic type inference from model fields
    - Boolean flags (--flag / --no-flag)
    - Nested keys via double dashes (--db--host maps to db.host)
    - Help text from field metadata

    Example:
        >>> @dataclass
        ... class Config:
        ...     host: str = field()
        >>> # Command line: python app.py --host 0.0.0.0
        >>> source = CLI(model=Config)
        >>> source.load()
        {'host': '0.0.0.0'}
    """

    def __init__(
        self,
        model: Optional[Type[Any]] = None,
        argv: Optional[List[str]] = None,
        source_id: Optional[str] = None,
    ):
        """Initialize CLI source.

        Args:
            model: Optional model to filter CLI arguments.
                  Only arguments that map to model fields will be parsed.
                  If None, model will be auto-injected by Config when used in Config.
                  If provided, this model will be used (allows override).
            argv: Command-line arguments (default: sys.argv[1:])
            source_id: Optional unique identifier (default: "cli")

        Note:
            - Recommended: Omit model parameter when used in Config (auto-injected).
            - Advanced: Provide model explicitly if using source independently.
        """
        super().__init__(model=model, source_id=source_id or "cli")
        self._argv = argv

    @property
    def name(self) -> str:
        """Return source name."""
        return "cli"

    def _generate_id(self) -> str:
        """Generate unique ID for CLI source."""
        return "cli"

    def load(self) -> Mapping[str, Any]:
        """Load configuration from command-line arguments, filtered by model fields.

        Returns:
            A mapping of normalized keys (using dot notation) to their values.
            Only includes arguments for model fields.

        Raises:
            ValueError: If model is not provided
        """
        self._load_status = "unknown"
        self._load_error = None

        try:
            if not self._model:
                raise ValueError(
                    "CLI source requires model. "
                    "When used in Config, model is auto-injected. "
                    "When used independently, provide model explicitly: CLI(model=AppConfig)"
                )

            valid_keys = get_all_field_keys(self._model)
            field_info_map = {
                info.normalized_key: info for info in get_all_fields_info(self._model)
            }

            parser = argparse.ArgumentParser(allow_abbrev=False, add_help=False)

            for normalized_key in valid_keys:
                if normalized_key not in field_info_map:
                    continue

                field_info = field_info_map[normalized_key]
                field_type = field_info.type

                cli_arg_name = normalized_key_to_cli_arg(normalized_key)
                argparse_dest = normalized_key.replace(".", "_")

                try:
                    if field_type is bool:
                        parser.add_argument(
                            f"--{cli_arg_name}",
                            action="store_true",
                            default=None,
                            dest=argparse_dest,
                            required=False,
                        )
                        parser.add_argument(
                            f"--no-{cli_arg_name}",
                            dest=argparse_dest,
                            action="store_false",
                            default=None,
                        )
                    else:

                        def make_type_converter(ftype):
                            def converter(value):
                                try:
                                    return ftype(value)
                                except (ValueError, TypeError):
                                    return value

                            return converter

                        parser.add_argument(
                            f"--{cli_arg_name}",
                            type=make_type_converter(field_type),
                            default=None,
                            dest=argparse_dest,
                            required=False,
                        )
                except Exception as e:
                    import logging

                    logging.debug(f"Failed to add argument for {normalized_key}: {e}")

            argv = self._argv if self._argv is not None else sys.argv[1:]
            filtered_argv = [arg for arg in argv if arg not in ("--help", "-h")]

            try:
                args, _ = parser.parse_known_args(filtered_argv)
            except SystemExit:
                self._load_status = "success"
                return {}

            result = {}
            for normalized_key in valid_keys:
                if normalized_key not in field_info_map:
                    continue
                argparse_dest = normalized_key.replace(".", "_")
                value = getattr(args, argparse_dest, None)
                if value is not None:
                    result[normalized_key] = value

            self._load_status = "success"
            return result
        except Exception as e:
            self._load_status = "failed"
            self._load_error = str(e)
            raise

    def format_help(self, prog: Optional[str] = None) -> str:
        """Generate help text for all CLI arguments based on model fields.

        This method generates help text without using argparse's built-in help,
        giving varlord complete control over the help output format.

        Args:
            prog: Program name (default: script name from sys.argv[0])

        Returns:
            Formatted help text string
        """
        if not self._model:
            return ""

        if prog is None:
            import os

            prog = os.path.basename(sys.argv[0]) if sys.argv else "app.py"

        # Get all field info
        field_infos = get_all_fields_info(self._model)

        # Group fields by category (required vs optional)
        required_fields = []
        optional_fields = []

        for field_info in field_infos:
            arg_name = normalized_key_to_cli_arg(field_info.normalized_key)
            help_text = field_info.help or field_info.description or ""
            type_name = (
                field_info.type.__name__
                if hasattr(field_info.type, "__name__")
                else str(field_info.type)
            )

            default_str = ""
            if field_info.required:
                default_str = " (required)"
            elif field_info.default is not ...:
                if field_info.default is None:
                    default_str = " (default: None)"
                elif isinstance(field_info.default, str):
                    default_str = f" (default: '{field_info.default}')"
                else:
                    default_str = f" (default: {field_info.default})"
            elif field_info.default_factory is not ...:
                default_str = " (has default factory)"

            field_entry = {
                "name": arg_name,
                "type": type_name,
                "help": help_text,
                "default": default_str,
                "normalized_key": field_info.normalized_key,
            }

            if field_info.required:
                required_fields.append(field_entry)
            else:
                optional_fields.append(field_entry)

        # Build help text with improved formatting
        lines = [f"Usage: {prog} [OPTIONS]"]
        lines.append("")

        if required_fields:
            lines.append("Required Arguments:")
            for field in required_fields:
                arg_line = f"  --{field['name']} {field['type'].upper()}"
                if field["help"]:
                    lines.append(arg_line)
                    lines.append(f"    {field['help']}")
                else:
                    lines.append(arg_line)
            lines.append("")

        if optional_fields:
            lines.append("Optional Arguments:")
            for field in optional_fields:
                arg_line = f"  --{field['name']} {field['type'].upper()}{field['default']}"
                if field["help"]:
                    lines.append(arg_line)
                    lines.append(f"    {field['help']}")
                else:
                    lines.append(arg_line)
            lines.append("")

        bool_fields = [f for f in field_infos if f.type is bool]
        if bool_fields:
            lines.append("Boolean Flags:")
            for field_info in bool_fields:
                arg_name = normalized_key_to_cli_arg(field_info.normalized_key)
                help_text = field_info.help or field_info.description or ""
                flag_line = f"  --{arg_name} / --no-{arg_name}"
                if help_text:
                    lines.append(flag_line)
                    lines.append(f"    {help_text}")
                else:
                    lines.append(flag_line)
            lines.append("")

        return "\n".join(lines)

    def get_field_help(self, field_key: str) -> Optional[str]:
        """Get help text for a specific field.

        Args:
            field_key: Normalized field key (e.g., "docx_path" or "db.host")

        Returns:
            Help text if found, None otherwise
        """
        if not self._model:
            return None

        from varlord.metadata import get_field_info

        field_info = get_field_info(self._model, field_key)
        if field_info:
            return field_info.help or field_info.description
        return None

    def __repr__(self) -> str:
        """Return string representation."""
        return "<CLI()>"
