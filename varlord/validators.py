"""
Value validators for configuration.

This module provides validation functions for configuration values:
- Numeric validators (port, range, positive, etc.)
- String validators (email, URL, IP, domain, etc.)
- Collection validators (list length, dict keys, etc.)
- File/path validators
- Custom validators

For model definition and structure validation, see varlord.model_validation.
"""

from __future__ import annotations

import base64
import json
import re
import uuid
from ipaddress import IPv4Address, IPv6Address, ip_address
from pathlib import Path
from typing import Any, Callable, Optional, Union

try:
    from varlord.logging import log_validation_error
except ImportError:

    def log_validation_error(*args, **kwargs):
        pass


class ValidationError(ValueError):
    """Raised when configuration validation fails."""

    def __init__(self, key: str, value: Any, message: str):
        """Initialize validation error.

        Args:
            key: Configuration key
            value: Invalid value
            message: Error message
        """
        self.key = key
        self.value = value
        self.message = message
        super().__init__(f"Validation failed for '{key}' = {value!r}: {message}")


# ============================================================================
# Basic Validators
# ============================================================================


def validate_range(value: Any, min: Optional[float] = None, max: Optional[float] = None) -> None:
    """Validate that a value is within a range.

    Args:
        value: Value to validate
        min: Minimum value (inclusive)
        max: Maximum value (inclusive)

    Raises:
        ValidationError: If value is out of range

    Example:
        >>> validate_range(50, min=0, max=100)  # OK
        >>> validate_range(150, min=0, max=100)  # Raises ValidationError
    """
    if min is not None and value < min:
        raise ValidationError("value", value, f"must be >= {min}")
    if max is not None and value > max:
        raise ValidationError("value", value, f"must be <= {max}")


