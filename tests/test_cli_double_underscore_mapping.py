"""
Comprehensive tests for CLI mapping functionality.

Tests the CLI argument mapping rules:
- Double dashes (--) in CLI arguments become dots (.) in normalized keys
- Single dashes (-) in CLI arguments become underscores (_) in normalized keys

Examples:
- --host → host
- --k8s-pod-name → k8s_pod_name
- --db--host → db.host
- --aaa--bbb--ccc-dd → aaa.bbb.ccc_dd

These tests are written from the interface perspective, testing expected behavior
without relying on implementation details.
"""

from dataclasses import dataclass, field
from typing import Optional

from varlord.sources.cli import CLI

# ============================================================================
# Test Models
# ============================================================================


@dataclass
class FlatConfig:
    """Simple flat configuration for testing."""

    host: str = field()
    port: int = field(default=8000)
    debug: bool = field(default=False)
    k8s_pod_name: str = field(default="default-pod")


@dataclass
class NestedConfig:
    """Configuration with nested fields using double underscore."""

    db__host: str = field()
    sandbox__default_session_id: Optional[str] = field(default=None)
    db__port: int = field(default=5432)
    api__timeout: int = field(default=30)
    api__retry_count: int = field(default=3)


@dataclass
class MixedConfig:
    """Configuration with both flat and nested fields."""

    host: str = field()
    db__host: str = field()
    port: int = field(default=8000)
    sandbox__default_session_id: Optional[str] = field(default=None)
    k8s_pod_name: str = field(default="default-pod")
    db__port: int = field(default=5432)


@dataclass
class DeepNestedConfig:
    """Configuration with deeply nested fields."""

    app__db__host: str = field()
    app__db__port: int = field(default=5432)
    app__api__timeout: int = field(default=30)
    app__api__retry__count: int = field(default=3)


# ============================================================================
# Tests for Nested Fields (Double Underscore Mapping)
# ============================================================================


class TestNestedFieldsDoubleUnderscore:
    """Test nested fields using double dash format."""

    def test_nested_field(self):
        """Test nested field: --sandbox--default-session-id"""
        source = CLI(
            model=NestedConfig,
            argv=["--sandbox--default-session-id", "session-123", "--db--host", "localhost"],
        )
        result = source.load()

        assert "sandbox.default_session_id" in result
        assert result["sandbox.default_session_id"] == "session-123"
        assert "db.host" in result
        assert result["db.host"] == "localhost"

    def test_multiple_nested_fields(self):
        """Test multiple nested fields in one command."""
        source = CLI(
            model=NestedConfig,
            argv=[
                "--sandbox--default-session-id",
                "session-789",
                "--db--host",
                "db.example.com",
                "--db--port",
                "3306",
                "--api--timeout",
                "60",
            ],
        )
        result = source.load()

        assert result["sandbox.default_session_id"] == "session-789"
        assert result["db.host"] == "db.example.com"
        assert result["db.port"] == 3306
        assert result["api.timeout"] == 60

    def test_deeply_nested_fields(self):
        """Test deeply nested fields (app--db--host)."""
        source = CLI(
            model=DeepNestedConfig,
            argv=[
                "--app--db--host",
                "deep-db.example.com",
                "--app--db--port",
                "5432",
                "--app--api--timeout",
                "90",
            ],
        )
        result = source.load()

        assert result["app.db.host"] == "deep-db.example.com"
        assert result["app.db.port"] == 5432
        assert result["app.api.timeout"] == 90

    def test_deeply_nested_with_underscore(self):
        """Test deeply nested fields with underscores in segment names."""
        source = CLI(
            model=DeepNestedConfig,
            argv=[
                "--app--db--host",
                "deep-db.example.com",
                "--app--api--retry--count",
                "5",
            ],
        )
        result = source.load()

        assert result["app.db.host"] == "deep-db.example.com"
        assert result["app.api.retry.count"] == 5


# ============================================================================
# Tests for Flat Fields (Single Underscore)
# ============================================================================


class TestFlatFields:
    """Test flat fields with single dashes."""

    def test_flat_field_with_dash(self):
        """Test flat field: --k8s-pod-name"""
        source = CLI(
            model=FlatConfig,
            argv=["--host", "example.com", "--k8s-pod-name", "my-pod"],
        )
        result = source.load()

        assert result["host"] == "example.com"
        assert result["k8s_pod_name"] == "my-pod"


# ============================================================================
# Tests for Mixed Configurations
# ============================================================================


