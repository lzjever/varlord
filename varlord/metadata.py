"""
Field metadata extraction and utilities.

Provides functions to extract field information from dataclass models,
including metadata, types, defaults, and normalized keys.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Any, List, Optional, Set, Type

from varlord.sources.base import normalize_key


@dataclass
class FieldInfo:
    """Information about a dataclass field.

    Attributes:
        name: Field name (e.g., "host" or "db" for nested)
        normalized_key: Normalized key in dot notation (e.g., "host" or "db.host")
        type: Field type
        default: Default value (or MISSING if no default)
        default_factory: Default factory (or MISSING if no factory)
        required: True if field is required (from metadata)
        optional: True if field is optional (from metadata)
        description: Field description from metadata
        help: Help text from metadata (for CLI)
    """

    name: str
    normalized_key: str
    type: Type[Any]
    default: Any
    default_factory: Any
    required: bool
    optional: bool
    description: Optional[str]
    help: Optional[str]


def get_all_fields_info(model: Type[Any], prefix: str = "") -> List[FieldInfo]:
    """Extract field information from model (recursive for nested dataclasses).

    Args:
        model: Dataclass model to extract fields from
        prefix: Prefix for nested fields (e.g., "db" for db.host)

    Returns:
        List of FieldInfo objects for all fields (including nested)

    Example:
        >>> @dataclass
        ... class DBConfig:
        ...     host: str = field()  # Required by default
        >>> @dataclass
        ... class AppConfig:
        ...     api_key: str = field()  # Required by default
        ...     db: DBConfig = field()  # Required by default
        >>> fields = get_all_fields_info(AppConfig)
        >>> [f.normalized_key for f in fields]
        ['api_key', 'db.host']
    """
    if not is_dataclass(model):
        return []

    result: List[FieldInfo] = []

    for field in fields(model):
        # Normalize field name
        normalized_name = normalize_key(field.name)
        normalized_key = f"{prefix}.{normalized_name}" if prefix else normalized_name

        # Extract metadata
        metadata = field.metadata if hasattr(field, "metadata") else {}
        description = metadata.get("description")
        help_text = metadata.get("help")

        # Get default and default_factory
        # Use ... as sentinel for missing values (consistent with dataclass behavior)
        from dataclasses import _MISSING_TYPE

        default = (
            field.default
            if field.default is not ... and not isinstance(field.default, _MISSING_TYPE)
            else ...
        )
        default_factory = (
            field.default_factory
            if field.default_factory is not ...
            and not isinstance(field.default_factory, _MISSING_TYPE)
            else ...
        )

        # Determine required/optional based on type annotation and default value
        # 1. If type is Optional[T] → optional
        # 2. If has default or default_factory → optional
        # 3. Otherwise → required
        from typing import Union, get_args, get_origin

        is_optional_type = False
        origin = get_origin(field.type)
        if origin is Union:
            args = get_args(field.type)
            if type(None) in args:
                is_optional_type = True

        has_default = default is not ... or default_factory is not ...
        optional = is_optional_type or has_default
        required = not optional

        # Create FieldInfo
        field_info = FieldInfo(
            name=field.name,
            normalized_key=normalized_key,
            type=field.type,
            default=default,
            default_factory=default_factory,
            required=required,
            optional=optional,
            description=description,
            help=help_text,
        )
        result.append(field_info)

        # Recursively process nested dataclasses
        if is_dataclass(field.type):
            nested_fields = get_all_fields_info(field.type, prefix=normalized_key)
            result.extend(nested_fields)

    return result


def get_all_field_keys(model: Type[Any]) -> Set[str]:
    """Extract all normalized field keys from model (recursive).

    Args:
        model: Dataclass model to extract keys from

    Returns:
        Set of normalized keys (e.g., {"host", "db.host", "db.port"})

    Example:
        >>> @dataclass
        ... class DBConfig:
        ...     host: str
        ...     port: int
        >>> @dataclass
        ... class AppConfig:
        ...     api_key: str
        ...     db: DBConfig
        >>> keys = get_all_field_keys(AppConfig)
        >>> keys == {"api_key", "db.host", "db.port"}
        True
    """
    field_infos = get_all_fields_info(model)
    return {field_info.normalized_key for field_info in field_infos}


def get_field_info(model: Type[Any], field_name: str) -> Optional[FieldInfo]:
    """Get information about a specific field.

    Args:
        model: Dataclass model
        field_name: Field name (can be nested, e.g., "db.host")

    Returns:
        FieldInfo if found, None otherwise
    """
    all_fields = get_all_fields_info(model)
    for field_info in all_fields:
        if field_info.normalized_key == normalize_key(field_name):
            return field_info
    return None