def validate_regex(value: str, pattern: str, flags: int = 0) -> None:
    r"""Validate that a string matches a regex pattern.

    Args:
        value: String to validate
        pattern: Regex pattern
        flags: Regex flags

    Raises:
        ValidationError: If value doesn't match pattern

    Example:
        >>> validate_regex("abc123", r'^[a-z]+\d+$')  # OK
        >>> validate_regex("ABC123", r'^[a-z]+\d+$')  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    if not re.match(pattern, value, flags):
        raise ValidationError("value", value, f"must match pattern {pattern!r}")


def validate_choice(value: Any, choices: list[Any]) -> None:
    """Validate that a value is in a list of choices.

    Args:
        value: Value to validate
        choices: List of valid choices

    Raises:
        ValidationError: If value is not in choices

    Example:
        >>> validate_choice("red", ["red", "green", "blue"])  # OK
        >>> validate_choice("yellow", ["red", "green", "blue"])  # Raises ValidationError
    """
    if value not in choices:
        raise ValidationError("value", value, f"must be one of {choices}")


def validate_not_empty(value: Any) -> None:
    """Validate that a value is not empty.

    Args:
        value: Value to validate

    Raises:
        ValidationError: If value is empty

    Example:
        >>> validate_not_empty("hello")  # OK
        >>> validate_not_empty(0)  # OK (0 is not considered empty)
        >>> validate_not_empty(False)  # OK (False is not considered empty)
        >>> validate_not_empty("")  # Raises ValidationError
        >>> validate_not_empty([])  # Raises ValidationError
    """
    # Check for empty collections and empty strings
    # Note: 0 and False are NOT considered empty
    if value is None:
        raise ValidationError("value", value, "must not be empty")
    if isinstance(value, str) and value == "":
        raise ValidationError("value", value, "must not be empty")
    if isinstance(value, (list, dict, tuple, set)) and len(value) == 0:
        raise ValidationError("value", value, "must not be empty")


# ============================================================================
# Numeric Validators
# ============================================================================


def validate_positive(value: Union[int, float]) -> None:
    """Validate that a number is positive (> 0).

    Args:
        value: Number to validate

    Raises:
        ValidationError: If value is not positive

    Example:
        >>> validate_positive(10)  # OK
        >>> validate_positive(-5)  # Raises ValidationError
    """
    if not isinstance(value, (int, float)):
        raise ValidationError("value", value, "must be a number")
    if value <= 0:
        raise ValidationError("value", value, "must be positive (> 0)")


def validate_non_negative(value: Union[int, float]) -> None:
    """Validate that a number is non-negative (>= 0).

    Args:
        value: Number to validate

    Raises:
        ValidationError: If value is negative

    Example:
        >>> validate_non_negative(0)  # OK
        >>> validate_non_negative(10)  # OK
        >>> validate_non_negative(-5)  # Raises ValidationError
    """
    if not isinstance(value, (int, float)):
        raise ValidationError("value", value, "must be a number")
    if value < 0:
        raise ValidationError("value", value, "must be non-negative (>= 0)")


def validate_integer(value: Any) -> None:
    """Validate that a value is an integer.

    Args:
        value: Value to validate

    Raises:
        ValidationError: If value is not an integer

    Example:
        >>> validate_integer(42)  # OK
        >>> validate_integer(42.5)  # Raises ValidationError
    """
    if not isinstance(value, int):
        raise ValidationError("value", value, "must be an integer")


def validate_float(value: Any) -> None:
    """Validate that a value is a float or can be converted to float.

    Args:
        value: Value to validate

    Raises:
        ValidationError: If value is not a float

    Example:
        >>> validate_float(3.14)  # OK
        >>> validate_float(42)  # OK (int can be float)
        >>> validate_float("not a number")  # Raises ValidationError
    """
    if not isinstance(value, (int, float)):
        try:
            float(value)
        except (ValueError, TypeError):
            raise ValidationError("value", value, "must be a float or convertible to float")


def validate_percentage(value: Union[int, float]) -> None:
    """Validate that a number is a valid percentage (0-100).

    Args:
        value: Number to validate

    Raises:
        ValidationError: If value is not in 0-100 range

    Example:
        >>> validate_percentage(50)  # OK
        >>> validate_percentage(150)  # Raises ValidationError
    """
    validate_range(value, min=0, max=100)


def validate_port(value: int) -> None:
    """Validate that a number is a valid port number (1-65535).

    Args:
        value: Port number to validate

    Raises:
        ValidationError: If value is not a valid port

    Example:
        >>> validate_port(8080)  # OK
        >>> validate_port(70000)  # Raises ValidationError
    """
    validate_integer(value)
    validate_range(value, min=1, max=65535)


def validate_greater_than(value: Union[int, float], threshold: Union[int, float]) -> None:
    """Validate that a number is greater than a threshold.

    Args:
        value: Number to validate
        threshold: Threshold value

    Raises:
        ValidationError: If value is not greater than threshold

    Example:
        >>> validate_greater_than(10, 5)  # OK
        >>> validate_greater_than(3, 5)  # Raises ValidationError
    """
    if not isinstance(value, (int, float)):
        raise ValidationError("value", value, "must be a number")
    if value <= threshold:
        raise ValidationError("value", value, f"must be greater than {threshold}")


def validate_less_than(value: Union[int, float], threshold: Union[int, float]) -> None:
    """Validate that a number is less than a threshold.

    Args:
        value: Number to validate
        threshold: Threshold value

    Raises:
        ValidationError: If value is not less than threshold

    Example:
        >>> validate_less_than(3, 5)  # OK
        >>> validate_less_than(10, 5)  # Raises ValidationError
    """
    if not isinstance(value, (int, float)):
        raise ValidationError("value", value, "must be a number")
    if value >= threshold:
        raise ValidationError("value", value, f"must be less than {threshold}")


# ============================================================================
# String Validators
# ============================================================================


def validate_length(
    value: str, min_length: Optional[int] = None, max_length: Optional[int] = None
) -> None:
    """Validate that a string has a length within a range.

    Args:
        value: String to validate
        min_length: Minimum length (inclusive)
        max_length: Maximum length (inclusive)

    Raises:
        ValidationError: If length is out of range

    Example:
        >>> validate_length("hello", min_length=3, max_length=10)  # OK
        >>> validate_length("hi", min_length=3)  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    length = len(value)
    if min_length is not None and length < min_length:
        raise ValidationError("value", value, f"length must be >= {min_length}")
    if max_length is not None and length > max_length:
        raise ValidationError("value", value, f"length must be <= {max_length}")


