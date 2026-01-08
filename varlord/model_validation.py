"""
Model and configuration structure validation.

This module provides validation functions for:
- Model definitions (checking required/optional metadata)
- Configuration structure (checking required fields are present)

For value validation (e.g., validate_port, validate_email), see varlord.validators.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin

from varlord.metadata import get_all_fields_info
from varlord.sources.base import Source


class VarlordError(Exception):
    """Base exception for varlord errors."""

    pass


class ModelDefinitionError(VarlordError):
    """Raised when model definition is invalid.

    Currently no validation errors are raised - Optional[T] types are supported
    and automatically recognized as optional fields.
    """

    def __init__(self, field_name: str, model_name: str, reason: str = "invalid"):
        """Initialize ModelDefinitionError.

        Args:
            field_name: Name of the field with the issue
            model_name: Name of the model class
            reason: Reason for the error
        """
        self.field_name = field_name
        self.model_name = model_name
        self.reason = reason

        message = f"Field '{field_name}' in model '{model_name}' has an invalid definition."
        super().__init__(message)


class RequiredFieldError(VarlordError):
    """Raised when required fields are missing from configuration.

    This error is raised when a required field is not present in the
    merged configuration dictionary.
    """

    def __init__(
        self,
        missing_fields: List[str],
        model_name: str,
        sources: List[Source],
        show_source_help: bool = True,
        field_infos: Optional[List[Any]] = None,
        config_dict: Optional[Dict[str, Any]] = None,
    ):
        """Initialize RequiredFieldError.

        Args:
            missing_fields: List of normalized keys of missing required fields
            model_name: Name of the model class
            sources: List of sources (for generating help examples)
            show_source_help: Whether to include source mapping help in error message
            field_infos: Optional list of FieldInfo objects for missing fields
            config_dict: Optional configuration dictionary for enhanced error messages
        """
        self.missing_fields = missing_fields
        self.model_name = model_name
        self.sources = sources
        self.show_source_help = show_source_help
        self.field_infos = field_infos or []
        self._config_dict = config_dict

        message = self._format_error_message()
        super().__init__(message)

    def _format_error_message(self) -> str:
        """Format error message with missing fields and source help."""
        lines = [
            f"Required fields are missing in model '{self.model_name}':",
            "",
        ]

        # Create a mapping from field key to field info for quick lookup
        field_info_map = {
            field_info.normalized_key: field_info
            for field_info in self.field_infos
            if field_info.normalized_key in self.missing_fields
        }

        # Get config_dict if available (for checking child fields)
        config_dict = getattr(self, "_config_dict", None)

        # List missing fields with descriptions if available
        for field_key in self.missing_fields:
            field_info = field_info_map.get(field_key)
            if field_info and field_info.description:
                lines.append(f"  - {field_key}: {field_info.description}")
            else:
                lines.append(f"  - {field_key}")

            # Check if child fields exist for nested dataclass fields
            if config_dict is not None and field_info:
                from dataclasses import is_dataclass

                if is_dataclass(field_info.type):
                    prefix = field_key + "."
                    child_fields = [k for k in config_dict.keys() if k.startswith(prefix)]
                    if child_fields:
                        lines.append(f"    Note: Child fields exist: {', '.join(child_fields[:5])}")
                        if len(child_fields) > 5:
                            lines.append(f"    ... and {len(child_fields) - 5} more")
                        lines.append(
                            "    This may indicate a validation logic issue with nested dataclass fields."
                        )

        # Add source help if enabled
        if self.show_source_help:
            try:
                from varlord.source_help import format_source_help

                help_text = format_source_help(self.sources, self.missing_fields)
                if help_text:
                    lines.append("")
                    lines.append(help_text)
            except ImportError:
                # source_help module not available yet, skip
                pass

        return "\n".join(lines)


def _is_optional_type(field_type: Type[Any]) -> bool:
    """Check if a type is Optional[T] or Union[T, None].

    Args:
        field_type: Type to check

    Returns:
        True if the type is Optional[T] or Union[T, None]
    """
    origin = get_origin(field_type)
    if origin is None:
        return False

    # Check for Optional[T] (which is Union[T, None])
    if origin is Union:
        args = get_args(field_type)
        # Optional[T] is Union[T, None], so check if None is in args
        if type(None) in args:
            return True

    return False


def validate_model_definition(model: Type[Any]) -> None:
    """Validate model definition.

    Fields are determined as required/optional based on:
    1. Type annotation: Optional[T] → optional
    2. Default value: has default or default_factory → optional
    3. Otherwise → required

    Args:
        model: Dataclass model to validate

    Example:
        >>> @dataclass
        ... class Config:
        ...     api_key: str = field()  # Required (no default, not Optional)
        ...     timeout: Optional[int] = field()  # Optional (Optional type)
        ...     host: str = field(default="localhost")  # Optional (has default)
        >>> validate_model_definition(Config)  # OK
    """
    # Currently no validation errors - Optional[T] types are supported
    # and automatically recognized as optional fields
    pass


def validate_config(
    model: Type[Any],
    config_dict: Dict[str, Any],
    sources: List[Source],
    show_source_help: bool = True,
) -> None:
    """Validate that all required fields exist in config_dict.

    Args:
        model: Dataclass model to validate against
        config_dict: Configuration dictionary to validate
        sources: List of sources (for generating help examples)
        show_source_help: Whether to include source mapping help in error message

    Raises:
        RequiredFieldError: If any required field is missing from config_dict

    Note:
        Only checks if keys exist in config_dict. Values can be None, empty string,
        or empty collections - these are all considered valid.

    Example:
        >>> @dataclass
        ... class Config:
        ...     api_key: str = field()  # Required by default
        >>> validate_config(Config, {}, [])
        RequiredFieldError: Required fields are missing...
    """
    if not hasattr(model, "__name__"):
        model_name = str(model)
    else:
        model_name = model.__name__

    # Get all field info
    field_infos = get_all_fields_info(model)

    # Find missing required fields
    missing_fields: List[str] = []
    missing_field_infos: List[Any] = []
    for field_info in field_infos:
        if field_info.required:
            # Check if key exists in config_dict
            if field_info.normalized_key in config_dict:
                continue  # Field exists, skip

            # For nested dataclass fields, check if any child field exists
            from dataclasses import is_dataclass

            if is_dataclass(field_info.type):
                # Check if any child field exists
                prefix = field_info.normalized_key + "."
                has_child = any(key.startswith(prefix) for key in config_dict.keys())
                if has_child:
                    continue  # Parent field is satisfied by child fields

            # Field is missing
            missing_fields.append(field_info.normalized_key)
            missing_field_infos.append(field_info)

    # Raise error if any required fields are missing
    if missing_fields:
        raise RequiredFieldError(
            missing_fields=missing_fields,
            model_name=model_name,
            sources=sources,
            show_source_help=show_source_help,
            field_infos=missing_field_infos,
            config_dict=config_dict,
        )
