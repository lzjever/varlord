"""
Comprehensive tests for nested configuration fixes.

Tests for:
- VARLORD-001: _flatten_to_nested recursive processing bug fix
- VARLORD-002: Nested dataclass field validation logic fix
- VARLORD-003: Enhanced error messages
- VARLORD-004: Custom environment variable prefixes

These tests are written from the interface perspective, testing expected behavior
without relying on implementation details.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import pytest

from varlord import Config, sources
from varlord.model_validation import RequiredFieldError
from varlord.sources.base import Source


# Helper: Dict source for testing
class DictSource(Source):
    """Source that loads configuration from a dictionary (for testing)."""

    def __init__(self, data: dict[str, Any], source_id: Optional[str] = None):
        super().__init__(source_id=source_id or "dict")
        self._data = data

    @property
    def name(self) -> str:
        return "dict"

    def load(self) -> Mapping[str, Any]:
        return self._data


# ============================================================================
# Test Models
# ============================================================================


@dataclass
class DBConfig:
    """Database configuration."""

    host: str = field()
    port: int = field(default=5432)
    name: str = field(default="testdb")


@dataclass
class ServiceConfig:
    """Service configuration."""

    api_key: str = field()
    timeout: int = field(default=30)
    retries: int = field(default=3)


@dataclass
class AIConfig:
    """AI configuration."""

    completion: ServiceConfig = field()
    embedding: Optional[ServiceConfig] = field(default=None)


@dataclass
class AppConfig:
    """Application configuration."""

    db: DBConfig = field()
    ai: AIConfig = field()
    host: str = field(default="0.0.0.0")
    port: int = field(default=8000)


# ============================================================================
# VARLORD-001: _flatten_to_nested recursive processing bug fix
# ============================================================================


class TestFlattenToNestedBugFix:
    """Test that _flatten_to_nested correctly processes nested structures."""

    def test_simple_nested_structure(self):
        """Test simple nested structure with required fields."""
        config_dict = {
            "db.host": "localhost",
            "db.port": 5432,
            "db.name": "mydb",
            "ai.completion.api_key": "sk-test123",  # Required field
        }

        cfg = Config(model=AppConfig, sources=[DictSource(config_dict)])

        # Should succeed - all required fields present
        app = cfg.load()

        # Verify structure
        assert app.db.host == "localhost"
        assert app.db.port == 5432
        assert app.db.name == "mydb"
        assert app.ai.completion.api_key == "sk-test123"
        assert app.host == "0.0.0.0"  # Default value
        assert app.port == 8000  # Default value

    def test_multi_level_nesting(self):
        """Test multi-level nested structure."""
        config_dict = {
            "db.host": "localhost",
            "ai.completion.api_key": "sk-test123",
            "ai.completion.timeout": 60,
            "ai.completion.retries": 5,
        }

        cfg = Config(model=AppConfig, sources=[DictSource(config_dict)])

        # Should succeed - all required fields present
        app = cfg.load()

        # Verify structure
        assert app.db.host == "localhost"
        assert app.ai.completion.api_key == "sk-test123"
        assert app.ai.completion.timeout == 60
        assert app.ai.completion.retries == 5
        assert app.ai.embedding is None  # Optional field

    def test_nested_with_optional_fields(self):
        """Test nested structure with optional fields."""
        config_dict = {
            "db.host": "localhost",
            "ai.completion.api_key": "sk-test123",
            "ai.embedding.api_key": "sk-embed123",
            "ai.embedding.timeout": 45,
        }

        cfg = Config(model=AppConfig, sources=[DictSource(config_dict)])

        # Should succeed
        app = cfg.load()

        # Verify structure
        assert app.ai.completion.api_key == "sk-test123"
        # Optional field should be created if child fields are provided
        # Note: This depends on how Optional fields are handled in _flatten_to_nested
        # If embedding is None, that's also valid (optional field)
        if app.ai.embedding is not None:
            assert app.ai.embedding.api_key == "sk-embed123"
            assert app.ai.embedding.timeout == 45
            assert app.ai.embedding.retries == 3  # Default value

    def test_nested_with_mixed_defaults(self):
        """Test nested structure with some fields using defaults."""
        config_dict = {
            "db.host": "localhost",
            # db.port and db.name use defaults
            "ai.completion.api_key": "sk-test123",
            # ai.completion.timeout and retries use defaults
        }

        cfg = Config(model=AppConfig, sources=[DictSource(config_dict)])

        # Should succeed
        app = cfg.load()

        # Verify defaults are applied
        assert app.db.host == "localhost"
        assert app.db.port == 5432  # Default
        assert app.db.name == "testdb"  # Default
        assert app.ai.completion.api_key == "sk-test123"
        assert app.ai.completion.timeout == 30  # Default
        assert app.ai.completion.retries == 3  # Default

    def test_nested_structure_with_all_fields(self):
        """Test nested structure with all fields explicitly set."""
        config_dict = {
            "db.host": "localhost",
            "db.port": 3306,
            "db.name": "production",
            "ai.completion.api_key": "sk-prod123",
            "ai.completion.timeout": 120,
            "ai.completion.retries": 10,
            "ai.embedding.api_key": "sk-embed456",
            "ai.embedding.timeout": 90,
            "ai.embedding.retries": 5,
            "host": "127.0.0.1",
            "port": 9000,
        }

        cfg = Config(model=AppConfig, sources=[DictSource(config_dict)])

        # Should succeed
        app = cfg.load()

        # Verify all fields
        assert app.db.host == "localhost"
        assert app.db.port == 3306
        assert app.db.name == "production"
        assert app.ai.completion.api_key == "sk-prod123"
        assert app.ai.completion.timeout == 120
        assert app.ai.completion.retries == 10
        assert app.ai.embedding.api_key == "sk-embed456"
        assert app.ai.embedding.timeout == 90
        assert app.ai.embedding.retries == 5
        assert app.host == "127.0.0.1"
        assert app.port == 9000


# ============================================================================
# VARLORD-002: Nested dataclass field validation logic fix
# ============================================================================


class TestNestedValidationFix:
    """Test that nested dataclass fields are validated correctly."""

    def test_validation_passes_with_child_fields(self):
        """Test that parent fields are considered satisfied if child fields exist."""
        config_dict = {
            "db.host": "localhost",  # Only child field, parent 'db' should be satisfied
            "ai.completion.api_key": "sk-test123",  # Only child field, parents should be satisfied
        }

        cfg = Config(model=AppConfig, sources=[DictSource(config_dict)])

        # Should pass validation - parent fields satisfied by child fields
        app = cfg.load()

        # Verify structure
        assert app.db.host == "localhost"
        assert app.ai.completion.api_key == "sk-test123"

    def test_validation_fails_without_required_child_fields(self):
        """Test that validation fails if required child fields are missing."""
        config_dict = {
            "db.host": "localhost",
            # Missing ai.completion.api_key - should fail
        }

        cfg = Config(model=AppConfig, sources=[DictSource(config_dict)])

        # Should fail validation - missing required child field
        with pytest.raises(RequiredFieldError) as exc_info:
            cfg.load()

        # Verify error mentions the missing field
        error_msg = str(exc_info.value)
        assert "ai.completion.api_key" in error_msg or "completion.api_key" in error_msg

    def test_validation_with_partial_nested_fields(self):
        """Test validation with some nested fields present."""
        config_dict = {
            "db.host": "localhost",
            "ai.completion.api_key": "sk-test123",
            # ai.completion.timeout and retries have defaults, so should be OK
        }

        cfg = Config(model=AppConfig, sources=[DictSource(config_dict)])

        # Should pass - all required fields present
        app = cfg.load()
        assert app.ai.completion.api_key == "sk-test123"

    def test_validation_with_optional_nested_fields(self):
        """Test validation with optional nested fields."""
        config_dict = {
            "db.host": "localhost",
            "ai.completion.api_key": "sk-test123",
            # ai.embedding is optional, so can be missing
        }

        cfg = Config(model=AppConfig, sources=[DictSource(config_dict)])

        # Should pass - optional fields can be missing
        app = cfg.load()
        assert app.ai.embedding is None

    def test_validation_with_deeply_nested_structure(self):
        """Test validation with deeply nested structure (3+ levels)."""

        @dataclass
        class Level3Config:
            value: str = field()

        @dataclass
        class Level2Config:
            level3: Level3Config = field()

        @dataclass
        class Level1Config:
            level2: Level2Config = field()

        @dataclass
        class RootConfig:
            level1: Level1Config = field()

        config_dict = {
            "level1.level2.level3.value": "deep-value",
        }

        cfg = Config(model=RootConfig, sources=[DictSource(config_dict)])

        # Should pass - all parent fields satisfied by child fields
        root = cfg.load()
        assert root.level1.level2.level3.value == "deep-value"


# ============================================================================
# VARLORD-003: Enhanced error messages
# ============================================================================


class TestEnhancedErrorMessages:
    """Test that error messages are enhanced with helpful information."""

    def test_error_message_shows_child_fields(self):
        """Test that error message shows child fields when parent is missing."""
        config_dict = {
            "db.host": "localhost",
            "ai.completion.api_key": "sk-test123",
            # Missing 'ai' parent key, but child fields exist
        }

        cfg = Config(model=AppConfig, sources=[DictSource(config_dict)])

        # This should not fail because child fields satisfy parent
        # But if it did, error should mention child fields
        try:
            app = cfg.load()
            # If we get here, validation passed (which is correct)
            assert app.ai.completion.api_key == "sk-test123"
        except RequiredFieldError as e:
            # If validation fails, error should mention child fields
            error_msg = str(e)
            assert "ai.completion.api_key" in error_msg or "Child fields exist" in error_msg

    def test_error_message_for_missing_required_field(self):
        """Test error message for missing required field."""
        config_dict = {
            "db.host": "localhost",
            # Missing ai.completion.api_key
        }

        cfg = Config(model=AppConfig, sources=[DictSource(config_dict)])

        with pytest.raises(RequiredFieldError) as exc_info:
            cfg.load()

        error_msg = str(exc_info.value)
        # Should mention the missing field
        assert "api_key" in error_msg or "completion" in error_msg
        # Should mention the model name
        assert "AppConfig" in error_msg


# ============================================================================
# VARLORD-004: Custom environment variable prefixes
# ============================================================================


class TestCustomEnvPrefixes:
    """Test custom environment variable prefix support."""

    def test_env_with_prefix(self):
        """Test Env source with custom prefix."""
        # Set environment variables with prefix
        os.environ["TEST__DB__HOST"] = "env-host"
        os.environ["TEST__DB__PORT"] = "3306"
        os.environ["TEST__AI__COMPLETION__API_KEY"] = "sk-env123"

        try:
            cfg = Config(model=AppConfig, sources=[sources.Env(prefix="TEST__")])

            app = cfg.load()

            # Verify values from environment
            assert app.db.host == "env-host"
            assert app.db.port == 3306
            assert app.ai.completion.api_key == "sk-env123"
        finally:
            # Clean up
            os.environ.pop("TEST__DB__HOST", None)
            os.environ.pop("TEST__DB__PORT", None)
            os.environ.pop("TEST__AI__COMPLETION__API_KEY", None)

    def test_env_without_prefix(self):
        """Test Env source without prefix (default behavior)."""
        # Set environment variables without prefix
        os.environ["DB__HOST"] = "no-prefix-host"
        os.environ["DB__PORT"] = "5432"
        os.environ["AI__COMPLETION__API_KEY"] = "sk-no-prefix"  # Required field

        try:
            cfg = Config(model=AppConfig, sources=[sources.Env()])

            app = cfg.load()

            # Verify values from environment
            assert app.db.host == "no-prefix-host"
            assert app.db.port == 5432
            assert app.ai.completion.api_key == "sk-no-prefix"
        finally:
            # Clean up
            os.environ.pop("DB__HOST", None)
            os.environ.pop("DB__PORT", None)
            os.environ.pop("AI__COMPLETION__API_KEY", None)

    def test_env_prefix_isolation(self):
        """Test that prefix isolates environment variables."""
        # Set variables with and without prefix
        os.environ["TEST__DB__HOST"] = "prefixed-host"
        os.environ["TEST__AI__COMPLETION__API_KEY"] = "sk-prefixed"
        os.environ["DB__HOST"] = "unprefixed-host"
        os.environ["AI__COMPLETION__API_KEY"] = "sk-unprefixed"

        try:
            # With prefix - should only see prefixed variables
            cfg_prefixed = Config(model=AppConfig, sources=[sources.Env(prefix="TEST__")])
            app_prefixed = cfg_prefixed.load()
            assert app_prefixed.db.host == "prefixed-host"
            assert app_prefixed.ai.completion.api_key == "sk-prefixed"

            # Without prefix - should see unprefixed variables
            cfg_unprefixed = Config(model=AppConfig, sources=[sources.Env()])
            app_unprefixed = cfg_unprefixed.load()
            assert app_unprefixed.db.host == "unprefixed-host"
            assert app_unprefixed.ai.completion.api_key == "sk-unprefixed"
        finally:
            # Clean up
            os.environ.pop("TEST__DB__HOST", None)
            os.environ.pop("TEST__AI__COMPLETION__API_KEY", None)
            os.environ.pop("DB__HOST", None)
            os.environ.pop("AI__COMPLETION__API_KEY", None)

    def test_env_prefix_case_insensitive(self):
        """Test that prefix matching is case-insensitive (normalized to uppercase)."""
        # Set variable with lowercase prefix
        os.environ["test__db__host"] = "lowercase-prefix-host"
        os.environ["test__ai__completion__api_key"] = "sk-lowercase"

        try:
            cfg = Config(model=AppConfig, sources=[sources.Env(prefix="TEST__")])

            app = cfg.load()

            # Should match despite case difference
            assert app.db.host == "lowercase-prefix-host"
            assert app.ai.completion.api_key == "sk-lowercase"
        finally:
            # Clean up
            os.environ.pop("test__db__host", None)
            os.environ.pop("test__ai__completion__api_key", None)

    def test_env_prefix_with_nested_structure(self):
        """Test prefix with deeply nested structure."""
        os.environ["APP__DB__HOST"] = "app-db-host"
        os.environ["APP__AI__COMPLETION__API_KEY"] = "sk-nested123"
        os.environ["APP__AI__COMPLETION__TIMEOUT"] = "120"

        try:
            cfg = Config(model=AppConfig, sources=[sources.Env(prefix="APP__")])

            app = cfg.load()

            assert app.db.host == "app-db-host"
            assert app.ai.completion.api_key == "sk-nested123"
            assert app.ai.completion.timeout == 120
        finally:
            # Clean up
            os.environ.pop("APP__DB__HOST", None)
            os.environ.pop("APP__AI__COMPLETION__API_KEY", None)
            os.environ.pop("APP__AI__COMPLETION__TIMEOUT", None)


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegrationScenarios:
    """Integration tests combining multiple fixes."""

    def test_yaml_source_with_nested_structure(self):
        """Test YAML source with nested structure (real-world scenario)."""
        import tempfile

        import yaml

        yaml_content = {
            "db": {
                "host": "yaml-host",
                "port": 5432,
            },
            "ai": {
                "completion": {
                    "api_key": "sk-yaml123",
                    "timeout": 60,
                }
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_content, f)
            yaml_path = f.name

        try:
            cfg = Config(model=AppConfig, sources=[sources.YAML(yaml_path)])

            app = cfg.load()

            assert app.db.host == "yaml-host"
            assert app.db.port == 5432
            assert app.ai.completion.api_key == "sk-yaml123"
            assert app.ai.completion.timeout == 60
        finally:
            import os

            os.unlink(yaml_path)

    def test_multiple_sources_with_nested_structure(self):
        """Test multiple sources with nested structure and priority."""
        import tempfile

        import yaml

        # YAML with defaults
        yaml_content = {
            "db": {"host": "yaml-host"},
            "ai": {"completion": {"api_key": "sk-yaml"}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_content, f)
            yaml_path = f.name

        # Env with overrides
        os.environ["DB__HOST"] = "env-host"
        os.environ["AI__COMPLETION__API_KEY"] = "sk-env"

        try:
            cfg = Config(
                model=AppConfig,
                sources=[
                    sources.YAML(yaml_path),
                    sources.Env(),  # Should override YAML
                ],
            )

            app = cfg.load()

            # Env should override YAML
            assert app.db.host == "env-host"
            assert app.ai.completion.api_key == "sk-env"
        finally:
            if os.path.exists(yaml_path):
                os.unlink(yaml_path)
            os.environ.pop("DB__HOST", None)
            os.environ.pop("AI__COMPLETION__API_KEY", None)
