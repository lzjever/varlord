"""
Tests for validation module.
"""

import pytest
from dataclasses import dataclass, field
from varlord.model_validation import (
    ModelDefinitionError,
    RequiredFieldError,
    validate_model_definition,
    validate_config,
)


def test_validate_model_definition_success():
    """Test successful model definition validation."""

    @dataclass
    class Config:
        api_key: str = field(metadata={"required": True})
        host: str = field(default="localhost", metadata={"optional": True})

    # Should not raise
    validate_model_definition(Config)


def test_validate_model_definition_missing_metadata():
    """Test model definition validation with missing metadata."""

    @dataclass
    class Config:
        host: str = field(default="localhost")  # Missing required/optional

    with pytest.raises(ModelDefinitionError) as exc_info:
        validate_model_definition(Config)

    assert "host" in str(exc_info.value)
    assert "required" in str(exc_info.value) or "optional" in str(exc_info.value)


def test_validate_model_definition_nested():
    """Test model definition validation with nested fields."""

    @dataclass
    class DBConfig:
        host: str = field(metadata={"required": True})
        port: int = field(default=5432)  # Missing metadata

    @dataclass
    class AppConfig:
        db: DBConfig = field(metadata={"required": True})

    with pytest.raises(ModelDefinitionError) as exc_info:
        validate_model_definition(AppConfig)

    # Should catch missing metadata in nested field
    assert "db.port" in str(exc_info.value) or "port" in str(exc_info.value)


def test_validate_config_success():
    """Test successful config validation."""

    @dataclass
    class Config:
        api_key: str = field(metadata={"required": True})
        host: str = field(default="localhost", metadata={"optional": True})

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
        api_key: str = field(metadata={"required": True})
        host: str = field(default="localhost", metadata={"optional": True})

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
        api_key: str = field(metadata={"required": True})

    config_dict = {
        "api_key": "",  # Empty string is valid
    }

    # Should not raise (empty string is valid)
    validate_config(Config, config_dict, [])


def test_validate_config_nested():
    """Test config validation with nested fields."""

    @dataclass
    class DBConfig:
        host: str = field(metadata={"required": True})
        port: int = field(default=5432, metadata={"optional": True})

    @dataclass
    class AppConfig:
        db: DBConfig = field(metadata={"required": True})

    # Missing db.host
    config_dict = {
        "db.port": 5432,
    }

    with pytest.raises(RequiredFieldError) as exc_info:
        validate_config(AppConfig, config_dict, [])

    assert "db.host" in str(exc_info.value)
