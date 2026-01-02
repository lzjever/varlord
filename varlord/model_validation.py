"""
Model and configuration structure validation.

This module provides validation functions for:
- Model definitions (checking required/optional metadata)
- Configuration structure (checking required fields are present)

For value validation (e.g., validate_port, validate_email), see varlord.validators.
"""

from __future__ import annotations
from typing import Type, Any, Dict, List, get_origin, get_args, Union
from varlord.metadata import get_all_fields_info
from varlord.sources.base import Source


class VarlordError(Exception):
    """Base exception for varlord errors."""

    pass


class ModelDefinitionError(VarlordError):
    """Raised when model definition is invalid.

    This error is raised when a field is missing required/optional metadata,
    has both required and optional, or uses disallowed type annotations like Optional[T].
    """

    def __init__(self, field_name: str, model_name: str, reason: str = "missing_metadata"):
        """Initialize ModelDefinitionError.

        Args:
            field_name: Name of the field with the issue
            model_name: Name of the model class
            reason: Reason for the error ("missing_metadata", "conflicting_metadata", or "optional_type")
        """
        self.field_name = field_name
        self.model_name = model_name
        self.reason = reason

        if reason == "optional_type":
            message = (
                f"Field '{field_name}' in model '{model_name}' uses Optional[T] type annotation, "
                f"which is not allowed. Use explicit metadata instead:\n"
                f"  Instead of: field_name: Optional[str] = field(...)\n"
                f"  Use: field_name: str = field(metadata={{'optional': True}}, ...)\n"
                f"  Or: field_name: str = field(metadata={{'required': True}}, ...)"
            )
        elif reason == "conflicting_metadata":
            message = (
                f"Field '{field_name}' in model '{model_name}' has both 'required' and 'optional' "
                f"in metadata, which is not allowed. Use exactly one:\n"
                f"  field(metadata={{'required': True}})  # For required fields\n"
                f"  field(metadata={{'optional': True}})   # For optional fields"
            )
        else:  # missing_metadata
            message = (
                f"Field '{field_name}' in model '{model_name}' must have "
                f"exactly one of 'required' or 'optional' in metadata. "
                f"Example: field(metadata={{'required': True}}) or "
                f"field(metadata={{'optional': True}})"
            )
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
    ):
        """Initialize RequiredFieldError.

        Args:
            missing_fields: List of normalized keys of missing required fields
            model_name: Name of the model class
            sources: List of sources (for generating help examples)
            show_source_help: Whether to include source mapping help in error message
        """
        self.missing_fields = missing_fields
        self.model_name = model_name
        self.sources = sources
        self.show_source_help = show_source_help

        message = self._format_error_message()
        super().__init__(message)

    def _format_error_message(self) -> str:
        """Format error message with missing fields and source help."""
        lines = [
            f"Required fields are missing in model '{self.model_name}':",
            "",
        ]

        # List missing fields
        for field_key in self.missing_fields:
            lines.append(f"  - {field_key}")

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
    """Validate that all fields in model have explicit required/optional metadata
    and do not use Optional[T] type annotations.

    Args:
        model: Dataclass model to validate

    Raises:
        ModelDefinitionError: If any field is missing required/optional metadata
            or uses Optional[T] type annotation

    Example:
        >>> @dataclass
        ... class Config:
        ...     api_key: str = field()  # Missing metadata
        >>> validate_model_definition(Config)
        ModelDefinitionError: Field 'api_key' in model 'Config' must have...

        >>> from typing import Optional
        >>> @dataclass
        ... class Config:
        ...     api_key: Optional[str] = field(metadata={"optional": True})  # Optional type not allowed
        >>> validate_model_definition(Config)
        ModelDefinitionError: Field 'api_key' in model 'Config' uses Optional[T]...
    """
    if not hasattr(model, "__name__"):
        model_name = str(model)
    else:
        model_name = model.__name__

    # Get field information from metadata module
    from dataclasses import fields, is_dataclass

    if not is_dataclass(model):
        return

    for field_obj in fields(model):
        # Check for Optional[T] type annotation
        if _is_optional_type(field_obj.type):
            from varlord.sources.base import normalize_key

            normalized_key = normalize_key(field_obj.name)
            raise ModelDefinitionError(normalized_key, model_name, reason="optional_type")

    # Check metadata requirements
    field_infos = get_all_fields_info(model)
    for field_info in field_infos:
        # Check if field has both required and optional (conflict)
        if field_info.required and field_info.optional:
            raise ModelDefinitionError(
                field_info.normalized_key, model_name, reason="conflicting_metadata"
            )
        # Check if field has neither required nor optional (missing)
        if not field_info.required and not field_info.optional:
            raise ModelDefinitionError(
                field_info.normalized_key, model_name, reason="missing_metadata"
            )


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
        ...     api_key: str = field(metadata={"required": True})
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
    for field_info in field_infos:
        if field_info.required:
            # Check if key exists in config_dict
            if field_info.normalized_key not in config_dict:
                missing_fields.append(field_info.normalized_key)

    # Raise error if any required fields are missing
    if missing_fields:
        raise RequiredFieldError(
            missing_fields=missing_fields,
            model_name=model_name,
            sources=sources,
            show_source_help=show_source_help,
        )
