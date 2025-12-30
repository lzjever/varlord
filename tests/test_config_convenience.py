"""
Tests for Config convenience methods.
"""

import os
import pytest
from dataclasses import dataclass
from varlord import Config, sources


@dataclass(frozen=True)
class AppTestConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False


def test_auto_inject_model_to_cli():
    """Test automatic model injection to CLI source."""
    cfg = Config(
        model=AppTestConfig,
        sources=[
            sources.Defaults(model=AppTestConfig),
            sources.CLI(),  # Model should be auto-injected
        ],
    )

    # CLI source should have model
    cli_source = next(s for s in cfg._sources if isinstance(s, sources.CLI))
    assert cli_source._model == AppTestConfig


def test_from_model_convenience():
    """Test Config.from_model convenience method."""
    os.environ["TEST_HOST"] = "0.0.0.0"

    try:
        cfg = Config.from_model(
            AppTestConfig,
            env_prefix="TEST_",
            cli=True,
            dotenv=None,  # Disable dotenv
        )

        app = cfg.load()
        assert app.host == "0.0.0.0"  # From env
        assert app.port == 8000  # From defaults
    finally:
        os.environ.pop("TEST_HOST", None)


def test_from_model_without_cli():
    """Test Config.from_model without CLI."""
    cfg = Config.from_model(
        AppTestConfig,
        env_prefix="",
        cli=False,
    )

    # Should not have CLI source
    cli_sources = [s for s in cfg._sources if isinstance(s, sources.CLI)]
    assert len(cli_sources) == 0


def test_from_model_priority():
    """Test Config.from_model with sources order."""
    os.environ["TEST_HOST"] = "env_value"

    try:
        # from_model creates sources in order: Defaults < Env < CLI
        # So Env overrides Defaults
        cfg = Config.from_model(
            AppTestConfig,
            env_prefix="TEST_",
        )

        app = cfg.load()
        assert app.host == "env_value"
    finally:
        os.environ.pop("TEST_HOST", None)
