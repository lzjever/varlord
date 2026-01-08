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


def test_env_with_prefix(monkeypatch):
    """Test environment variable loading with prefix."""
    monkeypatch.setenv("APP__HOST", "0.0.0.0")
    monkeypatch.setenv("APP__PORT", "9000")
    monkeypatch.setenv("HOST", "localhost")  # Should be ignored (no prefix)
    monkeypatch.setenv("OTHER__VAR", "ignored")  # Should be ignored (wrong prefix)

    source = Env(model=EnvTestConfig, prefix="APP__")
    config = source.load()

    assert config["host"] == "0.0.0.0"
    assert config["port"] == "9000"
    assert len(config) == 2  # Only prefixed vars should be loaded


def test_env_prefix_case_insensitive(monkeypatch):
    """Test that prefix matching is case-insensitive."""
    monkeypatch.setenv("app__host", "lowercase-prefix")  # Lowercase prefix
    monkeypatch.setenv("APP__PORT", "9000")  # Uppercase prefix

    source = Env(model=EnvTestConfig, prefix="APP__")
    config = source.load()

    assert config["host"] == "lowercase-prefix"
    assert config["port"] == "9000"


def test_env_prefix_with_nested_keys(monkeypatch):
    """Test prefix with nested configuration keys."""
    monkeypatch.setenv("APP__DB__HOST", "db.example.com")
    monkeypatch.setenv("APP__DB__PORT", "5432")
    monkeypatch.setenv("DB__HOST", "localhost")  # Should be ignored (no prefix)

    source = Env(model=NestedTestConfig, prefix="APP__")
    config = source.load()

    assert config["db.host"] == "db.example.com"
    assert config["db.port"] == "5432"
    assert "db.host" not in config or config.get("db.host") != "localhost"


def test_env_prefix_isolation(monkeypatch):
    """Test that prefix isolates environment variables."""
    monkeypatch.setenv("APP1__HOST", "app1-host")
    monkeypatch.setenv("APP2__HOST", "app2-host")
    monkeypatch.setenv("HOST", "no-prefix-host")

    # Test APP1 prefix
    source1 = Env(model=EnvTestConfig, prefix="APP1__")
    config1 = source1.load()
    assert config1["host"] == "app1-host"

    # Test APP2 prefix
    source2 = Env(model=EnvTestConfig, prefix="APP2__")
    config2 = source2.load()
    assert config2["host"] == "app2-host"

    # Test no prefix
    source3 = Env(model=EnvTestConfig)
    config3 = source3.load()
    assert config3["host"] == "no-prefix-host"


def test_env_source_id_with_prefix():
    """Test that source ID includes prefix when provided."""
    source1 = Env(model=EnvTestConfig)
    assert source1.id == "env"

    source2 = Env(model=EnvTestConfig, prefix="APP__")
    assert source2.id == "env:APP__"


def test_env_repr_with_prefix():
    """Test string representation with prefix."""
    source1 = Env(model=EnvTestConfig)
    assert "<Env(model-based)>" in repr(source1) or "Env" in repr(source1)

    source2 = Env(model=EnvTestConfig, prefix="APP__")
    assert "prefix='APP__'" in repr(source2) or "APP__" in repr(source2)
