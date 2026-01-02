"""
Comprehensive tests for model validation rules.

Tests all validation scenarios including:
- Missing metadata
- Conflicting metadata
- Optional type annotations
- Nested field validation
- Config class integration
- Error message correctness
"""

import pytest
from dataclasses import dataclass, field
from typing import Optional, Union, List, Dict

from varlord import Config, sources
from varlord.model_validation import (
    ModelDefinitionError,
    RequiredFieldError,
    validate_model_definition,
)


class TestMissingMetadata:
    """Test cases for missing required/optional metadata."""

    def test_single_field_missing_metadata(self):
        """Test single field missing metadata."""

        @dataclass
        class BadConfig:
            api_key: str = field()  # Missing metadata

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        assert exc_info.value.reason == "missing_metadata"
        assert "api_key" in str(exc_info.value)
        assert (
            "required" in str(exc_info.value).lower() or "optional" in str(exc_info.value).lower()
        )

    def test_multiple_fields_missing_metadata(self):
        """Test multiple fields missing metadata - should catch first one."""

        @dataclass
        class BadConfig:
            api_key: str = field()  # Missing metadata
            host: str = field()  # Missing metadata
            port: int = field()  # Missing metadata

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        assert exc_info.value.reason == "missing_metadata"
        # Should catch at least one field
        assert (
            "api_key" in str(exc_info.value)
            or "host" in str(exc_info.value)
            or "port" in str(exc_info.value)
        )

    def test_nested_field_missing_metadata(self):
        """Test nested field missing metadata."""

        @dataclass
        class DBConfig:
            host: str = field()  # Missing metadata

        @dataclass
        class AppConfig:
            db: DBConfig = field(metadata={"required": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(AppConfig)

        assert exc_info.value.reason == "missing_metadata"
        assert "db.host" in str(exc_info.value) or "host" in str(exc_info.value)

    def test_mixed_valid_and_invalid_fields(self):
        """Test model with both valid and invalid fields."""

        @dataclass
        class BadConfig:
            api_key: str = field(metadata={"required": True})  # Valid
            host: str = field()  # Missing metadata
            port: int = field(metadata={"optional": True})  # Valid

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        assert exc_info.value.reason == "missing_metadata"
        assert "host" in str(exc_info.value)

    def test_config_class_rejects_missing_metadata(self):
        """Test that Config class rejects models with missing metadata."""

        @dataclass
        class BadConfig:
            api_key: str = field()  # Missing metadata

        with pytest.raises(ModelDefinitionError) as exc_info:
            Config(model=BadConfig, sources=[])

        assert exc_info.value.reason == "missing_metadata"


class TestConflictingMetadata:
    """Test cases for conflicting required/optional metadata."""

    def test_single_field_conflicting_metadata(self):
        """Test single field with both required and optional."""

        @dataclass
        class BadConfig:
            api_key: str = field(metadata={"required": True, "optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        assert exc_info.value.reason == "conflicting_metadata"
        assert "api_key" in str(exc_info.value)
        assert "both" in str(exc_info.value).lower() or "conflicting" in str(exc_info.value).lower()

    def test_multiple_fields_conflicting_metadata(self):
        """Test multiple fields with conflicting metadata."""

        @dataclass
        class BadConfig:
            api_key: str = field(metadata={"required": True, "optional": True})
            host: str = field(metadata={"required": True, "optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        assert exc_info.value.reason == "conflicting_metadata"

    def test_nested_field_conflicting_metadata(self):
        """Test nested field with conflicting metadata."""

        @dataclass
        class DBConfig:
            host: str = field(metadata={"required": True, "optional": True})

        @dataclass
        class AppConfig:
            db: DBConfig = field(metadata={"required": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(AppConfig)

        assert exc_info.value.reason == "conflicting_metadata"
        assert "db.host" in str(exc_info.value) or "host" in str(exc_info.value)

    def test_config_class_rejects_conflicting_metadata(self):
        """Test that Config class rejects models with conflicting metadata."""

        @dataclass
        class BadConfig:
            api_key: str = field(metadata={"required": True, "optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            Config(model=BadConfig, sources=[])

        assert exc_info.value.reason == "conflicting_metadata"


class TestOptionalTypeAnnotations:
    """Test cases for Optional[T] type annotation rejection."""

    def test_optional_str(self):
        """Test Optional[str] type annotation."""

        @dataclass
        class BadConfig:
            api_key: Optional[str] = field(metadata={"optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        assert exc_info.value.reason == "optional_type"
        assert "Optional" in str(exc_info.value)

    def test_optional_int(self):
        """Test Optional[int] type annotation."""

        @dataclass
        class BadConfig:
            port: Optional[int] = field(metadata={"optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        assert exc_info.value.reason == "optional_type"

    def test_optional_bool(self):
        """Test Optional[bool] type annotation."""

        @dataclass
        class BadConfig:
            debug: Optional[bool] = field(metadata={"optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        assert exc_info.value.reason == "optional_type"

    def test_optional_list(self):
        """Test Optional[List] type annotation."""

        @dataclass
        class BadConfig:
            items: Optional[List[str]] = field(metadata={"optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        assert exc_info.value.reason == "optional_type"

    def test_optional_dict(self):
        """Test Optional[Dict] type annotation."""

        @dataclass
        class BadConfig:
            settings: Optional[Dict[str, str]] = field(metadata={"optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        assert exc_info.value.reason == "optional_type"

    def test_union_none_str(self):
        """Test Union[str, None] type annotation."""

        @dataclass
        class BadConfig:
            api_key: Union[str, None] = field(metadata={"optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        assert exc_info.value.reason == "optional_type"

    def test_union_none_int(self):
        """Test Union[int, None] type annotation."""

        @dataclass
        class BadConfig:
            port: Union[int, None] = field(metadata={"optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        assert exc_info.value.reason == "optional_type"

    def test_nested_optional_type(self):
        """Test nested field with Optional type."""

        @dataclass
        class DBConfig:
            host: Optional[str] = field(metadata={"optional": True})

        @dataclass
        class AppConfig:
            db: DBConfig = field(metadata={"required": True})

        # Optional type is checked at the nested dataclass level, not at AppConfig level
        # So we need to validate DBConfig directly
        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(DBConfig)

        assert exc_info.value.reason == "optional_type"
        assert "host" in str(exc_info.value)

    def test_config_class_rejects_optional_type(self):
        """Test that Config class rejects models with Optional type."""

        @dataclass
        class BadConfig:
            api_key: Optional[str] = field(metadata={"optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            Config(model=BadConfig, sources=[])

        assert exc_info.value.reason == "optional_type"


class TestValidConfigurations:
    """Test cases for valid configurations."""

    def test_all_required_fields(self):
        """Test model with all required fields."""

        @dataclass
        class Config:
            api_key: str = field(metadata={"required": True})
            host: str = field(metadata={"required": True})
            port: int = field(metadata={"required": True})

        # Should not raise
        validate_model_definition(Config)

    def test_all_optional_fields(self):
        """Test model with all optional fields."""

        @dataclass
        class Config:
            api_key: str = field(default="", metadata={"optional": True})
            host: str = field(default="localhost", metadata={"optional": True})
            port: int = field(default=8000, metadata={"optional": True})

        # Should not raise
        validate_model_definition(Config)

    def test_mixed_required_and_optional(self):
        """Test model with mixed required and optional fields."""

        @dataclass
        class AppConfig:
            # Required fields first (no defaults)
            api_key: str = field(metadata={"required": True})
            port: int = field(metadata={"required": True})
            # Optional fields after (with defaults)
            host: str = field(default="localhost", metadata={"optional": True})
            debug: bool = field(default=False, metadata={"optional": True})

        # Should not raise
        validate_model_definition(AppConfig)

    def test_nested_valid_configuration(self):
        """Test nested configuration with valid metadata."""

        @dataclass
        class DBConfig:
            host: str = field(metadata={"required": True})
            port: int = field(default=5432, metadata={"optional": True})

        @dataclass
        class AppConfig:
            api_key: str = field(metadata={"required": True})
            db: DBConfig = field(metadata={"required": True})

        # Should not raise
        validate_model_definition(AppConfig)

    def test_config_class_accepts_valid_model(self):
        """Test that Config class accepts valid models."""

        @dataclass
        class AppConfig:
            api_key: str = field(metadata={"required": True})
            host: str = field(default="localhost", metadata={"optional": True})

        # Should not raise
        cfg = Config(model=AppConfig, sources=[])
        assert cfg is not None


class TestConfigIntegration:
    """Test Config class integration with validation."""

    def test_config_init_validates_model(self):
        """Test that Config.__init__ validates model definition."""

        @dataclass
        class BadConfig:
            api_key: str = field()  # Missing metadata

        with pytest.raises(ModelDefinitionError):
            Config(model=BadConfig, sources=[])

    def test_config_load_validates_required_fields(self):
        """Test that Config.load() validates required fields."""

        @dataclass
        class AppConfig:
            api_key: str = field(metadata={"required": True})
            host: str = field(default="localhost", metadata={"optional": True})

        cfg = Config(model=AppConfig, sources=[])

        with pytest.raises(RequiredFieldError) as exc_info:
            cfg.load()

        assert "api_key" in str(exc_info.value)

    def test_config_load_with_valid_data(self):
        """Test Config.load() with valid data."""
        import os

        @dataclass
        class AppConfig:
            api_key: str = field(metadata={"required": True})
            host: str = field(default="localhost", metadata={"optional": True})

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
            api_key: str = field(metadata={"required": True})
            host: str = field(default="localhost", metadata={"optional": True})

        cfg = Config(model=AppConfig, sources=[])

        # Should raise for missing required field
        with pytest.raises(RequiredFieldError):
            cfg.validate()

        # Should pass with valid data
        valid_config = {"api_key": "secret-key", "host": "0.0.0.0"}
        cfg.validate(valid_config)


class TestErrorMessages:
    """Test error message correctness."""

    def test_missing_metadata_error_message(self):
        """Test error message for missing metadata."""

        @dataclass
        class BadConfig:
            api_key: str = field()

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        error_msg = str(exc_info.value)
        assert "api_key" in error_msg
        assert "required" in error_msg.lower() or "optional" in error_msg.lower()
        assert "example" in error_msg.lower() or "field" in error_msg.lower()

    def test_conflicting_metadata_error_message(self):
        """Test error message for conflicting metadata."""

        @dataclass
        class BadConfig:
            api_key: str = field(metadata={"required": True, "optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        error_msg = str(exc_info.value)
        assert "api_key" in error_msg
        assert "both" in error_msg.lower() or "conflicting" in error_msg.lower()

    def test_optional_type_error_message(self):
        """Test error message for Optional type."""

        @dataclass
        class BadConfig:
            api_key: Optional[str] = field(metadata={"optional": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(BadConfig)

        error_msg = str(exc_info.value)
        assert "Optional" in error_msg
        assert "not allowed" in error_msg.lower() or "disallowed" in error_msg.lower()


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
            items: List[str] = field(default_factory=list, metadata={"optional": True})

        # Should not raise
        validate_model_definition(Config)

    def test_field_with_description(self):
        """Test field with description metadata."""

        @dataclass
        class Config:
            api_key: str = field(
                metadata={"required": True, "description": "API key for authentication"}
            )

        # Should not raise
        validate_model_definition(Config)

    def test_field_with_help(self):
        """Test field with help metadata."""

        @dataclass
        class Config:
            api_key: str = field(metadata={"required": True, "help": "Required API key"})

        # Should not raise
        validate_model_definition(Config)

    def test_field_with_all_metadata(self):
        """Test field with all metadata keys."""

        @dataclass
        class Config:
            api_key: str = field(
                metadata={"required": True, "description": "API key", "help": "Required API key"}
            )

        # Should not raise
        validate_model_definition(Config)

    def test_deeply_nested_configuration(self):
        """Test deeply nested configuration."""

        @dataclass
        class CacheConfig:
            enabled: bool = field(metadata={"required": True})

        @dataclass
        class DBConfig:
            host: str = field(metadata={"required": True})
            cache: CacheConfig = field(metadata={"required": True})

        @dataclass
        class AppConfig:
            db: DBConfig = field(metadata={"required": True})

        # Should not raise
        validate_model_definition(AppConfig)

    def test_multiple_nested_levels_with_errors(self):
        """Test multiple nested levels with errors."""

        @dataclass
        class CacheConfig:
            enabled: bool = field()  # Missing metadata

        @dataclass
        class DBConfig:
            host: str = field(metadata={"required": True})
            cache: CacheConfig = field(metadata={"required": True})

        @dataclass
        class AppConfig:
            db: DBConfig = field(metadata={"required": True})

        with pytest.raises(ModelDefinitionError) as exc_info:
            validate_model_definition(AppConfig)

        assert exc_info.value.reason == "missing_metadata"
        assert "cache.enabled" in str(exc_info.value) or "enabled" in str(exc_info.value)
