"""
Tests for Config convenience methods.
"""

import os
from dataclasses import dataclass, field

from varlord import Config, sources


@dataclass(frozen=True)
class AppTestConfig:
    host: str = field(
        default="127.0.0.1",
    )
    port: int = field(
        default=8000,
    )
    debug: bool = field(
        default=False,
    )


def test_auto_inject_model_to_sources():
    """Test automatic model injection to all sources."""
    cfg = Config(
        model=AppTestConfig,
        sources=[
            sources.Env(),  # Model should be auto-injected
            sources.CLI(),  # Model should be auto-injected
        ],
    )

    # All sources should have model
    for source in cfg._sources:
        assert source._model == AppTestConfig


def test_from_model_convenience():
    """Test Config.from_model convenience method."""
    os.environ["HOST"] = "0.0.0.0"

    try:
        cfg = Config.from_model(
            AppTestConfig,
            cli=True,
            dotenv=None,  # Disable dotenv
        )

        app = cfg.load()
        assert app.host == "0.0.0.0"  # From env
        assert app.port == 8000  # From defaults
    finally:
        os.environ.pop("HOST", None)


def test_from_model_without_cli():
    """Test Config.from_model without CLI."""
    cfg = Config.from_model(
        AppTestConfig,
        cli=False,
    )

    # Should not have CLI source
    cli_sources = [s for s in cfg._sources if isinstance(s, sources.CLI)]
    assert len(cli_sources) == 0


def test_from_model_priority():
    """Test Config.from_model with sources order."""
    os.environ["HOST"] = "env_value"

    try:
        # from_model creates sources in order: Env < CLI
        # Defaults are automatically applied first
        # So Env overrides Defaults
        cfg = Config.from_model(
            AppTestConfig,
        )

        app = cfg.load()
        assert app.host == "env_value"
    finally:
        os.environ.pop("HOST", None)
