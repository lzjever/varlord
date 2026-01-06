"""
Tests for Config CLI flags handling (--help, --check-variables).
"""

import sys
from dataclasses import dataclass, field

from varlord import Config, sources


def test_handle_cli_flags_help():
    """Test handling --help flag."""

    @dataclass
    class AppConfig:
        host: str = field(metadata={"description": "Server host"})
        port: int = field(
            default=8000,
        )

    cfg = Config(
        model=AppConfig,
        sources=[sources.Env(), sources.CLI()],
    )

    # Test --help
    original_argv = sys.argv.copy()
    sys.argv = ["test.py", "--help"]
    try:
        help_shown, cv_shown = cfg.handle_cli_flags(exit_on_help=False)
        assert help_shown is True
        assert cv_shown is False
    finally:
        sys.argv = original_argv


def test_handle_cli_flags_check_variables():
    """Test handling --check-variables flag."""

    @dataclass
    class AppConfig:
        host: str = field()
        port: int = field(
            default=8000,
        )

    cfg = Config(
        model=AppConfig,
        sources=[sources.Env(), sources.CLI()],
    )

    # Test --check-variables
    original_argv = sys.argv.copy()
    sys.argv = ["test.py", "--check-variables"]
    try:
        help_shown, cv_shown = cfg.handle_cli_flags(
            exit_on_help=False, exit_on_check_variables=False
        )
        assert help_shown is False
        assert cv_shown is True
    finally:
        sys.argv = original_argv


def test_handle_cli_flags_short_flags():
    """Test handling -h and -cv short flags."""

    @dataclass
    class AppConfig:
        host: str = field()

    cfg = Config(
        model=AppConfig,
        sources=[sources.CLI()],
    )

    # Test -h
    original_argv = sys.argv.copy()
    sys.argv = ["test.py", "-h"]
    try:
        help_shown, cv_shown = cfg.handle_cli_flags(exit_on_help=False)
        assert help_shown is True
    finally:
        sys.argv = original_argv

    # Test -cv
    sys.argv = ["test.py", "-cv"]
    try:
        help_shown, cv_shown = cfg.handle_cli_flags(
            exit_on_help=False, exit_on_check_variables=False
        )
        assert cv_shown is True
    finally:
        sys.argv = original_argv


def test_format_diagnostic_table():
    """Test diagnostic table formatting."""

    @dataclass
    class AppConfig:
        host: str = field()
        port: int = field(
            default=8000,
        )
        debug: bool = field(
            default=False,
        )

    cfg = Config(
        model=AppConfig,
        sources=[sources.Env(), sources.CLI()],
    )

    table = cfg.format_diagnostic_table()
    assert "Variable" in table
    assert "Required" in table
    assert "Status" in table
    assert "Source" in table
    assert "Value" in table
    assert "host" in table
    assert "port" in table
    assert "debug" in table


def test_format_diagnostic_table_with_env():
    """Test diagnostic table with environment variables."""
    import os

    @dataclass
    class AppConfig:
        host: str = field()
        port: int = field(
            default=8000,
        )

    cfg = Config(
        model=AppConfig,
        sources=[sources.Env(), sources.CLI()],
    )

    # Set environment variable
    os.environ["HOST"] = "localhost"
    try:
        table = cfg.format_diagnostic_table()
        assert "host" in table
        assert "localhost" in table or "env" in table
    finally:
        os.environ.pop("HOST", None)


def test_handle_cli_commands():
    """Test handle_cli_commands() method."""
    import os

    @dataclass
    class AppConfig:
        host: str = field()
        port: int = field(
            default=8000,
        )

    cfg = Config(
        model=AppConfig,
        sources=[sources.Env(), sources.CLI()],
    )

    # Set environment variable to provide required field
    os.environ["HOST"] = "localhost"
    try:
        # Test that startup() doesn't exit when no flags are present
        original_argv = sys.argv.copy()
        sys.argv = ["test.py"]
        try:
            # Should not raise SystemExit
            cfg.handle_cli_commands()
            # After handle_cli_commands(), can safely call load()
            result = cfg.load(validate=False)
            assert result is not None
            assert result.host == "localhost"
        finally:
            sys.argv = original_argv
    finally:
        os.environ.pop("HOST", None)
