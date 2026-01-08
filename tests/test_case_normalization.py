"""Tests for case normalization across sources."""

import os
import sys
from dataclasses import dataclass, field

import pytest

from varlord import Config, sources


@dataclass
class AppConfig:
    host: str = field(
        default="default",
    )
    port: int = field(
        default=8000,
    )


def test_env_case_normalization():
    """Test that Env source normalizes keys to lowercase."""
    try:
        os.environ["HOST"] = "env-host"
        os.environ["PORT"] = "9000"

        source = sources.Env(model=AppConfig)
        result = source.load()

        # Should be lowercase
        assert "host" in result
        assert "port" in result
        assert result["host"] == "env-host"
        assert result["port"] == "9000"

        # Should not have uppercase keys
        assert "HOST" not in result
        assert "PORT" not in result
    finally:
        os.environ.pop("HOST", None)
        os.environ.pop("PORT", None)


def test_cli_case_normalization():
    """Test that CLI source normalizes output keys to lowercase."""
    original_argv = sys.argv[:]

    try:
        # CLI uses model field names for arguments, so --host (lowercase) is correct
        # The key point is that output keys are normalized to lowercase
        sys.argv = ["test", "--host", "cli-host", "--port", "9999"]

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.CLI(model=AppConfig),
            ],
        )

        app = cfg.load()
        # CLI should work correctly
        assert app.host == "cli-host"
        assert app.port == 9999

        # Verify that output keys are lowercase (this is the key normalization)
        cli_source = sources.CLI(model=AppConfig)
        result = cli_source.load()
        # Output keys should always be lowercase for consistency
        assert all(k == k.lower() for k in result.keys())
    finally:
        sys.argv = original_argv


@pytest.mark.unit
def test_dotenv_case_normalization():
    """Test that DotEnv source normalizes keys to lowercase."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("HOST=dotenv-host\n")
        f.write("PORT=7777\n")
        f.write("UNRELATED_VAR=ignored\n")  # This will be filtered out by model
        temp_path = f.name

    try:
        source = sources.DotEnv(temp_path, model=AppConfig)
        result = source.load()

        # Should be lowercase and filtered by model
        assert "host" in result
        assert "port" in result
        assert "unrelated_var" not in result  # Filtered out by model
        assert result["host"] == "dotenv-host"
        assert result["port"] == "7777"

        # Should not have uppercase keys
        assert "HOST" not in result
        assert "PORT" not in result
    finally:
        os.unlink(temp_path)


@pytest.mark.unit
def test_unified_case_across_sources():
    """Test that all sources use lowercase keys for consistency."""
    import tempfile

    original_argv = sys.argv[:]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("HOST=dotenv-host\n")  # DotEnv will convert to lowercase
        temp_path = f.name

    try:
        os.environ["HOST"] = "env-host"
        sys.argv = ["test", "--host", "cli-host"]

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.DotEnv(temp_path, model=AppConfig),  # Returns {"host": "dotenv-host"}
                sources.Env(model=AppConfig),  # Returns {"host": "env-host"}
                sources.CLI(model=AppConfig),  # Returns {"host": "cli-host"}
            ],
        )

        # All sources should use lowercase "host" key
        # CLI should override (last in list)
        app = cfg.load()
        assert app.host == "cli-host"
    finally:
        sys.argv = original_argv
        os.environ.pop("HOST", None)
        os.unlink(temp_path)