def validate_email(value: str) -> None:
    """Validate that a string is a valid email address.

    Args:
        value: String to validate

    Raises:
        ValidationError: If value is not a valid email

    Example:
        >>> validate_email("user@example.com")  # OK
        >>> validate_email("invalid-email")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    # RFC 5322 compliant email regex (simplified)
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, value):
        raise ValidationError("value", value, "must be a valid email address")


def validate_url(value: str, require_scheme: bool = True) -> None:
    """Validate that a string is a valid URL.

    Args:
        value: String to validate
        require_scheme: Whether to require http:// or https:// scheme

    Raises:
        ValidationError: If value is not a valid URL

    Example:
        >>> validate_url("https://example.com")  # OK
        >>> validate_url("not-a-url")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    if require_scheme:
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    else:
        pattern = r"^[^\s/$.?#].[^\s]*$"
    if not re.match(pattern, value):
        scheme_msg = " with http:// or https:// scheme" if require_scheme else ""
        raise ValidationError("value", value, f"must be a valid URL{scheme_msg}")


def validate_ipv4(value: str) -> None:
    """Validate that a string is a valid IPv4 address.

    Args:
        value: String to validate

    Raises:
        ValidationError: If value is not a valid IPv4 address

    Example:
        >>> validate_ipv4("192.168.1.1")  # OK
        >>> validate_ipv4("256.1.1.1")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    try:
        addr = ip_address(value)
        if not isinstance(addr, IPv4Address):
            raise ValidationError("value", value, "must be a valid IPv4 address")
    except ValueError:
        raise ValidationError("value", value, "must be a valid IPv4 address")


def validate_ipv6(value: str) -> None:
    """Validate that a string is a valid IPv6 address.

    Args:
        value: String to validate

    Raises:
        ValidationError: If value is not a valid IPv6 address

    Example:
        >>> validate_ipv6("2001:0db8:85a3:0000:0000:8a2e:0370:7334")  # OK
        >>> validate_ipv6("192.168.1.1")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    try:
        addr = ip_address(value)
        if not isinstance(addr, IPv6Address):
            raise ValidationError("value", value, "must be a valid IPv6 address")
    except ValueError:
        raise ValidationError("value", value, "must be a valid IPv6 address")


def validate_ip(value: str) -> None:
    """Validate that a string is a valid IPv4 or IPv6 address.

    Args:
        value: String to validate

    Raises:
        ValidationError: If value is not a valid IP address

    Example:
        >>> validate_ip("192.168.1.1")  # OK
        >>> validate_ip("2001:0db8::1")  # OK
        >>> validate_ip("invalid")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    try:
        ip_address(value)
    except ValueError:
        raise ValidationError("value", value, "must be a valid IPv4 or IPv6 address")


def validate_domain(value: str) -> None:
    """Validate that a string is a valid domain name.

    Args:
        value: String to validate

    Raises:
        ValidationError: If value is not a valid domain

    Example:
        >>> validate_domain("example.com")  # OK
        >>> validate_domain("sub.example.com")  # OK
        >>> validate_domain("invalid..domain")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    # Domain name regex (RFC 1035)
    pattern = r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    if not re.match(pattern, value):
        raise ValidationError("value", value, "must be a valid domain name")


def validate_phone(value: str, country: Optional[str] = None) -> None:
    """Validate that a string is a valid phone number.

    Args:
        value: String to validate
        country: Country code for validation (e.g., "US", "CN"). If None, uses generic pattern.

    Raises:
        ValidationError: If value is not a valid phone number

    Example:
        >>> validate_phone("+1-555-123-4567")  # OK
        >>> validate_phone("13800138000")  # OK (Chinese mobile)
        >>> validate_phone("invalid")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")

    # Remove common separators and check for + prefix
    cleaned = re.sub(r"[\s\-\(\)]", "", value)
    has_plus = cleaned.startswith("+")
    if has_plus:
        cleaned = cleaned[1:]  # Remove + for pattern matching

    if country == "CN":
        # Chinese mobile: 11 digits starting with 1
        pattern = r"^1[3-9]\d{9}$"
        if not re.match(pattern, cleaned):
            raise ValidationError(
                "value", value, "must be a valid Chinese mobile number (11 digits starting with 1)"
            )
    elif country == "US":
        # US phone: 10 digits, optionally with +1 prefix
        # Remove country code if present
        if has_plus and cleaned.startswith("1") and len(cleaned) == 11:
            cleaned = cleaned[1:]  # Remove country code
        # US phone format: NXX-NXX-XXXX where N is 2-9
        if len(cleaned) == 10:
            pattern = r"^[2-9]\d{2}[2-9]\d{2}\d{4}$"
            if not re.match(pattern, cleaned):
                raise ValidationError(
                    "value",
                    value,
                    "must be a valid US phone number (10 digits, area code cannot start with 0 or 1)",
                )
        else:
            raise ValidationError("value", value, "must be a valid US phone number (10 digits)")
    else:
        # Generic: 7-15 digits, optionally with + prefix
        pattern = r"^\d{7,15}$"
        if not re.match(pattern, cleaned):
            raise ValidationError("value", value, "must be a valid phone number (7-15 digits)")


def validate_uuid(value: str, version: Optional[int] = None) -> None:
    """Validate that a string is a valid UUID.

    Args:
        value: String to validate
        version: UUID version (1-5). If None, accepts any version.

    Raises:
        ValidationError: If value is not a valid UUID

    Example:
        >>> validate_uuid("550e8400-e29b-41d4-a716-446655440000")  # OK
        >>> validate_uuid("invalid-uuid")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    try:
        parsed = uuid.UUID(value)
        if version is not None and parsed.version != version:
            raise ValidationError("value", value, f"must be a valid UUID version {version}")
    except (ValueError, AttributeError):
        raise ValidationError("value", value, "must be a valid UUID")


