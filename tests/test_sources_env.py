"""
Tests for Env source.
"""

import os
import pytest
from varlord.sources.env import Env


def test_env_basic(monkeypatch):
    """Test basic environment variable loading."""
    monkeypatch.setenv("TEST_HOST", "0.0.0.0")
    monkeypatch.setenv("TEST_PORT", "9000")

    source = Env(prefix="TEST_")
    config = source.load()

    assert config["host"] == "0.0.0.0"
    assert config["port"] == "9000"


def test_env_nested_keys(monkeypatch):
    """Test nested keys with separator."""
    monkeypatch.setenv("APP_DB__HOST", "localhost")
    monkeypatch.setenv("APP_DB__PORT", "5432")

    source = Env(prefix="APP_", separator="__")
    config = source.load()

    assert config["db.host"] == "localhost"
    assert config["db.port"] == "5432"


def test_env_no_prefix(monkeypatch):
    """Test env without prefix."""
    monkeypatch.setenv("SOME_VAR", "value")

    source = Env(prefix="")
    config = source.load()

    assert "some.var" in config or "some_var" in config


def test_env_name():
    """Test source name."""
    source = Env()
    assert source.name == "env"
