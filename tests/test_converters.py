"""
Tests for type converters.
"""

from typing import Optional, Union

import pytest

from varlord.converters import convert_value


def test_convert_int():
    """Test integer conversion."""
    assert convert_value("123", int) == 123
    assert convert_value(123, int) == 123
    assert convert_value(123.5, int) == 123
    assert convert_value("123.5", int) == 123


def test_convert_float():
    """Test float conversion."""
    assert convert_value("123.5", float) == 123.5
    assert convert_value(123, float) == 123.0
    assert convert_value("123", float) == 123.0


def test_convert_bool():
    """Test boolean conversion."""
    assert convert_value("true", bool) is True
    assert convert_value("True", bool) is True
    assert convert_value("1", bool) is True
    assert convert_value("yes", bool) is True
    assert convert_value("false", bool) is False
    assert convert_value("False", bool) is False
    assert convert_value("0", bool) is False
    assert convert_value("no", bool) is False
    assert convert_value("", bool) is False
    assert convert_value(1, bool) is True
    assert convert_value(0, bool) is False


def test_convert_str():
    """Test string conversion."""
    assert convert_value(123, str) == "123"
    assert convert_value("hello", str) == "hello"


def test_convert_optional():
    """Test Optional type conversion."""
    assert convert_value("123", Optional[int]) == 123
    assert convert_value(None, Optional[int]) is None
    assert convert_value("hello", Optional[str]) == "hello"


def test_convert_union():
    """Test Union type conversion."""
    # Union[int, str] should try int first, then str
    result1 = convert_value("123", Union[int, str])
    assert result1 == 123 or result1 == "123"  # Either conversion is acceptable
    assert convert_value("hello", Union[int, str]) == "hello"  # int fails, use str


def test_convert_invalid():
    """Test invalid conversion."""
    # Should raise ValueError for invalid int conversion
    with pytest.raises(ValueError):
        convert_value("not_a_number", int)

    # Should raise ValueError for invalid float conversion
    with pytest.raises(ValueError):
        convert_value("not_a_number", float)
