"""
Tests for source help formatting.
"""

from dataclasses import dataclass, field

import pytest

from varlord import sources
from varlord.source_help import (
    format_source_help,
    generate_cli_example,
    generate_dotenv_example,
    generate_env_example,
)


def test_generate_env_example():
    """Test environment variable example generation."""
    example = generate_env_example("api_key", str)
    assert "API_KEY" in example
    assert "api_key" in example.lower()

    # Test nested
    example = generate_env_example("db.host", str)
    assert "DB__HOST" in example or "DB_HOST" in example


def test_generate_cli_example():
    """Test CLI argument example generation."""
    example = generate_cli_example("api_key", str)
    assert "--api-key" in example or "--api_key" in example

    # Test boolean
    example = generate_cli_example("debug", bool)
    assert "--debug" in example


def test_generate_dotenv_example():
    """Test DotEnv example generation."""
    example = generate_dotenv_example("api_key", str)
    assert "API_KEY" in example
    assert "=" in example

    # Test nested
    example = generate_dotenv_example("db.host", str)
    assert "DB__HOST" in example or "DB_HOST" in example


def test_format_source_help_with_env():
    """Test source help formatting with Env source."""

    @dataclass
    class Config:
        api_key: str = field()
        host: str = field()

    source_list = [sources.Env(model=Config)]
    missing_fields = ["api_key", "host"]

    help_text = format_source_help(source_list, missing_fields)

    assert "Environment Variables" in help_text
    assert "api_key" in help_text.lower()
    assert "host" in help_text.lower()


def test_format_source_help_with_cli():
    """Test source help formatting with CLI source."""

    @dataclass
    class Config:
        api_key: str = field()

    source_list = [sources.CLI(model=Config)]
    missing_fields = ["api_key"]

    help_text = format_source_help(source_list, missing_fields)

    assert "Command Line Arguments" in help_text
    assert "api-key" in help_text.lower() or "api_key" in help_text.lower()


@pytest.mark.unit
def test_format_source_help_with_dotenv():
    """Test source help formatting with DotEnv source."""

    @dataclass
    class Config:
        api_key: str = field()

    source_list = [sources.DotEnv(".env", model=Config)]
    missing_fields = ["api_key"]

    help_text = format_source_help(source_list, missing_fields)

    assert ".env" in help_text or "DotEnv" in help_text or "File" in help_text
    assert "api_key" in help_text.lower()


def test_format_source_help_multiple_sources():
    """Test source help formatting with multiple sources."""

    @dataclass
    class Config:
        api_key: str = field()

    source_list = [
        sources.Env(model=Config),
        sources.CLI(model=Config),
    ]
    missing_fields = ["api_key"]

    help_text = format_source_help(source_list, missing_fields)

    # Should contain help for both sources
    assert "Environment Variables" in help_text or "Command Line Arguments" in help_text


def test_format_source_help_empty():
    """Test source help formatting with empty inputs."""
    help_text = format_source_help([], [])
    assert help_text == ""

    help_text = format_source_help([sources.Env()], [])
    assert help_text == ""
