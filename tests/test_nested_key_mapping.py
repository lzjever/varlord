"""Tests for nested key mapping functionality."""

import pytest
from dataclasses import dataclass
from varlord import Config, sources


@dataclass
class DBConfig:
    host: str = "localhost"
    port: int = 5432


@dataclass
class AppConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    db: DBConfig = None  # type: ignore

    def __post_init__(self):
        if self.db is None:
            self.db = DBConfig()


def test_cli_nested_key_mapping():
    """Test that CLI source maps nested keys correctly."""
    import sys

    original_argv = sys.argv[:]

    try:
        sys.argv = ["test", "--db-host", "cli-host", "--db-port", "9999"]

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
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
        os.environ["APP_DB__HOST"] = "env-host"
        os.environ["APP_DB__PORT"] = "8888"

        # Set CLI argument (should override env)
        sys.argv = ["test", "--db-host", "cli-host"]

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.Env(prefix="APP_", separator="__"),
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
        os.environ.pop("APP_DB__HOST", None)
        os.environ.pop("APP_DB__PORT", None)


def test_unified_key_format():
    """Test that all sources use unified dot notation."""
    import os
    import sys

    original_argv = sys.argv[:]

    try:
        # Env: db.host
        os.environ["APP_DB__HOST"] = "env-host"

        # CLI: db.host (should override)
        sys.argv = ["test", "--db-host", "cli-host"]

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.Env(prefix="APP_", separator="__"),
                sources.CLI(model=AppConfig),
            ],
        )

        # Both sources should use db.host, allowing proper override
        app = cfg.load()
        assert app.db.host == "cli-host"  # CLI overrides Env
    finally:
        sys.argv = original_argv
        os.environ.pop("APP_DB__HOST", None)


def test_flat_key_still_works():
    """Test that flat keys (without dots) still work correctly."""
    import sys

    original_argv = sys.argv[:]

    try:
        sys.argv = ["test", "--host", "cli-host", "--port", "9999"]

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.CLI(model=AppConfig),
            ],
        )

        app = cfg.load()
        assert app.host == "cli-host"
        assert app.port == 9999
    finally:
        sys.argv = original_argv
