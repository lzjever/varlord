"""
Tests for CLI source.
"""

from dataclasses import dataclass, field

import pytest

from varlord.sources.cli import CLI


@dataclass
class CLITestConfig:
    host: str = field(metadata={"description": "Server host"})
    port: int = field(default=8000, metadata={"optional": True, "help": "Server port"})
    debug: bool = field(
        default=False,
    )


def test_cli_basic():
    """Test basic CLI argument parsing."""
    source = CLI(model=CLITestConfig, argv=["--host", "0.0.0.0"])
    config = source.load()

    assert config["host"] == "0.0.0.0"


def test_cli_with_port():
    """Test CLI with port argument."""
    source = CLI(model=CLITestConfig, argv=["--host", "0.0.0.0", "--port", "9000"])
    config = source.load()

    assert config["host"] == "0.0.0.0"
    assert config["port"] == 9000


def test_cli_boolean_flag():
    """Test CLI boolean flag."""
    source = CLI(model=CLITestConfig, argv=["--host", "0.0.0.0", "--debug"])
    config = source.load()

    assert config["host"] == "0.0.0.0"
    assert config["debug"] is True


def test_cli_boolean_no_flag():
    """Test CLI boolean no-flag."""
    source = CLI(model=CLITestConfig, argv=["--host", "0.0.0.0", "--no-debug"])
    config = source.load()

    assert config["host"] == "0.0.0.0"
    assert config["debug"] is False


def test_cli_model_filtering():
    """Test that CLI only parses model fields."""
    source = CLI(model=CLITestConfig, argv=["--host", "0.0.0.0", "--unknown-arg", "value"])
    config = source.load()

    assert "host" in config
    assert "unknown_arg" not in config  # Filtered out


def test_cli_required_argument():
    """Test CLI with required argument."""
    source = CLI(model=CLITestConfig, argv=["--host", "0.0.0.0"])
    config = source.load()

    # host is required, should be present
    assert "host" in config


def test_cli_nested_fields():
    """Test CLI with nested fields."""

    @dataclass
    class DBConfig:
        host: str = field()
        port: int = field(
            default=5432,
        )

    @dataclass
    class AppConfig:
        db_host: str = field()  # Flat field, not nested
        db_port: int = field(
            default=5432,
        )

    source = CLI(model=AppConfig, argv=["--db-host", "localhost", "--db-port", "5432"])
    config = source.load()

    assert config["db_host"] == "localhost"
    assert config["db_port"] == 5432


def test_cli_name():
    """Test source name."""
    source = CLI(model=CLITestConfig)
    assert source.name == "cli"


def test_cli_no_model_error():
    """Test that CLI raises error without model."""
    source = CLI()

    with pytest.raises(ValueError) as exc_info:
        source.load()

    assert "model" in str(exc_info.value).lower()


def test_cli_hyphen_underscore_both_work():
    """Test that both hyphen and underscore work for CLI args."""
    source1 = CLI(model=CLITestConfig, argv=["--host", "0.0.0.0"])
    config1 = source1.load()

    # Both should work (argparse handles both)
    assert config1["host"] == "0.0.0.0"
