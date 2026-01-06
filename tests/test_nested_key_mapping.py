"""Tests for nested key mapping functionality."""

from dataclasses import dataclass, field

from varlord import Config, sources


@dataclass
class DBConfig:
    host: str = field(
        default="localhost",
    )
    port: int = field(
        default=5432,
    )


@dataclass
class AppConfig:
    host: str = field(
        default="0.0.0.0",
    )
    port: int = field(
        default=8000,
    )
    db: DBConfig = field(
        default_factory=DBConfig,
    )


def test_cli_nested_key_mapping():
    """Test that CLI source maps nested keys correctly."""
    import sys

    original_argv = sys.argv[:]

    try:
        sys.argv = ["test", "--db-host", "cli-host", "--db-port", "9999"]

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.CLI(model=AppConfig),
            ],
        )

        app = cfg.load()
        assert app.db.host == "cli-host"
        assert app.db.port == 9999
    finally:
        sys.argv = original_argv


def test_env_cli_override_nested():
    """Test that CLI can override Env for nested keys."""
    import os
    import sys

    original_argv = sys.argv[:]

    try:
        # Set environment variable
        os.environ["DB__HOST"] = "env-host"
        os.environ["DB__PORT"] = "8888"

        # Set CLI argument (should override env)
        sys.argv = ["test", "--db-host", "cli-host"]

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Env(model=AppConfig),
                sources.CLI(model=AppConfig),
            ],
        )

        app = cfg.load()
        # CLI should override Env
        assert app.db.host == "cli-host"
        # Env value should be used for port (no CLI override)
        assert app.db.port == 8888
    finally:
        sys.argv = original_argv
        os.environ.pop("DB__HOST", None)
        os.environ.pop("DB__PORT", None)


def test_unified_key_format():
    """Test that all sources use unified dot notation."""
    import os
    import sys

    original_argv = sys.argv[:]

    try:
        # Env: db.host
        os.environ["DB__HOST"] = "env-host"

        # CLI: db.host (should override)
        sys.argv = ["test", "--db-host", "cli-host"]

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Env(model=AppConfig),
                sources.CLI(model=AppConfig),
            ],
        )

        # Both sources should use db.host, allowing proper override
        app = cfg.load()
        assert app.db.host == "cli-host"  # CLI overrides Env
    finally:
        sys.argv = original_argv
        os.environ.pop("DB__HOST", None)


def test_flat_key_still_works():
    """Test that flat keys (without dots) still work correctly."""
    import sys

    original_argv = sys.argv[:]

    try:
        sys.argv = ["test", "--host", "cli-host", "--port", "9999"]

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.CLI(model=AppConfig),
            ],
        )

        app = cfg.load()
        assert app.host == "cli-host"
        assert app.port == 9999
    finally:
        sys.argv = original_argv
