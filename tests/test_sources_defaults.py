"""
Tests for Defaults source.
"""

import pytest
from dataclasses import dataclass, field
from varlord.sources.defaults import Defaults


def test_defaults_basic(sample_config_model):
    """Test basic defaults loading."""
    source = Defaults(model=sample_config_model)
    config = source.load()

    assert config["host"] == "127.0.0.1"
    assert config["port"] == 8000
    assert config["debug"] is False
    assert config["timeout"] == 30.0


def test_defaults_with_factory():
    """Test defaults with default_factory."""

    @dataclass
    class Config:
        items: list = field(default_factory=list)
        count: int = 0

    source = Defaults(model=Config)
    config = source.load()

    assert config["items"] == []
    assert config["count"] == 0


def test_defaults_non_dataclass():
    """Test that non-dataclass raises error."""

    class NotADataclass:
        pass

    with pytest.raises(TypeError):
        Defaults(model=NotADataclass)


def test_defaults_name():
    """Test source name."""

    @dataclass
    class Config:
        pass

    source = Defaults(model=Config)
    assert source.name == "defaults"
