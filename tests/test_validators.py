"""
Comprehensive tests for validators.
"""

import os
import tempfile

import pytest

from varlord.validators import (
    ValidationError,
    apply_validators,
    validate_base64,
    validate_choice,
    # Custom
    validate_custom,
    validate_date_format,
    validate_datetime_format,
    validate_dict_keys,
    validate_directory_path,
    validate_domain,
    validate_email,
    # File/Path
    validate_file_path,
    validate_float,
    validate_greater_than,
    validate_integer,
    validate_ip,
    validate_ipv4,
    validate_ipv6,
    validate_json_string,
    # String
    validate_length,
    validate_less_than,
    # Collection
    validate_list_length,
    validate_non_negative,
    validate_not_empty,
    validate_percentage,
    validate_phone,
    validate_port,
    # Numeric
    validate_positive,
    # Basic
    validate_range,
    validate_regex,
    validate_time_format,
    validate_url,
    validate_uuid,
)

# ============================================================================
# Basic Validators
# ============================================================================


def test_validate_range():
    """Test validate_range."""
    validate_range(50, min=0, max=100)
    validate_range(0, min=0, max=100)
    validate_range(100, min=0, max=100)

    with pytest.raises(ValidationError):
        validate_range(-1, min=0, max=100)
    with pytest.raises(ValidationError):
        validate_range(101, min=0, max=100)
    with pytest.raises(ValidationError):
        validate_range(50, min=60)


def test_validate_regex():
    """Test validate_regex."""
    validate_regex("abc123", r"^[a-z]+\d+$")
    validate_regex("test", r"^test$")

    with pytest.raises(ValidationError):
        validate_regex("ABC123", r"^[a-z]+\d+$")
    with pytest.raises(ValidationError):
        validate_regex(123, r"^\d+$")  # Not a string


def test_validate_choice():
    """Test validate_choice."""
    validate_choice("red", ["red", "green", "blue"])
    validate_choice(42, [1, 42, 100])

    with pytest.raises(ValidationError):
        validate_choice("yellow", ["red", "green", "blue"])
    with pytest.raises(ValidationError):
        validate_choice(99, [1, 42, 100])


def test_validate_not_empty():
    """Test validate_not_empty."""
    validate_not_empty("hello")
    validate_not_empty([1, 2, 3])
    validate_not_empty({"key": "value"})
    validate_not_empty(0)  # 0 is not empty
    validate_not_empty(False)  # False is not empty

    with pytest.raises(ValidationError):
        validate_not_empty("")
    with pytest.raises(ValidationError):
        validate_not_empty([])
    with pytest.raises(ValidationError):
        validate_not_empty({})
    with pytest.raises(ValidationError):
        validate_not_empty(None)


# ============================================================================
# Numeric Validators
# ============================================================================


def test_validate_positive():
    """Test validate_positive."""
    validate_positive(1)
    validate_positive(100)
    validate_positive(0.5)

    with pytest.raises(ValidationError):
        validate_positive(0)
    with pytest.raises(ValidationError):
        validate_positive(-1)
    with pytest.raises(ValidationError):
        validate_positive("10")  # Not a number


def test_validate_non_negative():
    """Test validate_non_negative."""
    validate_non_negative(0)
    validate_non_negative(100)
    validate_non_negative(0.5)

    with pytest.raises(ValidationError):
        validate_non_negative(-1)
    with pytest.raises(ValidationError):
        validate_non_negative(-0.1)


def test_validate_integer():
    """Test validate_integer."""
    validate_integer(42)
    validate_integer(0)
    validate_integer(-100)

    with pytest.raises(ValidationError):
        validate_integer(42.5)
    with pytest.raises(ValidationError):
        validate_integer("42")


def test_validate_float():
    """Test validate_float."""
    validate_float(3.14)
    validate_float(42)  # int is acceptable
    validate_float(0.0)

    with pytest.raises(ValidationError):
        validate_float("not a number")
    with pytest.raises(ValidationError):
        validate_float([1, 2, 3])


def test_validate_percentage():
    """Test validate_percentage."""
    validate_percentage(0)
    validate_percentage(50)
    validate_percentage(100)

    with pytest.raises(ValidationError):
        validate_percentage(-1)
    with pytest.raises(ValidationError):
        validate_percentage(101)


def test_validate_port():
    """Test validate_port."""
    validate_port(1)
    validate_port(8080)
    validate_port(65535)

    with pytest.raises(ValidationError):
        validate_port(0)
    with pytest.raises(ValidationError):
        validate_port(65536)
    with pytest.raises(ValidationError):
        validate_port(42.5)  # Not an integer


def test_validate_greater_than():
    """Test validate_greater_than."""
    validate_greater_than(10, 5)
    validate_greater_than(0.1, 0)

    with pytest.raises(ValidationError):
        validate_greater_than(5, 5)
    with pytest.raises(ValidationError):
        validate_greater_than(3, 5)


