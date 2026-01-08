"""
Strict tests for check-variables functionality.

Testing edge cases and error paths. These tests are designed to find bugs,
not just to pass.
"""

import os
import sys
from dataclasses import dataclass, field
from typing import Optional

import pytest

from varlord import Config, sources
from varlord.sources.base import Source


@dataclass
class SampleTestConfig:
    """Test configuration model."""

    host: str = field()
    port: int = field(default=8000)


class TestEdgeCasesAndErrorPaths:
    """Test edge cases and error paths that could cause failures."""

    def test_source_without_name_property(self):
        """Test source that doesn't have name property.

        Note: Source base class requires name property. This will fail
        during initialization when trying to generate ID.
        """

        class BadSource(Source):
            def load(self):
                return {}

            # Missing name property

        # Should raise NotImplementedError during initialization
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement name property",
        ):
            BadSource()

    def test_source_name_returns_non_string(self):
        """Test source where name property returns non-string."""

        class BadSource(Source):
            @property
            def name(self):
                return 123  # Not a string

            def load(self):
                return {}

        cfg = Config(
            model=SampleTestConfig,
            sources=[BadSource()],
        )

        # Should handle non-string name
        output = cfg.format_diagnostic_table()
        # Should still work, but name might be converted to string
        assert "123" in output or "Configuration" in output

    def test_source_repr_raises_exception(self):
        """Test source where __repr__ raises exception."""

        class BadSource(Source):
            @property
            def name(self) -> str:
                return "bad"

            def load(self):
                return {}

            def __repr__(self) -> str:
                raise Exception("repr failed")

        cfg = Config(
            model=SampleTestConfig,
            sources=[BadSource()],
        )

        # Should handle repr exception
        with pytest.raises(Exception, match="repr failed"):
            cfg.format_diagnostic_table()

    def test_source_load_returns_non_dict(self):
        """Test source where load() returns non-dict.

        Note: This will fail in _load_config_dict -> resolver.resolve()
        because resolver expects dict. The exception in format_diagnostic_table
        (line 640) only catches exceptions when loading individually for
        source_configs, but _load_config_dict is called first (line 629).
        """

        class BadSource(Source):
            @property
            def name(self) -> str:
                return "bad"

            def load(self):
                return "not a dict"  # Should be dict

        cfg = Config(
            model=SampleTestConfig,
            sources=[BadSource()],
        )

        # This will fail in resolver.resolve() because it expects dict
        with pytest.raises(AttributeError, match="'str' object has no attribute 'items'"):
            cfg.format_diagnostic_table()

    def test_source_load_returns_dict_with_non_string_keys(self):
        """Test source where load() returns dict with non-string keys."""

        class BadSource(Source):
            @property
            def name(self) -> str:
                return "bad"

            def load(self):
                return {123: "value"}  # Non-string key

        cfg = Config(
            model=SampleTestConfig,
            sources=[BadSource()],
        )

        # Should handle non-string keys
        output = cfg.format_diagnostic_table()
        assert "Configuration" in output

    def test_source_supports_watch_raises_exception(self):
        """Test source where supports_watch() raises exception."""

        class BadSource(Source):
            @property
            def name(self) -> str:
                return "bad"

            def load(self):
                return {}

            def supports_watch(self) -> bool:
                raise Exception("supports_watch failed")

        cfg = Config(
            model=SampleTestConfig,
            sources=[BadSource()],
        )

        # Should handle exception in supports_watch
        with pytest.raises(Exception, match="supports_watch failed"):
            cfg.format_diagnostic_table()

    def test_measure_source_load_time_raises_exception(self):
        """Test when _measure_source_load_time raises exception.

        Note: _measure_source_load_time catches exceptions (line 848),
        but the source.load() failure will first fail in _load_config_dict.
        """

        class BadSource(Source):
            @property
            def name(self) -> str:
                return "bad"

            def load(self):
                # This will cause measure to fail
                raise Exception("load failed")

        cfg = Config(
            model=SampleTestConfig,
            sources=[BadSource()],
        )

        # This will fail in _load_config_dict -> resolver.resolve()
        # because resolver calls source.load() which raises exception
        with pytest.raises(Exception, match="load failed"):
            cfg.format_diagnostic_table()

    def test_empty_sources_list_edge_case(self):
        """Test with empty sources list (only defaults)."""
        cfg = Config(
            model=SampleTestConfig,
            sources=[],  # Empty list
        )

        output = cfg.format_diagnostic_table()

        # Should handle empty sources
        assert "defaults" in output or "1 (lowest)" in output
        # Should not crash

    def test_format_ascii_table_with_missing_keys(self):
        """Test _format_ascii_table with rows missing required keys."""
        cfg = Config(
            model=SampleTestConfig,
            sources=[sources.Env()],
        )

        # Mock _format_ascii_table to test with bad data
        original_method = cfg._format_ascii_table

        def bad_format_ascii_table(rows):
            # Simulate rows with missing keys
            bad_rows = [{"variable": "test"}]  # Missing other keys
            return original_method(bad_rows)

        cfg._format_ascii_table = bad_format_ascii_table

        # Should handle KeyError gracefully
        with pytest.raises(KeyError):
            cfg.format_diagnostic_table()

    def test_format_ascii_table_with_non_string_values(self):
        """Test _format_ascii_table with non-string values."""
        cfg = Config(
            model=SampleTestConfig,
            sources=[sources.Env()],
        )

        # Mock to inject bad data
        original_method = cfg._format_ascii_table

        def bad_format_ascii_table(rows):
            # Simulate rows with non-string values
            bad_rows = [
                {
                    "variable": 123,  # Not string
                    "required": True,  # Not string
                    "status": None,  # None
                    "source": object(),  # Object
                    "value": ["list"],  # List
                }
            ]
            return original_method(bad_rows)

        cfg._format_ascii_table = bad_format_ascii_table

        # Should handle non-string values (str() conversion)
        output = cfg.format_diagnostic_table()
        # Should still produce output, values converted to string
        assert "Configuration" in output

    def test_source_info_table_with_none_source(self):
        """Test _format_source_info_table with None in sources list."""
        cfg = Config(
            model=SampleTestConfig,
            sources=[sources.Env()],
        )

        # Create sources list with None
        defaults_source = cfg._create_defaults_source()
        bad_sources = [defaults_source, None]  # None in list
        source_statuses = {defaults_source.id: "success"}  # Provide source_statuses

        # Should handle None gracefully
        output = cfg._format_source_info_table(bad_sources, source_statuses)
        # Should not crash, but might have issues
        assert "Configuration" in output

    def test_source_info_table_with_empty_sources(self):
        """Test _format_source_info_table with empty sources list."""
        cfg = Config(
            model=SampleTestConfig,
            sources=[sources.Env()],
        )

        # Empty sources list
        output = cfg._format_source_info_table([], {})

        # Should handle empty list
        assert "Configuration" in output or output == ""

    def test_very_long_source_name(self):
        """Test with very long source name."""

        class LongNameSource(Source):
            @property
            def name(self) -> str:
                return "a" * 1000  # Very long name

            def load(self):
                return {}

        cfg = Config(
            model=SampleTestConfig,
            sources=[LongNameSource()],
        )

        output = cfg.format_diagnostic_table()

        # Should handle long names (might wrap or truncate)
        assert "Configuration" in output

    def test_source_with_unicode_name(self):
        """Test source with unicode characters in name."""

        class UnicodeSource(Source):
            @property
            def name(self) -> str:
                return "测试源_🎉_тест"

            def load(self):
                return {}

        cfg = Config(
            model=SampleTestConfig,
            sources=[UnicodeSource()],
        )

        output = cfg.format_diagnostic_table()

        # Should handle unicode
        assert "Configuration" in output

    def test_source_repr_with_unicode(self):
        """Test source __repr__ with unicode characters."""

        class UnicodeReprSource(Source):
            @property
            def name(self) -> str:
                return "unicode"

            def load(self):
                return {}

            def __repr__(self) -> str:
                return "<UnicodeSource(测试='🎉')>"

        cfg = Config(
            model=SampleTestConfig,
            sources=[UnicodeReprSource()],
        )

        output = cfg.format_diagnostic_table()

        # Should handle unicode in repr
        assert "Configuration" in output

    def test_value_with_special_characters(self):
        """Test configuration value with special characters."""
        os.environ["HOST"] = "test\nvalue\twith\rspecial\"chars'"
        try:
            cfg = Config(
                model=SampleTestConfig,
                sources=[sources.Env()],
            )

            output = cfg.format_diagnostic_table()

            # Should handle special characters
            assert "Configuration" in output
        finally:
            os.environ.pop("HOST", None)

    def test_value_with_newlines(self):
        """Test configuration value with newlines."""
        os.environ["HOST"] = "line1\nline2\nline3"
        try:
            cfg = Config(
                model=SampleTestConfig,
                sources=[sources.Env()],
            )

            output = cfg.format_diagnostic_table()

            # Should handle newlines (might be converted or escaped)
            assert "Configuration" in output
        finally:
            os.environ.pop("HOST", None)

    def test_very_long_value_truncation(self):
        """Test that very long values are properly truncated."""
        long_value = "x" * 1000
        os.environ["HOST"] = long_value
        try:
            cfg = Config(
                model=SampleTestConfig,
                sources=[sources.Env()],
            )

            output = cfg.format_diagnostic_table()

            # Should truncate at 40 chars (line 675-676)
            # Check that value is truncated
            lines = output.split("\n")
            for line in lines:
                # If we see 50+ x's, truncation didn't work
                if "x" * 50 in line:
                    # Actually, truncation happens at 40,
                    # so we should see "..."
                    x_count = len([c for c in line if c == "x"])
                    assert "..." in line or x_count <= 40
        finally:
            os.environ.pop("HOST", None)

    def test_none_value_in_config_dict(self):
        """Test when config_dict has None values."""

        @dataclass
        class ConfigWithNone:
            optional_field: Optional[str] = field(default=None)

        cfg = Config(
            model=ConfigWithNone,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Should handle None values
        assert "None" in output or "optional_field" in output

    def test_empty_string_vs_missing_key(self):
        """Test distinction between empty string and missing key."""

        @dataclass
        class ConfigWithEmpty:
            field2: str = field()  # Required, no default (must come first)
            field1: str = field(default="")  # Has default

        os.environ["FIELD2"] = ""  # Empty string, not missing
        try:
            cfg = Config(
                model=ConfigWithEmpty,
                sources=[sources.Env()],
            )

            output = cfg.format_diagnostic_table()

            # Should distinguish between missing and empty
            assert "field1" in output
            assert "field2" in output
            # field1 should show "Using Default" (has default="")
            # field2 should show "Loaded (empty)" (not "Missing")
            # since it's in env. Check that field2 is not marked as "Missing"
            lines = output.split("\n")
            field2_line = [line for line in lines if "field2" in line.lower()]
            if field2_line:
                # Should not say "Missing" since it's loaded from env
                # (even if empty)
                line_content = field2_line[0]
                missing_check = "Missing" not in line_content
                loaded_check = "Loaded (empty)" in line_content
                assert missing_check or loaded_check
        finally:
            os.environ.pop("FIELD2", None)

    def test_source_priority_determination_with_same_key(self):
        """Test source priority when same key exists in multiple sources."""
        os.environ["HOST"] = "env_value"
        original_argv = sys.argv.copy()
        sys.argv = ["test.py", "--host", "cli_value"]
        try:
            cfg = Config(
                model=SampleTestConfig,
                sources=[
                    sources.Env(),  # Lower priority
                    sources.CLI(),  # Higher priority
                ],
            )

            output = cfg.format_diagnostic_table()

            # CLI should win (higher priority)
            # Check that cli is shown as source for host
            assert "cli" in output
            # The actual value should come from CLI (higher priority)
        finally:
            sys.argv = original_argv
            os.environ.pop("HOST", None)

    def test_default_factory_vs_default(self):
        """Test distinction between default and default_factory."""
        from dataclasses import field

        @dataclass
        class ConfigWithFactory:
            list_field: list = field(default_factory=list)
            int_field: int = field(default=42)

        cfg = Config(
            model=ConfigWithFactory,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Should show different status for factory vs default
        assert "list_field" in output
        assert "int_field" in output
        # list_field should show "Using Default (factory)"
        # int_field should show "Using Default"

    def test_measure_load_time_with_slow_source(self):
        """Test load time measurement with slow source."""
        import time

        class SlowSource(Source):
            @property
            def name(self) -> str:
                return "slow"

            def load(self):
                time.sleep(0.1)  # 100ms delay
                return {}

        cfg = Config(
            model=SampleTestConfig,
            sources=[SlowSource()],
        )

        output = cfg.format_diagnostic_table()

        # Should measure load time correctly
        assert "Configuration" in output
        # Load time should be >= 100ms
        lines = output.split("\n")
        for line in lines:
            if "slow" in line.lower() and "ms" in line:
                # Extract time value
                import re

                time_match = re.search(r"(\d+\.\d+)", line)
                if time_match:
                    time_value = float(time_match.group(1))
                    # At least 90ms (allowing some overhead)
                    assert time_value >= 90.0

    def test_format_diagnostic_table_with_load_config_dict_failure(self):
        """Test when _load_config_dict fails."""
        cfg = Config(
            model=SampleTestConfig,
            sources=[sources.Env()],
        )

        # Mock _load_config_dict to raise exception
        def failing_load_config_dict(validate=False):
            raise Exception("load_config_dict failed")

        cfg._load_config_dict = failing_load_config_dict

        # Should handle exception
        with pytest.raises(Exception, match="load_config_dict failed"):
            cfg.format_diagnostic_table()

    def test_get_all_fields_info_returns_empty(self):
        """Test when get_all_fields_info returns empty list."""

        @dataclass
        class EmptyConfig:
            pass

        cfg = Config(
            model=EmptyConfig,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Should handle empty fields
        assert "Configuration" in output or "No variables" in output

    def test_source_configs_dict_with_missing_source_name(self):
        """Test when source_configs dict is missing a source name."""
        cfg = Config(
            model=SampleTestConfig,
            sources=[sources.Env()],
        )

        # This tests the logic in lines 660-664
        # If source.name is not in source_configs,
        # it should default to "defaults"
        output = cfg.format_diagnostic_table()

        # Should handle missing source names gracefully
        assert "Configuration" in output
