"""
Tests for CLI help generation functionality.
"""

from dataclasses import dataclass, field

from varlord import Config, sources
from varlord.sources.cli import CLI


def test_cli_format_help_basic():
    """Test basic CLI help formatting."""

    @dataclass
    class AppConfig:
        host: str = field(metadata={"description": "Server host"})
        port: int = field(default=8000, metadata={"optional": True, "description": "Server port"})

    cli = CLI(model=AppConfig)
    help_text = cli.format_help(prog="test.py")

    assert "Usage: test.py" in help_text or "usage: test.py" in help_text
    assert "--host STR" in help_text
    assert "Server host" in help_text
    assert "Required Arguments:" in help_text or "Required arguments:" in help_text
    assert "--port INT" in help_text
    assert "Server port" in help_text
    assert "Optional Arguments:" in help_text or "Optional arguments:" in help_text
    assert "(default: 8000)" in help_text


def test_cli_format_help_with_help_metadata():
    """Test CLI help with help metadata (overrides description)."""

    @dataclass
    class AppConfig:
        api_key: str = field(
            metadata={
                "required": True,
                "description": "API key for authentication",
                "help": "Required API key",
            }
        )

    cli = CLI(model=AppConfig)
    help_text = cli.format_help(prog="test.py")

    assert "Required API key" in help_text
    assert "API key for authentication" not in help_text  # help overrides description


def test_cli_format_help_boolean_flags():
    """Test CLI help for boolean flags."""

    @dataclass
    class AppConfig:
        debug: bool = field(
            default=False, metadata={"optional": True, "description": "Enable debug mode"}
        )

    cli = CLI(model=AppConfig)
    help_text = cli.format_help(prog="test.py")

    assert "Boolean Flags:" in help_text or "Boolean flags:" in help_text
    assert "--debug / --no-debug" in help_text
    assert "Enable debug mode" in help_text


def test_cli_get_field_help():
    """Test getting help for a specific field."""

    @dataclass
    class AppConfig:
        api_key: str = field(metadata={"description": "API key"})
        host: str = field(metadata={"help": "Server host"})

    cli = CLI(model=AppConfig)

    # Test with description
    help_text = cli.get_field_help("api_key")
    assert help_text == "API key"

    # Test with help (should return help, not description)
    help_text = cli.get_field_help("host")
    assert help_text == "Server host"


def test_config_format_cli_help():
    """Test Config.format_cli_help() method."""

    @dataclass
    class AppConfig:
        api_key: str = field(metadata={"description": "API key"})

    cfg = Config(
        model=AppConfig,
        sources=[sources.CLI()],
    )

    help_text = cfg.format_cli_help(prog="test.py")

    # Check standard options
    assert "Standard Options:" in help_text
    assert "--help, -h" in help_text
    assert "--check-variables, -cv" in help_text
    assert "Show this help message and exit" in help_text
    assert "Show diagnostic table" in help_text

    # Check usage and arguments
    assert "Usage: test.py" in help_text or "usage: test.py" in help_text
    assert "--api-key STR" in help_text
    assert "API key" in help_text


def test_config_format_cli_help_no_cli_source():
    """Test Config.format_cli_help() when no CLI source is present."""

    @dataclass
    class AppConfig:
        api_key: str = field()

    cfg = Config(
        model=AppConfig,
        sources=[sources.Env()],
    )

    help_text = cfg.format_cli_help()
    assert help_text == ""


def test_cli_format_help_nested_fields():
    """Test CLI help with nested fields."""

    @dataclass
    class DBConfig:
        host: str = field(metadata={"description": "Database host"})

    @dataclass
    class AppConfig:
        db: DBConfig = field()

    cli = CLI(model=AppConfig)
    help_text = cli.format_help(prog="test.py")

    assert "--db-host STR" in help_text
    assert "Database host" in help_text
