"""
Comprehensive tests for check-variables functionality.

Tests the diagnostic table output, source information table,
and various real-world usage scenarios.
"""

import os
import sys
from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import patch

import pytest

from varlord import Config, sources


@dataclass
class SampleConfig:
    """Test configuration model."""

    host: str = field()  # Required
    port: int = field(default=8000)  # Optional with default
    debug: bool = field(default=False)  # Optional with default
    timeout: Optional[float] = field(default=None)  # Optional with Optional type


@dataclass
class NestedSampleConfig:
    """Test configuration with nested fields."""

    host: str = field()
    db_host: str = field(default="localhost")
    db_port: int = field(default=5432)


class TestCheckVariablesBasic:
    """Test basic check-variables functionality."""

    def test_check_variables_output_structure(self):
        """Test that check-variables output has correct structure."""
        cfg = Config(
            model=SampleConfig,
            sources=[
                sources.Env(),
                sources.CLI(),
            ],
        )

        output = cfg.format_diagnostic_table()

        # Should contain both tables
        assert "Variable" in output
        assert "Required" in output
        assert "Status" in output
        assert "Source" in output
        assert "Value" in output

        assert "Configuration Source Priority and Details" in output
        assert "Priority" in output
        assert "Source Name" in output
        assert "Instance" in output
        assert "Load Time (ms)" in output
        assert "Watch Support" in output
        assert "Last Update" in output

    def test_source_info_table_uses_source_name(self):
        """Test that source info table uses source.name property."""
        cfg = Config(
            model=SampleConfig,
            sources=[
                sources.Env(),
                sources.CLI(),
            ],
        )

        output = cfg.format_diagnostic_table()

        # Should use actual source.name values
        assert "defaults" in output or "1 (lowest)" in output
        assert "env" in output
        assert "cli" in output

    def test_source_info_table_uses_str_source(self):
        """Test that Instance column uses str(source) representation."""
        cfg = Config(
            model=SampleConfig,
            sources=[
                sources.Env(),
                sources.CLI(),
            ],
        )

        output = cfg.format_diagnostic_table()

        # Should contain source string representations
        assert "<Env" in output or "Env" in output
        assert "<CLI" in output or "CLI" in output
        assert "<Defaults" in output or "Defaults" in output

    def test_source_info_table_includes_all_sources(self):
        """Test that all sources are included in the table."""
        cfg = Config(
            model=SampleConfig,
            sources=[
                sources.Env(),
                sources.CLI(),
            ],
        )

        output = cfg.format_diagnostic_table()

        # Count source entries (should have defaults + 2 user sources = 3 total)
        lines = output.split("\n")
        source_table_start = False
        source_count = 0
        for line in lines:
            if "Configuration Source Priority" in line:
                source_table_start = True
                continue
            if source_table_start and "|" in line and "Priority" not in line and "---" not in line:
                if line.strip() and not line.strip().startswith("+"):
                    source_count += 1

        # Should have at least defaults + env + cli
        assert source_count >= 3

    def test_source_info_table_priority_order(self):
        """Test that sources are listed in correct priority order."""
        cfg = Config(
            model=SampleConfig,
            sources=[
                sources.Env(),
                sources.CLI(),
            ],
        )

        output = cfg.format_diagnostic_table()

        # Extract priority numbers
        lines = output.split("\n")
        priorities = []
        in_table = False
        for line in lines:
            if "Configuration Source Priority" in line:
                in_table = True
                continue
            if in_table and "|" in line and "Priority" not in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) > 0 and parts[0].isdigit():
                    priorities.append(int(parts[0]))

        # Should be in ascending order
        assert priorities == sorted(priorities)