def validate_base64(value: str) -> None:
    """Validate that a string is valid Base64 encoded data.

    Args:
        value: String to validate

    Raises:
        ValidationError: If value is not valid Base64

    Example:
        >>> validate_base64("SGVsbG8gV29ybGQ=")  # OK
        >>> validate_base64("invalid!")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    try:
        base64.b64decode(value, validate=True)
    except Exception:
        raise ValidationError("value", value, "must be valid Base64 encoded data")


def validate_json_string(value: str) -> None:
    """Validate that a string is valid JSON.

    Args:
        value: String to validate

    Raises:
        ValidationError: If value is not valid JSON

    Example:
        >>> validate_json_string('{"key": "value"}')  # OK
        >>> validate_json_string("invalid json")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    try:
        json.loads(value)
    except json.JSONDecodeError as e:
        raise ValidationError("value", value, f"must be valid JSON: {e}")


def validate_date_format(value: str, format: str = "%Y-%m-%d") -> None:
    """Validate that a string matches a date format.

    Args:
        value: String to validate
        format: Date format string (default: "%Y-%m-%d")

    Raises:
        ValidationError: If value doesn't match format

    Example:
        >>> validate_date_format("2024-01-15", "%Y-%m-%d")  # OK
        >>> validate_date_format("01/15/2024", "%m/%d/%Y")  # OK
        >>> validate_date_format("invalid", "%Y-%m-%d")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    try:
        from datetime import datetime

        datetime.strptime(value, format)
    except ValueError:
        raise ValidationError("value", value, f"must match date format {format!r}")


def validate_time_format(value: str, format: str = "%H:%M:%S") -> None:
    """Validate that a string matches a time format.

    Args:
        value: String to validate
        format: Time format string (default: "%H:%M:%S")

    Raises:
        ValidationError: If value doesn't match format

    Example:
        >>> validate_time_format("14:30:00", "%H:%M:%S")  # OK
        >>> validate_time_format("2:30 PM", "%I:%M %p")  # OK
        >>> validate_time_format("invalid", "%H:%M:%S")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    try:
        from datetime import datetime

        datetime.strptime(value, format)
    except ValueError:
        raise ValidationError("value", value, f"must match time format {format!r}")


