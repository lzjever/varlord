"""
Tests for validation module.
"""

from dataclasses import dataclass, field

import pytest

from varlord.model_validation import (
    RequiredFieldError,
    validate_config,
    validate_model_definition,
)


def test_validate_model_definition_success():
    """Test successful model definition validation."""

    @dataclass
    class Config:
        api_key: str = field()  # Required by default
        host: str = field(
            default="localhost",
        )

    # Should not raise
    validate_model_definition(Config)


def test_validate_model_definition_nested():
    """Test model definition validation with nested fields."""

    @dataclass
    class DBConfig:
        host: str = field()  # Required by default
        port: int = field(
            default=5432,
        )

    @dataclass
    class AppConfig:
        db: DBConfig = field()  # Required by default

    # Should not raise
    validate_model_definition(AppConfig)


def test_validate_config_success():
    """Test successful config validation."""

    @dataclass
    class Config:
        api_key: str = field()  # Required by default
        host: str = field(
            default="localhost",
        )

    config_dict = {
        "host": "0.0.0.0",
        "api_key": "secret-key",
    }

    # Should not raise
    validate_config(Config, config_dict, [])


def test_validate_config_missing_required():
    """Test config validation with missing required field."""

    @dataclass
    class Config:
        api_key: str = field()  # Required by default
        host: str = field(
            default="localhost",
        )

    config_dict = {
        "host": "0.0.0.0",
        # api_key missing
    }

    with pytest.raises(RequiredFieldError) as exc_info:
        validate_config(Config, config_dict, [])

    assert "api_key" in str(exc_info.value)
    assert "missing" in str(exc_info.value).lower()


def test_validate_config_empty_string_valid():
    """Test that empty string is considered valid."""

    @dataclass
    class Config:
        api_key: str = field()  # Required by default

    config_dict = {
        "api_key": "",  # Empty string is valid
    }

    # Should not raise (empty string is valid)
    validate_config(Config, config_dict, [])


def test_validate_config_nested():
    """Test config validation with nested fields."""

    @dataclass
    class DBConfig:
        host: str = field()  # Required by default
        port: int = field(
            default=5432,
        )

    @dataclass
    class AppConfig:
        db: DBConfig = field()  # Required by default

    # Missing db.host
    config_dict = {
        "db.port": 5432,
    }

    with pytest.raises(RequiredFieldError) as exc_info:
        validate_config(AppConfig, config_dict, [])

    assert "db.host" in str(exc_info.value)


def test_validate_model_definition_accepts_optional_type():
    """Test that validate_model_definition accepts Optional[T] type annotations."""
    from typing import Optional

    @dataclass
    class Config:
        api_key: Optional[str] = field()

    # Should not raise - Optional[T] is supported
    validate_model_definition(Config)

    # Verify field is optional
    from varlord.metadata import get_all_fields_info

    field_infos = get_all_fields_info(Config)
    api_key_info = next(f for f in field_infos if f.name == "api_key")
    assert api_key_info.optional is True
    assert api_key_info.required is False


def test_validate_model_definition_accepts_union_none():
    """Test that validate_model_definition accepts Union[T, None] type annotations."""
    from typing import Union

    @dataclass
    class Config:
        api_key: Union[str, None] = field()

    # Should not raise - Union[T, None] is supported
    validate_model_definition(Config)

    # Verify field is optional
    from varlord.metadata import get_all_fields_info

    field_infos = get_all_fields_info(Config)
    api_key_info = next(f for f in field_infos if f.name == "api_key")
    assert api_key_info.optional is True
    assert api_key_info.required is False


def test_validate_model_definition_default_required():
    """Test that fields are required by default."""

    # Test with no metadata (should be required by default)
    @dataclass
    class Config1:
        api_key: str = field()  # Required by default

    # Test with optional
    @dataclass
    class Config2:
        api_key: str = field()

    # Both should pass
    validate_model_definition(Config1)
    validate_model_definition(Config2)

    # Verify Config1 field is required
    from varlord.metadata import get_all_fields_info

    field_infos = get_all_fields_info(Config1)
    api_key_info = next(f for f in field_infos if f.name == "api_key")
    assert api_key_info.required is True
    assert api_key_info.optional is False