def test_validate_less_than():
    """Test validate_less_than."""
    validate_less_than(3, 5)
    validate_less_than(0.1, 1)

    with pytest.raises(ValidationError):
        validate_less_than(5, 5)
    with pytest.raises(ValidationError):
        validate_less_than(10, 5)


# ============================================================================
# String Validators
# ============================================================================


def test_validate_length():
    """Test validate_length."""
    validate_length("hello", min_length=3, max_length=10)
    validate_length("hi", min_length=2)
    validate_length("test", max_length=10)

    with pytest.raises(ValidationError):
        validate_length("hi", min_length=3)
    with pytest.raises(ValidationError):
        validate_length("very long string", max_length=10)
    with pytest.raises(ValidationError):
        validate_length(123, min_length=1)  # Not a string


def test_validate_email():
    """Test validate_email."""
    validate_email("user@example.com")
    validate_email("test.user+tag@example.co.uk")
    validate_email("user123@test-domain.com")

    with pytest.raises(ValidationError):
        validate_email("invalid-email")
    with pytest.raises(ValidationError):
        validate_email("@example.com")
    with pytest.raises(ValidationError):
        validate_email("user@")
    with pytest.raises(ValidationError):
        validate_email(123)  # Not a string


def test_validate_url():
    """Test validate_url."""
    validate_url("https://example.com")
    validate_url("http://example.com/path?query=1")
    validate_url("https://sub.example.com:8080/path")

    with pytest.raises(ValidationError):
        validate_url("not-a-url")
    with pytest.raises(ValidationError):
        validate_url("example.com")  # Missing scheme

    # Test without requiring scheme
    validate_url("example.com", require_scheme=False)
    validate_url("localhost:8080", require_scheme=False)


def test_validate_ipv4():
    """Test validate_ipv4."""
    validate_ipv4("192.168.1.1")
    validate_ipv4("0.0.0.0")
    validate_ipv4("255.255.255.255")

    with pytest.raises(ValidationError):
        validate_ipv4("256.1.1.1")
    with pytest.raises(ValidationError):
        validate_ipv4("2001:0db8::1")  # IPv6
    with pytest.raises(ValidationError):
        validate_ipv4("invalid")


