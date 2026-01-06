"""
Tests for Env source.
"""

from dataclasses import dataclass, field

from varlord.sources.env import Env


@dataclass
class EnvTestConfig:
    host: str = field(
        default="localhost",
    )
    port: int = field(
        default=8000,
    )


@dataclass
class DBConfig:
    host: str = field(
        default="localhost",
    )
    port: int = field(
        default=5432,
    )


@dataclass
class NestedTestConfig:
    db: DBConfig = field(
        default_factory=lambda: DBConfig(),
    )


def test_env_basic(monkeypatch):
    """Test basic environment variable loading (filtered by model)."""
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("OTHER_VAR", "ignored")  # Should be ignored

    source = Env(model=EnvTestConfig)
    config = source.load()

    assert config["host"] == "0.0.0.0"
    assert config["port"] == "9000"
    assert "other_var" not in config  # Filtered out


def test_env_nested_keys(monkeypatch):
    """Test nested keys with unified normalization."""
    monkeypatch.setenv("DB__HOST", "localhost")
    monkeypatch.setenv("DB__PORT", "5432")

    source = Env(model=NestedTestConfig)
    config = source.load()

    assert config["db.host"] == "localhost"
    assert config["db.port"] == "5432"


def test_env_model_filtering(monkeypatch):
    """Test that env source only loads model fields."""
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("UNRELATED_VAR", "value")

    source = Env(model=EnvTestConfig)
    config = source.load()

    assert "host" in config
    assert "unrelated_var" not in config  # Filtered out


def test_env_name():
    """Test source name."""
    source = Env(model=EnvTestConfig)
    assert source.name == "env"
