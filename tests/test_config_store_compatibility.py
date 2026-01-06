"""
Tests for ConfigStore compatibility with new validation system.
"""

from dataclasses import dataclass, field

from varlord import Config, sources


def test_config_store_basic():
    """Test ConfigStore works with new validation system."""

    @dataclass
    class AppConfig:
        host: str = field(
            default="localhost",
        )
        port: int = field(
            default=8000,
        )

    cfg = Config(
        model=AppConfig,
        sources=[],
    )

    store = cfg.load_store()

    # Store should have config loaded
    config = store.get()
    assert config.host == "localhost"
    assert config.port == 8000


def test_config_store_with_sources():
    """Test ConfigStore with sources."""

    @dataclass
    class AppConfig:
        host: str = field(
            default="localhost",
        )
        port: int = field(
            default=8000,
        )

    import os

    os.environ["HOST"] = "0.0.0.0"

    try:
        cfg = Config(
            model=AppConfig,
            sources=[sources.Env()],
        )

        store = cfg.load_store()

        # Should use env value
        config = store.get()
        assert config.host == "0.0.0.0"
        assert config.port == 8000  # From defaults
    finally:
        os.environ.pop("HOST", None)


def test_config_store_auto_defaults():
    """Test ConfigStore automatically uses model defaults."""

    @dataclass
    class AppConfig:
        host: str = field(
            default="localhost",
        )
        port: int = field(
            default=8000,
        )

    cfg = Config(
        model=AppConfig,
        sources=[],  # No sources, but defaults should be applied
    )

    store = cfg.load_store()

    # Defaults should be available
    config = store.get()
    assert config.host == "localhost"
    assert config.port == 8000
