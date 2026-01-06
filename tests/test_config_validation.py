"""
Tests for Config validation functionality.
"""

from dataclasses import dataclass, field

import pytest

from varlord import Config, sources
from varlord.model_validation import RequiredFieldError


def test_config_validate_independent():
    """Test Config.validate() as standalone method."""

    @dataclass
    class AppConfig:
        api_key: str = field()
        host: str = field(
            default="localhost",
        )

    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Env(),
        ],
    )

    # Test with valid config dict
    valid_config = {
        "api_key": "secret",
        "host": "0.0.0.0",
    }
    cfg.validate(valid_config)  # Should not raise

    # Test with missing required field
    invalid_config = {
        "host": "0.0.0.0",
    }
    with pytest.raises(RequiredFieldError):
        cfg.validate(invalid_config)


def test_config_validate_loads_config():
    """Test Config.validate() loads config if None provided."""

    @dataclass
    class AppConfig:
        api_key: str = field()
        host: str = field(
            default="localhost",
        )

    # No sources provide api_key, so validation should fail
    cfg = Config(
        model=AppConfig,
        sources=[],
    )

    with pytest.raises(RequiredFieldError) as exc_info:
        cfg.validate()  # Should load config first, then validate

    assert "api_key" in str(exc_info.value)


def test_config_load_with_validate_false():
    """Test Config.load(validate=False) skips validation."""

    @dataclass
    class AppConfig:
        api_key: str = field(
            default="",
        )  # Use optional to avoid init error
        host: str = field(
            default="localhost",
        )

    cfg = Config(
        model=AppConfig,
        sources=[],  # No sources, so api_key will use default
    )

    # Should not raise even though validation is skipped
    app = cfg.load(validate=False)
    assert app.host == "localhost"
    assert app.api_key == ""  # Default value


def test_config_load_with_validate_true():
    """Test Config.load(validate=True) validates by default."""

    @dataclass
    class AppConfig:
        api_key: str = field()
        host: str = field(
            default="localhost",
        )

    cfg = Config(
        model=AppConfig,
        sources=[],  # No sources, so api_key will be missing
    )

    with pytest.raises(RequiredFieldError):
        cfg.load(validate=True)


def test_config_empty_collections_valid():
    """Test that empty collections are considered valid values."""

    @dataclass
    class AppConfig:
        items: list = field()
        tags: dict = field()

    cfg = Config(
        model=AppConfig,
        sources=[],
    )

    # Empty collections should be valid
    config_dict = {
        "items": [],
        "tags": {},
    }

    cfg.validate(config_dict)  # Should not raise


def test_config_multiple_missing_fields():
    """Test error message with multiple missing required fields."""

    @dataclass
    class AppConfig:
        api_key: str = field()
        secret: str = field()
        host: str = field(
            default="localhost",
        )

    cfg = Config(
        model=AppConfig,
        sources=[],
    )

    with pytest.raises(RequiredFieldError) as exc_info:
        cfg.validate()

    error_msg = str(exc_info.value)
    assert "api_key" in error_msg
    assert "secret" in error_msg


def test_config_nested_validation():
    """Test validation with nested fields."""

    @dataclass
    class DBConfig:
        host: str = field()
        port: int = field(
            default=5432,
        )

    @dataclass
    class AppConfig:
        api_key: str = field()
        db: DBConfig = field()

    cfg = Config(
        model=AppConfig,
        sources=[],
    )

    # Missing both api_key and db.host
    with pytest.raises(RequiredFieldError) as exc_info:
        cfg.validate()

    error_msg = str(exc_info.value)
    assert "api_key" in error_msg
    assert "db.host" in error_msg


def test_config_show_source_help():
    """Test show_source_help parameter."""

    @dataclass
    class AppConfig:
        api_key: str = field()

    # With source help enabled
    cfg_with_help = Config(
        model=AppConfig,
        sources=[sources.Env()],
        show_source_help=True,
    )

    with pytest.raises(RequiredFieldError) as exc_info:
        cfg_with_help.validate()

    error_msg = str(exc_info.value)
    # Should contain source help
    assert (
        "Environment Variables" in error_msg
        or "Command Line Arguments" in error_msg
        or len(error_msg) > 100
    )

    # With source help disabled
    cfg_no_help = Config(
        model=AppConfig,
        sources=[sources.Env()],
        show_source_help=False,
    )

    with pytest.raises(RequiredFieldError) as exc_info:
        cfg_no_help.validate()

    error_msg = str(exc_info.value)
    # Should not contain detailed source help
    assert len(error_msg) < 200  # Much shorter without help