def validate_datetime_format(value: str, format: str = "%Y-%m-%d %H:%M:%S") -> None:
    """Validate that a string matches a datetime format.

    Args:
        value: String to validate
        format: Datetime format string (default: "%Y-%m-%d %H:%M:%S")

    Raises:
        ValidationError: If value doesn't match format

    Example:
        >>> validate_datetime_format("2024-01-15 14:30:00")  # OK
        >>> validate_datetime_format("invalid", "%Y-%m-%d %H:%M:%S")  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    try:
        from datetime import datetime

        datetime.strptime(value, format)
    except ValueError:
        raise ValidationError("value", value, f"must match datetime format {format!r}")


# ============================================================================
# Collection Validators
# ============================================================================


def validate_list_length(
    value: list, min_length: Optional[int] = None, max_length: Optional[int] = None
) -> None:
    """Validate that a list has a length within a range.

    Args:
        value: List to validate
        min_length: Minimum length (inclusive)
        max_length: Maximum length (inclusive)

    Raises:
        ValidationError: If length is out of range

    Example:
        >>> validate_list_length([1, 2, 3], min_length=2, max_length=5)  # OK
        >>> validate_list_length([1], min_length=2)  # Raises ValidationError
    """
    if not isinstance(value, list):
        raise ValidationError("value", value, "must be a list")
    length = len(value)
    if min_length is not None and length < min_length:
        raise ValidationError("value", value, f"list length must be >= {min_length}")
    if max_length is not None and length > max_length:
        raise ValidationError("value", value, f"list length must be <= {max_length}")


def validate_dict_keys(
    value: dict, required_keys: Optional[list[str]] = None, allowed_keys: Optional[list[str]] = None
) -> None:
    """Validate that a dictionary has required keys and/or only allowed keys.

    Args:
        value: Dictionary to validate
        required_keys: List of keys that must be present
        allowed_keys: List of keys that are allowed (if None, all keys allowed)

    Raises:
        ValidationError: If keys don't match requirements

    Example:
        >>> validate_dict_keys({"a": 1, "b": 2}, required_keys=["a"])  # OK
        >>> validate_dict_keys({"a": 1}, required_keys=["a", "b"])  # Raises ValidationError
        >>> validate_dict_keys({"a": 1, "c": 3}, allowed_keys=["a", "b"])  # Raises ValidationError
    """
    if not isinstance(value, dict):
        raise ValidationError("value", value, "must be a dictionary")

    if required_keys:
        missing = set(required_keys) - set(value.keys())
        if missing:
            raise ValidationError("value", value, f"missing required keys: {list(missing)}")

    if allowed_keys is not None:
        extra = set(value.keys()) - set(allowed_keys)
        if extra:
            raise ValidationError("value", value, f"contains disallowed keys: {list(extra)}")


# ============================================================================
# File/Path Validators
# ============================================================================


def validate_file_path(value: str, must_exist: bool = False) -> None:
    """Validate that a string is a valid file path.

    Args:
        value: String to validate
        must_exist: Whether the file must exist

    Raises:
        ValidationError: If value is not a valid file path

    Example:
        >>> validate_file_path("/path/to/file.txt")  # OK
        >>> validate_file_path("/nonexistent.txt", must_exist=True)  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    try:
        path = Path(value)
        if must_exist and not path.is_file():
            raise ValidationError("value", value, f"file path must exist: {value}")
    except Exception as e:
        raise ValidationError("value", value, f"must be a valid file path: {e}")


def validate_directory_path(value: str, must_exist: bool = False) -> None:
    """Validate that a string is a valid directory path.

    Args:
        value: String to validate
        must_exist: Whether the directory must exist

    Raises:
        ValidationError: If value is not a valid directory path

    Example:
        >>> validate_directory_path("/path/to/dir")  # OK
        >>> validate_directory_path("/nonexistent", must_exist=True)  # Raises ValidationError
    """
    if not isinstance(value, str):
        raise ValidationError("value", value, "must be a string")
    try:
        path = Path(value)
        if must_exist and not path.is_dir():
            raise ValidationError("value", value, f"directory path must exist: {value}")
    except Exception as e:
        raise ValidationError("value", value, f"must be a valid directory path: {e}")


# ============================================================================
# Custom Validators
# ============================================================================


def validate_custom(
    value: Any, validator: Callable[[Any], bool], message: str = "validation failed"
) -> None:
    """Validate using a custom validator function.

    Args:
        value: Value to validate
        validator: Function that returns True if value is valid
        message: Error message if validation fails

    Raises:
        ValidationError: If validator returns False

    Example:
        >>> def is_even(n): return n % 2 == 0
        >>> validate_custom(4, is_even)  # OK
        >>> validate_custom(3, is_even)  # Raises ValidationError
    """
    if not validator(value):
        raise ValidationError("value", value, message)


def apply_validators(config: Any, validators: dict[str, list[Callable[[Any], None]]]) -> None:
    """Apply validators to a configuration object.

    Args:
        config: Configuration object (dataclass instance)
        validators: Dictionary mapping field names to lists of validator functions

    Raises:
        ValidationError: If any validation fails

    Example:
        >>> @dataclass
        ... class Config:
        ...     port: int = 8000
        ...     host: str = "localhost"
        >>> cfg = Config()
        >>> apply_validators(cfg, {
        ...     "port": [lambda v: validate_port(v)],
        ...     "host": [lambda v: validate_not_empty(v)]
        ... })
    """
    for key, validator_list in validators.items():
        if not hasattr(config, key):
            continue
        value = getattr(config, key)
        for validator in validator_list:
            try:
                validator(value)
            except ValidationError as e:
                e.key = key
                log_validation_error(key, value, e.message)
                raise
