"""
Comprehensive tests for model validation rules.

Tests all validation scenarios including:
- Default required behavior (fields are required by default)
- Optional fields (explicitly marked with optional=True)
- Optional type annotations (rejected)
- Nested field validation
- Config class integration
- Error message correctness
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

import pytest

from varlord import Config, sources
from varlord.model_validation import (
    RequiredFieldError,
    validate_model_definition,
)


class TestDefaultRequiredBehavior:
    """Test cases for default required behavior (fields are required by default)."""

    def test_single_field_default_required(self):
        """Test single field without optional is required by default."""

        @dataclass
        class Config:
            api_key: str = field()  # Required by default

        # Should not raise
        validate_model_definition(Config)

        # Verify field is required
        from varlord.metadata import get_all_fields_info

        field_infos = get_all_fields_info(Config)
        api_key_info = next(f for f in field_infos if f.name == "api_key")
        assert api_key_info.required is True
        assert api_key_info.optional is False

    def test_multiple_fields_default_required(self):
        """Test multiple fields without optional are required by default."""

        @dataclass
        class Config:
            api_key: str = field()  # Required by default
            host: str = field()  # Required by default
            port: int = field()  # Required by default

        # Should not raise
        validate_model_definition(Config)

        from varlord.metadata import get_all_fields_info

        field_infos = get_all_fields_info(Config)
        for field_info in field_infos:
            assert field_info.required is True
            assert field_info.optional is False

    def test_nested_field_default_required(self):
        """Test nested field without optional is required by default."""

        @dataclass
        class DBConfig:
            host: str = field()  # Required by default

        @dataclass
        class AppConfig:
            db: DBConfig = field()  # Required by default

        # Should not raise
        validate_model_definition(AppConfig)

        from varlord.metadata import get_all_fields_info

        field_infos = get_all_fields_info(AppConfig)
        db_host_info = next(f for f in field_infos if f.normalized_key == "db.host")
        assert db_host_info.required is True
        assert db_host_info.optional is False

    def test_config_class_accepts_default_required(self):
        """Test that Config class accepts models with default required fields."""

        @dataclass
        class TestConfig:
            api_key: str = field()  # Required by default

        # Should not raise
        from varlord import Config

        cfg = Config(model=TestConfig, sources=[])
        assert cfg is not None


class TestOptionalTypeAnnotations:
    """Test cases for Optional[T] type annotation support."""

    def test_optional_str(self):
        """Test Optional[str] type annotation is automatically optional."""

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

    def test_optional_int(self):
        """Test Optional[int] type annotation."""

        @dataclass
        class Config:
            port: Optional[int] = field()

        validate_model_definition(Config)

        from varlord.metadata import get_all_fields_info

        field_infos = get_all_fields_info(Config)
        port_info = next(f for f in field_infos if f.name == "port")
        assert port_info.optional is True

    def test_optional_bool(self):
        """Test Optional[bool] type annotation."""

        @dataclass
        class Config:
            debug: Optional[bool] = field()

        validate_model_definition(Config)

        from varlord.metadata import get_all_fields_info

        field_infos = get_all_fields_info(Config)
        debug_info = next(f for f in field_infos if f.name == "debug")
        assert debug_info.optional is True

    def test_optional_list(self):
        """Test Optional[List] type annotation."""

        @dataclass
        class Config:
            items: Optional[List[str]] = field()

        validate_model_definition(Config)

        from varlord.metadata import get_all_fields_info

        field_infos = get_all_fields_info(Config)
        items_info = next(f for f in field_infos if f.name == "items")
        assert items_info.optional is True

    def test_optional_dict(self):
        """Test Optional[Dict] type annotation."""

        @dataclass
        class Config:
            settings: Optional[Dict[str, str]] = field()

        validate_model_definition(Config)

        from varlord.metadata import get_all_fields_info

        field_infos = get_all_fields_info(Config)
        settings_info = next(f for f in field_infos if f.name == "settings")
        assert settings_info.optional is True

    def test_union_none_str(self):
        """Test Union[str, None] type annotation."""

        @dataclass
        class Config:
            api_key: Union[str, None] = field()

        validate_model_definition(Config)

        from varlord.metadata import get_all_fields_info

        field_infos = get_all_fields_info(Config)
        api_key_info = next(f for f in field_infos if f.name == "api_key")
        assert api_key_info.optional is True

    def test_union_none_int(self):
        """Test Union[int, None] type annotation."""

        @dataclass
        class Config:
            port: Union[int, None] = field()

        validate_model_definition(Config)

        from varlord.metadata import get_all_fields_info

        field_infos = get_all_fields_info(Config)
        port_info = next(f for f in field_infos if f.name == "port")
        assert port_info.optional is True

    def test_nested_optional_type(self):
        """Test nested field with Optional type."""

        @dataclass
        class DBConfig:
            host: Optional[str] = field()

        @dataclass
        class AppConfig:
            db: DBConfig = field()

        validate_model_definition(AppConfig)

        from varlord.metadata import get_all_fields_info

        field_infos = get_all_fields_info(AppConfig)
        db_host_info = next(f for f in field_infos if f.normalized_key == "db.host")
        assert db_host_info.optional is True

    def test_config_class_accepts_optional_type(self):
        """Test that Config class accepts models with Optional type."""

        @dataclass
        class TestConfig:
            api_key: Optional[str] = field()

        # Should not raise
        from varlord import Config

        cfg = Config(model=TestConfig, sources=[])
        assert cfg is not None


class TestValidConfigurations:
    """Test cases for valid configurations."""

    def test_all_required_fields(self):
        """Test model with all required fields (default behavior)."""

        @dataclass
        class Config:
            api_key: str = field()  # Required by default
            host: str = field()  # Required by default
            port: int = field()  # Required by default

        # Should not raise
        validate_model_definition(Config)

    def test_all_optional_fields(self):
        """Test model with all optional fields."""

        @dataclass
        class Config:
            api_key: str = field(default="")
            host: str = field(default="localhost")
            port: int = field(default=8000)

        # Should not raise
        validate_model_definition(Config)

    def test_mixed_required_and_optional(self):
        """Test model with mixed required and optional fields."""

        @dataclass
        class AppConfig:
            # Required fields (no metadata needed)
            api_key: str = field()  # Required by default
            port: int = field()  # Required by default
            # Optional fields (explicitly marked)
            host: str = field(default="localhost")
            debug: bool = field(default=False)

        # Should not raise
        validate_model_definition(AppConfig)

    def test_nested_valid_configuration(self):
        """Test nested configuration with valid metadata."""

        @dataclass
        class DBConfig:
            host: str = field()  # Required by default
            port: int = field(default=5432)

        @dataclass
        class AppConfig:
            api_key: str = field()  # Required by default
            db: DBConfig = field()  # Required by default

        # Should not raise
        validate_model_definition(AppConfig)

    def test_config_class_accepts_valid_model(self):
        """Test that Config class accepts valid models."""

        @dataclass
        class AppConfig:
            api_key: str = field()  # Required by default
            host: str = field(default="localhost")

        # Should not raise
        cfg = Config(model=AppConfig, sources=[])
        assert cfg is not None


class TestConfigIntegration:
    """Test Config class integration with validation."""

    def test_config_init_validates_model(self):
        """Test that Config.__init__ validates model definition."""

        @dataclass
        class ValidConfig:
            api_key: str = field()  # Required by default

        # Should not raise (valid model)
        cfg = Config(model=ValidConfig, sources=[])
        assert cfg is not None

    def test_config_load_validates_required_fields(self):
        """Test that Config.load() validates required fields."""

        @dataclass
        class AppConfig:
            api_key: str = field()  # Required by default
            host: str = field(default="localhost")

        cfg = Config(model=AppConfig, sources=[])

        with pytest.raises(RequiredFieldError) as exc_info:
            cfg.load()

        assert "api_key" in str(exc_info.value)

    def test_config_load_with_valid_data(self):
        """Test Config.load() with valid data."""
        import os

        @dataclass
        class AppConfig:
            api_key: str = field()  # Required by default
            host: str = field(default="localhost")

        os.environ["API_KEY"] = "secret-key"

        try:
            cfg = Config(
                model=AppConfig,
                sources=[sources.Env(model=AppConfig)],
            )
            app = cfg.load()

            assert app.api_key == "secret-key"
            assert app.host == "localhost"
        finally:
            os.environ.pop("API_KEY", None)

    def test_config_validate_method(self):
        """Test Config.validate() method."""

        @dataclass
        class AppConfig:
            api_key: str = field()  # Required by default
            host: str = field(default="localhost")

        cfg = Config(model=AppConfig, sources=[])

        # Should raise for missing required field
        with pytest.raises(RequiredFieldError):
            cfg.validate()

        # Should pass with valid data
        valid_config = {"api_key": "secret-key", "host": "0.0.0.0"}
        cfg.validate(valid_config)


class TestOptionalWithDefaults:
    """Test Optional[T] with default values."""

    def test_optional_with_default(self):
        """Test Optional[T] with default value - should still be optional."""

        @dataclass
        class Config:
            timeout: Optional[int] = field(default=None)

        validate_model_definition(Config)

        from varlord.metadata import get_all_fields_info

        field_infos = get_all_fields_info(Config)
        timeout_info = next(f for f in field_infos if f.name == "timeout")
        assert timeout_info.optional is True
        assert timeout_info.required is False

    def test_mixed_optional_and_required(self):
        """Test model with both Optional[T] and required fields."""

        @dataclass
        class Config:
            api_key: str = field()  # Required
            timeout: Optional[int] = field()  # Optional (Optional type)
            host: str = field(default="localhost")  # Optional (has default)

        validate_model_definition(Config)

        from varlord.metadata import get_all_fields_info

        field_infos = get_all_fields_info(Config)

        api_key_info = next(f for f in field_infos if f.name == "api_key")
        assert api_key_info.required is True
        assert api_key_info.optional is False

        timeout_info = next(f for f in field_infos if f.name == "timeout")
        assert timeout_info.optional is True
        assert timeout_info.required is False

        host_info = next(f for f in field_infos if f.name == "host")
        assert host_info.optional is True
        assert host_info.required is False


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_model(self):
        """Test empty model (no fields)."""

        @dataclass
        class EmptyConfig:
            pass

        # Should not raise (no fields to validate)
        validate_model_definition(EmptyConfig)

    def test_field_with_default_factory(self):
        """Test field with default_factory."""

        @dataclass
        class Config:
            items: List[str] = field(default_factory=list)

        # Should not raise
        validate_model_definition(Config)

    def test_field_with_description(self):
        """Test field with description metadata."""

        @dataclass
        class Config:
            api_key: str = field(
                metadata={"description": "API key for authentication"}
            )  # Required by default

        # Should not raise
        validate_model_definition(Config)

    def test_field_with_help(self):
        """Test field with help metadata."""

        @dataclass
        class Config:
            api_key: str = field(metadata={"help": "Required API key"})  # Required by default

        # Should not raise
        validate_model_definition(Config)

    def test_field_with_all_metadata(self):
        """Test field with all metadata keys."""

        @dataclass
        class Config:
            api_key: str = field(
                metadata={"description": "API key", "help": "Required API key"}
            )  # Required by default

        # Should not raise
        validate_model_definition(Config)

    def test_deeply_nested_configuration(self):
        """Test deeply nested configuration."""

        @dataclass
        class CacheConfig:
            enabled: bool = field()  # Required by default

        @dataclass
        class DBConfig:
            host: str = field()  # Required by default
            cache: CacheConfig = field()  # Required by default

        @dataclass
        class AppConfig:
            db: DBConfig = field()  # Required by default

        # Should not raise
        validate_model_definition(AppConfig)
