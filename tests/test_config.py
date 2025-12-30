"""
Tests for Config class.
"""

import pytest
from dataclasses import dataclass
from varlord import Config, sources


def test_config_basic(sample_config_model):
    """Test basic config loading."""
    cfg = Config(
        model=sample_config_model,
        sources=[
            sources.Defaults(model=sample_config_model),
        ],
    )

    app = cfg.load()
    assert app.host == "127.0.0.1"
    assert app.port == 8000
    assert app.debug is False


def test_config_with_env(sample_config_model, monkeypatch):
    """Test config with environment variables."""
    monkeypatch.setenv("APP_HOST", "0.0.0.0")
    monkeypatch.setenv("APP_PORT", "9000")

    cfg = Config(
        model=sample_config_model,
        sources=[
            sources.Defaults(model=sample_config_model),
            sources.Env(prefix="APP_"),
        ],
    )

    app = cfg.load()
    assert app.host == "0.0.0.0"  # Overridden by env
    assert app.port == 9000  # Overridden by env (type conversion works)
    assert app.debug is False


def test_config_priority(sample_config_model, monkeypatch):
    """Test config priority ordering."""
    monkeypatch.setenv("APP_HOST", "env_value")

    # Priority is determined by sources order: later sources override earlier ones
    cfg = Config(
        model=sample_config_model,
        sources=[
            sources.Defaults(model=sample_config_model),
            sources.Env(prefix="APP_"),  # Later source overrides earlier one
        ],
    )

    app = cfg.load()
    assert app.host == "env_value"