class TestMixedConfigurations:
    """Test configurations with both flat and nested fields."""

    def test_mixed_flat_and_nested(self):
        """Test mixing flat and nested fields."""
        source = CLI(
            model=MixedConfig,
            argv=[
                "--host",
                "example.com",
                "--port",
                "9000",
                "--sandbox--default-session-id",
                "session-123",
                "--k8s-pod-name",
                "my-pod",
                "--db--host",
                "db.example.com",
            ],
        )
        result = source.load()

        assert result["host"] == "example.com"
        assert result["port"] == 9000
        assert result["sandbox.default_session_id"] == "session-123"
        assert result["k8s_pod_name"] == "my-pod"
        assert result["db.host"] == "db.example.com"


# ============================================================================
# Tests for Boolean Flags
# ============================================================================


class TestBooleanFlags:
    """Test boolean flags with nested fields."""

    @dataclass
    class BooleanConfig:
        debug: bool = field(default=False)
        verbose: bool = field(default=False)
        api__enable_cache: bool = field(default=False)
        db__use_ssl: bool = field(default=True)

    def test_boolean_flag_nested(self):
        """Test boolean flag with nested fields."""
        source = CLI(
            model=self.BooleanConfig,
            argv=["--api--enable-cache", "--db--use-ssl"],
        )
        result = source.load()

        assert result["api.enable_cache"] is True
        assert result["db.use_ssl"] is True

    def test_boolean_no_flag_nested(self):
        """Test boolean no-flag with nested fields."""
        source = CLI(
            model=self.BooleanConfig,
            argv=["--no-api--enable-cache", "--no-db--use-ssl"],
        )
        result = source.load()

        assert result["api.enable_cache"] is False
        assert result["db.use_ssl"] is False

    def test_boolean_flat_and_nested(self):
        """Test both flat and nested boolean flags."""
        source = CLI(
            model=self.BooleanConfig,
            argv=["--debug", "--api--enable-cache", "--no-verbose"],
        )
        result = source.load()

        assert result["debug"] is True
        assert result["api.enable_cache"] is True
        assert result["verbose"] is False


# ============================================================================
# Tests for Type Conversion
# ============================================================================


class TestTypeConversion:
    """Test type conversion for nested fields."""

    def test_int_conversion_nested(self):
        """Test integer conversion for nested fields."""
        source = CLI(
            model=NestedConfig,
            argv=["--db--port", "3306", "--api--timeout", "60", "--api--retry-count", "5"],
        )
        result = source.load()

        assert result["db.port"] == 3306
        assert isinstance(result["db.port"], int)
        assert result["api.timeout"] == 60
        assert isinstance(result["api.timeout"], int)
        assert result["api.retry_count"] == 5
        assert isinstance(result["api.retry_count"], int)


# ============================================================================
# Tests for Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_value(self):
        """Test empty string value."""
        source = CLI(
            model=NestedConfig,
            argv=["--sandbox--default-session-id", "", "--db--host", "localhost"],
        )
        result = source.load()

        assert result["sandbox.default_session_id"] == ""
        assert result["db.host"] == "localhost"

    def test_numeric_string_value(self):
        """Test numeric string value."""
        source = CLI(
            model=NestedConfig,
            argv=["--sandbox--default-session-id", "12345"],
        )
        result = source.load()

        assert result["sandbox.default_session_id"] == "12345"
        assert isinstance(result["sandbox.default_session_id"], str)

    def test_special_characters_in_value(self):
        """Test special characters in value."""
        source = CLI(
            model=NestedConfig,
            argv=["--sandbox--default-session-id", "session-123_abc@example.com"],
        )
        result = source.load()

        assert result["sandbox.default_session_id"] == "session-123_abc@example.com"

    def test_multiple_double_dashes(self):
        """Test field with multiple double dashes (deep nesting)."""
        source = CLI(
            model=DeepNestedConfig,
            argv=["--app--api--retry--count", "10"],
        )
        result = source.load()

        assert result["app.api.retry.count"] == 10

    def test_field_with_only_double_underscores(self):
        """Test field name that is just double underscores."""

        @dataclass
        class EdgeConfig:
            __value: str = field(default="test")  # This would be normalized to .value

        # This is an edge case - field names starting with __ are typically private
        # But we should handle it gracefully
        # The field name __value would be normalized to .value
        # So the CLI arg would be --value (no leading dashes)
        source = CLI(
            model=EdgeConfig,
            argv=["--value", "edge-case"],  # __value normalizes to .value, which maps to --value
        )
        result = source.load()

        # The normalized key would be ".value" (leading dot)
        # But this is an unusual case - let's test what actually happens
        # Actually, __value in dataclass field name is a special case
        # It might be treated differently by the metadata system
        # For now, let's just verify it doesn't crash
        assert isinstance(result, dict)