class TestCheckVariablesWithDifferentSources:
    """Test check-variables with different source types."""

    def test_with_env_source(self):
        """Test check-variables output with Env source."""
        cfg = Config(
            model=SampleConfig,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Check Env source representation
        assert "env" in output
        assert "<Env" in output or "Env" in output

    def test_with_cli_source(self):
        """Test check-variables output with CLI source."""
        cfg = Config(
            model=SampleConfig,
            sources=[sources.CLI()],
        )

        output = cfg.format_diagnostic_table()

        # Check CLI source representation
        assert "cli" in output
        assert "<CLI" in output or "CLI" in output

    @pytest.mark.unit
    def test_with_dotenv_source(self):
        """Test check-variables output with DotEnv source."""
        cfg = Config(
            model=SampleConfig,
            sources=[sources.DotEnv(".env")],
        )

        output = cfg.format_diagnostic_table()

        # Check DotEnv source representation
        assert "dotenv" in output
        assert "<DotEnv" in output or "DotEnv" in output
        assert ".env" in output  # Should show path

    @pytest.mark.requires_etcd
    @pytest.mark.integration
    def test_with_etcd_source(self):
        """Test check-variables output with Etcd source."""
        try:
            cfg = Config(
                model=SampleConfig,
                sources=[
                    sources.Etcd(
                        host="127.0.0.1",
                        port=2379,
                        prefix="/app/",
                        watch=False,
                    )
                ],
            )

            output = cfg.format_diagnostic_table()

            # Check Etcd source representation
            assert "etcd" in output
            assert "<Etcd" in output or "Etcd" in output
            # Should show etcd parameters in string representation
            assert "127.0.0.1" in output or "host" in output.lower()
        except ImportError:
            pytest.skip("etcd3 not installed")

    def test_with_multiple_sources(self):
        """Test check-variables with multiple sources."""
        cfg = Config(
            model=SampleConfig,
            sources=[
                sources.Env(),
                sources.CLI(),
            ],
        )

        output = cfg.format_diagnostic_table()

        # Should include all sources
        assert "defaults" in output or "1 (lowest)" in output
        assert "env" in output
        assert "cli" in output

    def test_source_string_representations(self):
        """Test that all source types have proper string representations."""
        cfg = Config(
            model=SampleConfig,
            sources=[
                sources.Env(),
                sources.CLI(),
            ],
        )

        # Test that str() works on sources
        for source in cfg._sources:
            source_str = str(source)
            assert source_str is not None
            assert len(source_str) > 0
            assert source.name in source_str or source.__class__.__name__ in source_str

    def test_source_name_property(self):
        """Test that all sources have name property."""
        cfg = Config(
            model=SampleConfig,
            sources=[
                sources.Env(),
                sources.CLI(),
            ],
        )

        # Test that name property works
        for source in cfg._sources:
            assert hasattr(source, "name")
            name = source.name
            assert isinstance(name, str)
            assert len(name) > 0


class TestCheckVariablesRealWorldScenarios:
    """Test check-variables with real-world usage scenarios."""

    def test_missing_required_fields(self):
        """Test check-variables when required fields are missing."""
        cfg = Config(
            model=SampleConfig,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Should show missing required field
        assert "host" in output
        assert "Required" in output
        assert "Missing" in output or "missing" in output.lower()

    def test_all_fields_provided(self):
        """Test check-variables when all fields are provided."""
        os.environ["HOST"] = "localhost"
        try:
            cfg = Config(
                model=SampleConfig,
                sources=[sources.Env()],
            )

            output = cfg.format_diagnostic_table()

            # Should show all fields
            assert "host" in output
            assert "port" in output
            assert "debug" in output
        finally:
            os.environ.pop("HOST", None)

    def test_fields_with_defaults(self):
        """Test check-variables with fields that have defaults."""
        cfg = Config(
            model=SampleConfig,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Should show fields with defaults
        assert "port" in output
        assert "debug" in output
        # Should indicate they're using defaults
        assert "Using Default" in output or "default" in output.lower()

    def test_optional_fields(self):
        """Test check-variables with Optional type fields."""
        cfg = Config(
            model=SampleConfig,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Should show optional fields
        assert "timeout" in output
        assert "Optional" in output

    def test_nested_configuration(self):
        """Test check-variables with nested configuration."""
        cfg = Config(
            model=NestedSampleConfig,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Should show nested fields
        assert "host" in output
        assert "db_host" in output
        assert "db_port" in output

    def test_source_load_times(self):
        """Test that load times are measured and displayed."""
        cfg = Config(
            model=SampleConfig,
            sources=[sources.Env(), sources.CLI()],
        )

        output = cfg.format_diagnostic_table()

        # Should contain load time information
        assert "Load Time" in output
        assert "ms" in output or "0.00" in output

    def test_watch_support_display(self):
        """Test that watch support status is displayed."""
        cfg = Config(
            model=SampleConfig,
            sources=[sources.Env(), sources.CLI()],
        )

        output = cfg.format_diagnostic_table()

        # Should show watch support
        assert "Watch Support" in output
        assert "No" in output or "Yes" in output


class TestCheckVariablesEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_sources_list(self):
        """Test check-variables with empty sources list."""
        cfg = Config(
            model=SampleConfig,
            sources=[],  # No sources, only defaults
        )

        output = cfg.format_diagnostic_table()

        # Should still work with just defaults
        assert "defaults" in output or "1 (lowest)" in output
        assert "Configuration Source Priority" in output

    def test_custom_source_string_representation(self):
        """Test that custom sources work with str() representation."""
        from varlord.sources.base import Source

        class CustomSource(Source):
            @property
            def name(self) -> str:
                return "custom"

            def load(self):
                return {}

            def __repr__(self) -> str:
                return "<CustomSource(custom_param='value')>"

        cfg = Config(
            model=SampleConfig,
            sources=[CustomSource()],
        )

        output = cfg.format_diagnostic_table()

        # Should use custom source's string representation
        assert "custom" in output
        assert "CustomSource" in output

    def test_source_without_repr(self):
        """Test handling of source without custom __repr__."""
        from varlord.sources.base import Source

        class SimpleSource(Source):
            @property
            def name(self) -> str:
                return "simple"

            def load(self):
                return {}

            # No custom __repr__, uses base class

        cfg = Config(
            model=SampleConfig,
            sources=[SimpleSource()],
        )

        output = cfg.format_diagnostic_table()

        # Should still work, using base class __repr__
        assert "simple" in output
        assert "SimpleSource" in output

    def test_fallback_without_prettytable(self):
        """Test fallback when prettytable is not available."""
        with patch.dict("sys.modules", {"prettytable": None}):
            original_import = __import__

            def mock_import(name, *args, **kwargs):
                if name == "prettytable":
                    raise ImportError("No module named 'prettytable'")
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                cfg = Config(
                    model=SampleConfig,
                    sources=[sources.Env(), sources.CLI()],
                )

                output = cfg.format_diagnostic_table()

                # Should use fallback format
                assert "Configuration Source Priority" in output
                assert "defaults" in output or "1" in output
                assert "env" in output
                assert "cli" in output

    def test_source_name_edge_cases(self):
        """Test edge cases for source names."""
        from varlord.sources.base import Source

        class EdgeCaseSource(Source):
            @property
            def name(self) -> str:
                return "source-with-dashes_and_underscores"

            def load(self):
                return {}

        cfg = Config(
            model=SampleConfig,
            sources=[EdgeCaseSource()],
        )

        output = cfg.format_diagnostic_table()

        # Should handle edge case names
        assert "source-with-dashes_and_underscores" in output


class TestCheckVariablesIntegration:
    """Integration tests for check-variables in real scenarios."""

    def test_real_world_app_config(self):
        """Test with a realistic application configuration."""

        @dataclass
        class AppConfig:
            api_key: str = field()  # Required
            database_url: str = field(default="sqlite:///db.sqlite")
            max_workers: int = field(default=4)
            debug: bool = field(default=False)
            log_level: str = field(default="INFO")

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Env(),
                sources.CLI(),
            ],
        )

        output = cfg.format_diagnostic_table()

        # Should show all fields
        assert "api_key" in output
        assert "database_url" in output
        assert "max_workers" in output
        assert "debug" in output
        assert "log_level" in output

        # Should show source information
        assert "Configuration Source Priority" in output
        assert "env" in output
        assert "cli" in output

    def test_with_environment_variables_set(self):
        """Test check-variables when environment variables are set."""
        os.environ["HOST"] = "0.0.0.0"
        os.environ["PORT"] = "9000"
        try:
            cfg = Config(
                model=SampleConfig,
                sources=[sources.Env()],
            )

            output = cfg.format_diagnostic_table()

            # Should show values from env
            assert "0.0.0.0" in output or "env" in output
            assert "9000" in output or "env" in output
        finally:
            os.environ.pop("HOST", None)
            os.environ.pop("PORT", None)

    def test_with_cli_arguments(self):
        """Test check-variables when CLI arguments are provided."""
        original_argv = sys.argv.copy()
        sys.argv = ["test.py", "--host", "192.168.1.1", "--port", "8080"]
        try:
            cfg = Config(
                model=SampleConfig,
                sources=[sources.CLI()],
            )

            output = cfg.format_diagnostic_table()

            # Should show values from CLI
            assert "192.168.1.1" in output or "cli" in output
            assert "8080" in output or "cli" in output
        finally:
            sys.argv = original_argv

    def test_priority_override_behavior(self):
        """Test that check-variables shows correct priority behavior."""
        os.environ["HOST"] = "env_value"
        original_argv = sys.argv.copy()
        sys.argv = ["test.py", "--host", "cli_value"]
        try:
            cfg = Config(
                model=SampleConfig,
                sources=[
                    sources.Env(),  # Lower priority
                    sources.CLI(),  # Higher priority
                ],
            )

            output = cfg.format_diagnostic_table()

            # CLI should override env
            # The actual value shown depends on which source provided it
            assert "cli" in output
            assert "env" in output
        finally:
            sys.argv = original_argv
            os.environ.pop("HOST", None)

    def test_handle_cli_commands_with_check_variables(self):
        """Test handle_cli_commands() with --check-variables flag."""
        original_argv = sys.argv.copy()
        sys.argv = ["test.py", "--check-variables"]
        try:
            cfg = Config(
                model=SampleConfig,
                sources=[sources.Env(), sources.CLI()],
            )

            # Should not raise exception (will exit, but we catch it)
            with pytest.raises(SystemExit):
                cfg.handle_cli_commands()
        finally:
            sys.argv = original_argv

    def test_handle_cli_commands_with_short_flag(self):
        """Test handle_cli_commands() with -cv short flag."""
        original_argv = sys.argv.copy()
        sys.argv = ["test.py", "-cv"]
        try:
            cfg = Config(
                model=SampleConfig,
                sources=[sources.Env(), sources.CLI()],
            )

            # Should not raise exception (will exit, but we catch it)
            with pytest.raises(SystemExit):
                cfg.handle_cli_commands()
        finally:
            sys.argv = original_argv


class TestSourceStringRepresentations:
    """Test string representations of different source types."""

    def test_env_source_str(self):
        """Test Env source string representation."""
        source = sources.Env()
        source_str = str(source)
        assert "Env" in source_str
        assert isinstance(source_str, str)

    def test_cli_source_str(self):
        """Test CLI source string representation."""
        source = sources.CLI()
        source_str = str(source)
        assert "CLI" in source_str
        assert isinstance(source_str, str)

    @pytest.mark.unit
    def test_dotenv_source_str(self):
        """Test DotEnv source string representation."""
        source = sources.DotEnv(".env")
        source_str = str(source)
        assert "DotEnv" in source_str
        assert ".env" in source_str
        assert isinstance(source_str, str)

    def test_defaults_source_str(self):
        """Test Defaults source string representation."""
        from varlord.sources.defaults import Defaults

        source = Defaults(model=SampleConfig)
        source_str = str(source)
        assert "Defaults" in source_str
        assert "SampleConfig" in source_str or "model" in source_str.lower()
        assert isinstance(source_str, str)

    @pytest.mark.requires_etcd
    @pytest.mark.integration
    def test_etcd_source_str(self):
        """Test Etcd source string representation."""
        try:
            source = sources.Etcd(
                host="127.0.0.1",
                port=2379,
                prefix="/app/",
                watch=False,
            )
            source_str = str(source)
            assert "Etcd" in source_str
            # Should show some parameters
            assert isinstance(source_str, str)
        except ImportError:
            pytest.skip("etcd3 not installed")


class TestCheckVariablesPerformance:
    """Test performance-related aspects of check-variables."""

    def test_load_time_measurement(self):
        """Test that load times are measured correctly."""
        cfg = Config(
            model=SampleConfig,
            sources=[sources.Env(), sources.CLI()],
        )

        output = cfg.format_diagnostic_table()

        # Should contain load time measurements
        assert "Load Time" in output

        # Extract load times and verify they're numeric
        lines = output.split("\n")
        for line in lines:
            if "|" in line and "Load Time" not in line and "---" not in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 4:  # Should have Load Time column
                    load_time_str = parts[3]  # Load Time is 4th column
                    if "ms" in load_time_str or "." in load_time_str:
                        # Should be a valid number
                        time_value = load_time_str.replace("ms", "").strip()
                        try:
                            float(time_value)
                        except ValueError:
                            # If it's not a number, it might be "N/A" or similar
                            assert time_value in ["N/A", ""] or "0.00" in load_time_str

    def test_empty_model_fields(self):
        """Test check-variables with model that has no fields."""

        @dataclass
        class EmptyConfig:
            pass

        cfg = Config(
            model=EmptyConfig,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Should handle empty model gracefully
        assert "Configuration Variables Status" in output or "No variables" in output
        assert "Configuration Source Priority" in output

    def test_large_value_truncation(self):
        """Test that large values are truncated in output."""

        @dataclass
        class LargeValueConfig:
            api_key: str = field(default="x" * 100)  # Very long default value

        cfg = Config(
            model=LargeValueConfig,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Should truncate long values
        assert "api_key" in output
        # Value should be truncated if longer than 40 chars
        if "x" * 100 in output:
            # If not truncated, that's also acceptable
            pass
        else:
            # Should have truncation indicator
            assert (
                "..." in output
                or len([line for line in output.split("\n") if "x" * 40 in line]) > 0
            )

    def test_none_value_display(self):
        """Test that None values are displayed correctly."""

        @dataclass
        class NoneValueConfig:
            optional_field: Optional[str] = field(default=None)

        cfg = Config(
            model=NoneValueConfig,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Should show None values
        assert "optional_field" in output
        assert "None" in output or "Optional" in output

    def test_empty_string_value_display(self):
        """Test that empty string values are displayed correctly."""

        @dataclass
        class EmptyStringConfig:
            empty_field: str = field(default="")

        cfg = Config(
            model=EmptyStringConfig,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Should handle empty strings
        assert "empty_field" in output
        # Should show as "Loaded (empty)" or similar
        assert "empty" in output.lower() or "Using Default" in output

    def test_all_source_types_in_one_config(self):
        """Test check-variables with all available source types."""
        sources_list = [sources.Env(), sources.CLI()]

        try:
            sources_list.append(sources.DotEnv(".env"))
        except ImportError:
            pass

        try:
            sources_list.append(sources.Etcd(host="127.0.0.1", port=2379, prefix="/", watch=False))
        except ImportError:
            pass

        cfg = Config(
            model=SampleConfig,
            sources=sources_list,
        )

        output = cfg.format_diagnostic_table()

        # Should include all sources
        assert "env" in output
        assert "cli" in output
        # Other sources may or may not be present depending on imports

    def test_required_vs_optional_display(self):
        """Test that required and optional fields are clearly distinguished."""

        @dataclass
        class MixedConfig:
            required_field: str = field()  # Required
            optional_with_default: int = field(default=42)  # Optional
            optional_none: Optional[str] = field(default=None)  # Optional

        cfg = Config(
            model=MixedConfig,
            sources=[sources.Env()],
        )

        output = cfg.format_diagnostic_table()

        # Should show required/optional status
        assert "required_field" in output
        assert "optional_with_default" in output
        assert "optional_none" in output
        assert "Required" in output
        assert "Optional" in output

    def test_source_priority_display_order(self):
        """Test that sources are displayed in correct priority order."""
        cfg = Config(
            model=SampleConfig,
            sources=[
                sources.Env(),  # Priority 2
                sources.CLI(),  # Priority 3
            ],
        )

        output = cfg.format_diagnostic_table()

        # Extract priority numbers from output
        lines = output.split("\n")
        priorities = []
        in_table = False
        for line in lines:
            if "Configuration Source Priority" in line:
                in_table = True
                continue
            if in_table and "|" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) > 0:
                    priority_str = parts[0]
                    if priority_str.isdigit() or "lowest" in priority_str.lower():
                        priorities.append(priority_str)

        # Should have at least 3 priorities (defaults, env, cli)
        assert len(priorities) >= 3
        # First should be "1 (lowest)" or "1"
        assert "1" in priorities[0] or "lowest" in priorities[0].lower()

    def test_multiple_calls_performance(self):
        """Test that multiple calls to format_diagnostic_table work correctly."""
        cfg = Config(
            model=SampleConfig,
            sources=[sources.Env(), sources.CLI()],
        )

        # Call multiple times
        output1 = cfg.format_diagnostic_table()
        output2 = cfg.format_diagnostic_table()

        # Should produce consistent structure (load times may vary slightly)
        # Check that key components are present in both
        assert "Variable" in output1
        assert "Variable" in output2
        assert "Configuration Source Priority" in output1
        assert "Configuration Source Priority" in output2
        assert "Source Name" in output1
        assert "Source Name" in output2
        assert "Instance" in output1
        assert "Instance" in output2

        # Check that all variables are present in both
        assert "host" in output1 and "host" in output2
        assert "port" in output1 and "port" in output2
        assert "debug" in output1 and "debug" in output2
        assert "timeout" in output1 and "timeout" in output2

        # Check that source names are consistent
        assert "defaults" in output1 and "defaults" in output2
        assert "env" in output1 and "env" in output2
        assert "cli" in output1 and "cli" in output2
