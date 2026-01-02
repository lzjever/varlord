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
        items: list = field(default_factory=list, metadata={"optional": True})
        count: int = field(default=0, metadata={"optional": True})

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


def test_defaults_precomputed():
    """Test precomputed defaults."""
    from dataclasses import dataclass, field

    @dataclass
    class Config:
        host: str = field(default="localhost", metadata={"optional": True})
        port: int = field(default=8000, metadata={"optional": True})

    source = Defaults(model=Config)
    source._precomputed_defaults = {"host": "precomputed", "port": 9999}

    config = source.load()
    assert config["host"] == "precomputed"
    assert config["port"] == 9999