def test_validate_ipv6():
    """Test validate_ipv6."""
    validate_ipv6("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
    validate_ipv6("::1")
    validate_ipv6("2001:db8::1")

    with pytest.raises(ValidationError):
        validate_ipv6("192.168.1.1")  # IPv4
    with pytest.raises(ValidationError):
        validate_ipv6("invalid")


def test_validate_ip():
    """Test validate_ip."""
    validate_ip("192.168.1.1")  # IPv4
    validate_ip("2001:db8::1")  # IPv6

    with pytest.raises(ValidationError):
        validate_ip("invalid")


def test_validate_domain():
    """Test validate_domain."""
    validate_domain("example.com")
    validate_domain("sub.example.com")
    validate_domain("test.co.uk")

    with pytest.raises(ValidationError):
        validate_domain("invalid..domain")
    with pytest.raises(ValidationError):
        validate_domain("not a domain")
    with pytest.raises(ValidationError):
        validate_domain(".example.com")  # Leading dot


def test_validate_phone():
    """Test validate_phone."""
    validate_phone("+1234567890")
    validate_phone("1234567890")

    # Chinese mobile
    validate_phone("13800138000", country="CN")
    validate_phone("15912345678", country="CN")

    # US phone (area code and exchange code cannot start with 0 or 1)
    validate_phone("5552345678", country="US")  # Valid: 555 (area), 234 (exchange)
    validate_phone("+15552345678", country="US")

    with pytest.raises(ValidationError):
        validate_phone("invalid")
    with pytest.raises(ValidationError):
        validate_phone("123", country="CN")  # Too short


def test_validate_uuid():
    """Test validate_uuid."""
    validate_uuid("550e8400-e29b-41d4-a716-446655440000")
    validate_uuid("00000000-0000-0000-0000-000000000000")

    with pytest.raises(ValidationError):
        validate_uuid("invalid-uuid")
    with pytest.raises(ValidationError):
        validate_uuid("550e8400-e29b-41d4-a716")  # Incomplete


def test_validate_base64():
    """Test validate_base64."""
    validate_base64("SGVsbG8gV29ybGQ=")  # "Hello World"
    validate_base64("dGVzdA==")  # "test"

    with pytest.raises(ValidationError):
        validate_base64("invalid!")
    with pytest.raises(ValidationError):
        validate_base64("not base64@#$")


def test_validate_json_string():
    """Test validate_json_string."""
    validate_json_string('{"key": "value"}')
    validate_json_string("[1, 2, 3]")
    validate_json_string('"string"')
    validate_json_string("123")

    with pytest.raises(ValidationError):
        validate_json_string("invalid json")
    with pytest.raises(ValidationError):
        validate_json_string('{"key": value}')  # Missing quotes


def test_validate_date_format():
    """Test validate_date_format."""
    validate_date_format("2024-01-15", "%Y-%m-%d")
    validate_date_format("01/15/2024", "%m/%d/%Y")

    with pytest.raises(ValidationError):
        validate_date_format("invalid", "%Y-%m-%d")
    with pytest.raises(ValidationError):
        validate_date_format("2024-13-45", "%Y-%m-%d")  # Invalid date


def test_validate_time_format():
    """Test validate_time_format."""
    validate_time_format("14:30:00", "%H:%M:%S")
    validate_time_format("2:30 PM", "%I:%M %p")

    with pytest.raises(ValidationError):
        validate_time_format("invalid", "%H:%M:%S")
    with pytest.raises(ValidationError):
        validate_time_format("25:00:00", "%H:%M:%S")  # Invalid time


def test_validate_datetime_format():
    """Test validate_datetime_format."""
    validate_datetime_format("2024-01-15 14:30:00", "%Y-%m-%d %H:%M:%S")
    validate_datetime_format("2024-01-15 14:30:00")  # Default format

    with pytest.raises(ValidationError):
        validate_datetime_format("invalid", "%Y-%m-%d %H:%M:%S")


# ============================================================================
# Collection Validators
# ============================================================================


def test_validate_list_length():
    """Test validate_list_length."""
    validate_list_length([1, 2, 3], min_length=2, max_length=5)
    validate_list_length([1], min_length=1)
    validate_list_length([1, 2, 3], max_length=5)

    with pytest.raises(ValidationError):
        validate_list_length([1], min_length=2)
    with pytest.raises(ValidationError):
        validate_list_length([1, 2, 3, 4, 5, 6], max_length=5)
    with pytest.raises(ValidationError):
        validate_list_length("not a list", min_length=1)


def test_validate_dict_keys():
    """Test validate_dict_keys."""
    validate_dict_keys({"a": 1, "b": 2}, required_keys=["a"])
    validate_dict_keys({"a": 1, "b": 2}, allowed_keys=["a", "b", "c"])
    validate_dict_keys({"a": 1}, required_keys=["a"], allowed_keys=["a", "b"])

    with pytest.raises(ValidationError):
        validate_dict_keys({"a": 1}, required_keys=["a", "b"])
    with pytest.raises(ValidationError):
        validate_dict_keys({"a": 1, "c": 3}, allowed_keys=["a", "b"])
    with pytest.raises(ValidationError):
        validate_dict_keys("not a dict", required_keys=["a"])


# ============================================================================
# File/Path Validators
# ============================================================================


def test_validate_file_path():
    """Test validate_file_path."""
    # Test with temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
        validate_file_path(temp_path)
        validate_file_path(temp_path, must_exist=True)

    # Clean up
    os.unlink(temp_path)

    # Test non-existent file
    validate_file_path("/nonexistent/file.txt")  # OK if must_exist=False
    with pytest.raises(ValidationError):
        validate_file_path("/nonexistent/file.txt", must_exist=True)


def test_validate_directory_path():
    """Test validate_directory_path."""
    # Test with temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        validate_directory_path(temp_dir)
        validate_directory_path(temp_dir, must_exist=True)

    # Test non-existent directory
    validate_directory_path("/nonexistent/dir")  # OK if must_exist=False
    with pytest.raises(ValidationError):
        validate_directory_path("/nonexistent/dir", must_exist=True)


# ============================================================================
# Custom Validators
# ============================================================================


def test_validate_custom():
    """Test validate_custom."""

    def is_even(n):
        return isinstance(n, int) and n % 2 == 0

    validate_custom(4, is_even)
    validate_custom(2, is_even)

    with pytest.raises(ValidationError):
        validate_custom(3, is_even)
    with pytest.raises(ValidationError):
        validate_custom(3, is_even, message="must be even")


def test_apply_validators():
    """Test apply_validators."""
    from dataclasses import dataclass

    @dataclass
    class TestConfig:
        port: int = 8000
        host: str = "localhost"
        email: str = "user@example.com"

    config = TestConfig()

    # Valid config
    apply_validators(
        config,
        {
            "port": [lambda v: validate_port(v)],
            "host": [lambda v: validate_not_empty(v)],
            "email": [lambda v: validate_email(v)],
        },
    )

    # Invalid config
    invalid_config = TestConfig(port=70000, email="invalid")
    with pytest.raises(ValidationError) as exc_info:
        apply_validators(
            invalid_config,
            {
                "port": [lambda v: validate_port(v)],
                "email": [lambda v: validate_email(v)],
            },
        )
    assert exc_info.value.key == "port" or exc_info.value.key == "email"


def test_validation_error():
    """Test ValidationError."""
    error = ValidationError("port", 70000, "must be between 1 and 65535")
    assert error.key == "port"
    assert error.value == 70000
    assert error.message == "must be between 1 and 65535"
    assert "port" in str(error)
    assert "70000" in str(error)