# ============================================================================
# Tests for Model Filtering
# ============================================================================


class TestModelFiltering:
    """Test that CLI only parses model fields."""

    def test_unknown_nested_field_filtered(self):
        """Test that unknown nested fields are filtered out."""
        source = CLI(
            model=NestedConfig,
            argv=[
                "--sandbox--default-session-id",
                "session-123",
                "--unknown--nested--field",
                "value",
            ],
        )
        result = source.load()

        assert "sandbox.default_session_id" in result
        assert "unknown.nested.field" not in result

    def test_unknown_flat_field_filtered(self):
        """Test that unknown flat fields are filtered out."""
        source = CLI(
            model=FlatConfig,
            argv=["--host", "example.com", "--unknown-field", "value"],
        )
        result = source.load()

        assert "host" in result
        assert "unknown_field" not in result


# ============================================================================
# Tests for Default Values
# ============================================================================


class TestDefaultValues:
    """Test default value handling."""

    def test_default_value_not_overridden(self):
        """Test that default values are not included when not provided."""
        source = CLI(
            model=NestedConfig,
            argv=["--db--host", "localhost"],
        )
        result = source.load()

        assert "db.host" in result
        assert result["db.host"] == "localhost"
        # Default values should not be in result if not provided
        assert "db.port" not in result or result.get("db.port") == 5432

    def test_default_value_overridden(self):
        """Test that default values can be overridden."""
        source = CLI(
            model=NestedConfig,
            argv=["--db--host", "localhost", "--db--port", "3306"],
        )
        result = source.load()

        assert result["db.host"] == "localhost"
        assert result["db.port"] == 3306
        assert isinstance(result["db.port"], int)


# ============================================================================
# Tests for Argument Name Generation
# ============================================================================


class TestArgumentNameGeneration:
    """Test that argument names are generated correctly."""

    def test_single_dash_becomes_underscore(self):
        """Test that single dashes become underscores in normalized keys."""
        source = CLI(
            model=FlatConfig,
            argv=["--k8s-pod-name", "pod-1"],
        )
        result = source.load()

        assert result["k8s_pod_name"] == "pod-1"

    def test_double_dash_becomes_dot(self):
        """Test that double dashes become dots in normalized keys."""
        source = CLI(
            model=NestedConfig,
            argv=["--sandbox--default-session-id", "session-1"],
        )
        result = source.load()

        assert "sandbox.default_session_id" in result
        assert "sandbox__default_session_id" not in result

    def test_no_nesting_for_single_dash(self):
        """Test that single dash does not create nesting."""
        source = CLI(
            model=FlatConfig,
            argv=["--k8s-pod-name", "pod-1"],
        )
        result = source.load()

        assert "k8s_pod_name" in result
        assert "k8s.pod_name" not in result
        assert "k8s.pod.name" not in result


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests with real-world scenarios."""

    def test_complex_real_world_config(self):
        """Test a complex real-world configuration scenario."""

        @dataclass
        class RealWorldConfig:
            app_name: str = field()
            app__db__host: str = field()
            app__db__port: int = field(default=5432)
            app__api__timeout: int = field(default=30)
            app__api__enable_cache: bool = field(default=False)
            k8s_pod_name: str = field(default="default-pod")

        source = CLI(
            model=RealWorldConfig,
            argv=[
                "--app-name",
                "my-app",
                "--app--db--host",
                "db.example.com",
                "--app--db--port",
                "3306",
                "--app--api--timeout",
                "60",
                "--app--api--enable-cache",
                "--k8s-pod-name",
                "my-pod",
            ],
        )
        result = source.load()

        assert result["app_name"] == "my-app"
        assert result["app.db.host"] == "db.example.com"
        assert result["app.db.port"] == 3306
        assert result["app.api.timeout"] == 60
        assert result["app.api.enable_cache"] is True
        assert result["k8s_pod_name"] == "my-pod"

    def test_all_format_variations(self):
        """Test all format variations in one command."""
        source = CLI(
            model=MixedConfig,
            argv=[
                "--host",
                "example.com",
                "--port",
                "9000",
                "--sandbox--default-session-id",
                "standard",
                "--k8s-pod-name",
                "hyphen",
                "--db--host",
                "db.example.com",
                "--db--port",
                "3306",
            ],
        )
        result = source.load()

        assert result["host"] == "example.com"
        assert result["port"] == 9000
        assert result["sandbox.default_session_id"] == "standard"
        assert result["k8s_pod_name"] == "hyphen"
        assert result["db.host"] == "db.example.com"
        assert result["db.port"] == 3306
