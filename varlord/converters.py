"""
Type converters for configuration values.

Handles conversion of string values (from env vars, CLI, etc.) to
appropriate Python types based on model field types.
"""

from __future__ import annotations

import json
from typing import Any, Optional, Type, get_args, get_origin

try:
    from varlord.logging import log_type_conversion
except ImportError:
    # Fallback if logging not available
    def log_type_conversion(*args, **kwargs):
        pass


def convert_value(value: Any, target_type: Type[Any], key: Optional[str] = None) -> Any:
    """Convert a value to the target type.

    Args:
        value: Value to convert
        target_type: Target type
        key: Optional configuration key for logging

    Returns:
        Converted value

    Note:
        Handles common types: int, float, bool, str, and Optional types.
        For complex types, returns value as-is.
    """
    # If already the right type, return as-is
    if isinstance(value, target_type):
        return value

    # Handle Optional types and Union types
    origin = get_origin(target_type)
    if origin is not None:
        # Handle Union types (including Optional[T] which is Union[T, None])
        args = get_args(target_type)
        if len(args) > 0:
            # Filter out None type
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                # Try each type in order until one succeeds
                for inner_type in non_none_types:
                    try:
                        # Check if value is already the right type
                        if isinstance(value, inner_type):
                            return value
                        # Try to convert
                        converted = convert_value(value, inner_type, key=key)
                        # If conversion succeeded (no exception), return it
                        return converted
                    except (ValueError, TypeError):
                        # Try next type
                        continue
                # If all conversions failed, return original value
                return value

    # Handle None
    if value is None:
        return None

    # Convert based on target type
    if target_type is bool:
        result = _convert_bool(value)
    elif target_type is int:
        result = _convert_int(value)
    elif target_type is float:
        result = _convert_float(value)
    elif target_type is str:
        result = str(value)
    else:
        # For other types, try JSON parsing if it's a string
        if isinstance(value, str):
            try:
                result = json.loads(value)
            except (ValueError, TypeError):
                result = value
        else:
            result = value

    # Log conversion if key provided
    if key:
        log_type_conversion(key, value, target_type, result)

    return result


def _convert_bool(value: Any) -> bool:
    """Convert value to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lower = value.lower()
        if lower in ("true", "1", "yes", "on"):
            return True
        if lower in ("false", "0", "no", "off", ""):
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return bool(value)


def _convert_int(value: Any) -> int:
    """Convert value to integer."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            # Try float first, then int
            try:
                return int(float(value))
            except ValueError:
                raise ValueError(f"Cannot convert {value!r} to int")
    raise TypeError(f"Cannot convert {type(value)} to int")


def _convert_float(value: Any) -> float:
    """Convert value to float."""
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Cannot convert {value!r} to float")
    raise TypeError(f"Cannot convert {type(value)} to float")
