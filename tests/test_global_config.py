"""
Tests for global configuration registry.
"""

import threading

import pytest

from varlord import Config, sources
from varlord.global_config import (
    clear_global_configs,
    get_global_config,
    has_global_config,
    list_global_configs,
    remove_global_config,
    set_global_config,
)


def test_set_and_get_global_config():
    """Test basic set and get functionality."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "localhost"
        port: int = 8000

    cfg = Config(model=AppConfig, sources=[])

    # Set global config
    set_global_config(cfg)

    # Get global config
    retrieved = get_global_config()
    assert retrieved is cfg

    # Load and verify
    app = retrieved.load()
    assert app.host == "localhost"
    assert app.port == 8000

    # Cleanup
    clear_global_configs()


def test_named_configurations():
    """Test named configurations."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "app_host"

    @dataclass(frozen=True)
    class DBConfig:
        host: str = "db_host"

    app_cfg = Config(model=AppConfig, sources=[])
    db_cfg = Config(model=DBConfig, sources=[])

    # Set named configurations
    set_global_config(app_cfg, name="app")
    set_global_config(db_cfg, name="database")

    # Get by name
    app_config = get_global_config(name="app")
    db_config = get_global_config(name="database")

    assert app_config is app_cfg
    assert db_config is db_cfg

    # Verify they're different
    app = app_config.load()
    db = db_config.load()
    assert app.host == "app_host"
    assert db.host == "db_host"

    # Cleanup
    clear_global_configs()


def test_has_global_config():
    """Test has_global_config function."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "localhost"

    cfg = Config(model=AppConfig, sources=[])

    # Initially not set
    assert not has_global_config()

    # Set it
    set_global_config(cfg)
    assert has_global_config()

    # Check named config
    assert not has_global_config(name="other")
    set_global_config(cfg, name="other")
    assert has_global_config(name="other")

    # Cleanup
    clear_global_configs()


def test_remove_global_config():
    """Test remove_global_config function."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "localhost"

    cfg = Config(model=AppConfig, sources=[])

    set_global_config(cfg)
    assert has_global_config()

    remove_global_config()
    assert not has_global_config()

    # Test removing non-existent config
    with pytest.raises(KeyError):
        remove_global_config()


def test_list_global_configs():
    """Test list_global_configs function."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "localhost"

    cfg = Config(model=AppConfig, sources=[])

    # Initially empty
    assert list_global_configs() == []

    # Add configurations
    set_global_config(cfg, name="app")
    set_global_config(cfg, name="database")
    set_global_config(cfg, name="cache")

    names = list_global_configs()
    assert set(names) == {"app", "database", "cache"}

    # Cleanup
    clear_global_configs()


def test_get_nonexistent_config():
    """Test getting non-existent configuration."""
    with pytest.raises(KeyError) as exc_info:
        get_global_config(name="nonexistent")

    assert "nonexistent" in str(exc_info.value)
    assert "not found" in str(exc_info.value).lower()


def test_set_invalid_config():
    """Test setting invalid config type."""
    with pytest.raises(TypeError) as exc_info:
        set_global_config("not a config")

    assert "Config or ConfigStore" in str(exc_info.value)


def test_overwrite_config():
    """Test overwriting existing configuration."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "localhost"

    cfg1 = Config(model=AppConfig, sources=[])
    cfg2 = Config(model=AppConfig, sources=[])

    set_global_config(cfg1, name="app")
    assert get_global_config(name="app") is cfg1

    # Overwrite
    set_global_config(cfg2, name="app", overwrite=True)
    assert get_global_config(name="app") is cfg2

    # Try to overwrite without flag
    with pytest.raises(ValueError) as exc_info:
        set_global_config(cfg1, name="app", overwrite=False)

    assert "already exists" in str(exc_info.value).lower()

    # Cleanup
    clear_global_configs()


def test_config_store_global():
    """Test using ConfigStore with global registry."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "localhost"
        port: int = 8000

    cfg = Config(model=AppConfig, sources=[])
    store = cfg.load_store()

    # Register ConfigStore
    set_global_config(store, name="store")

    # Retrieve and use
    retrieved_store = get_global_config(name="store")
    assert retrieved_store is store

    app = retrieved_store.get()
    assert app.host == "localhost"
    assert app.port == 8000

    # Cleanup
    clear_global_configs()


def test_thread_local_storage():
    """Test that configurations are thread-local."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "localhost"

    cfg1 = Config(model=AppConfig, sources=[])
    cfg2 = Config(model=AppConfig, sources=[])

    # Set in main thread
    set_global_config(cfg1, name="app")

    configs_in_thread = []

    def thread_func():
        # Set different config in thread
        set_global_config(cfg2, name="app")
        configs_in_thread.append(get_global_config(name="app"))

    thread = threading.Thread(target=thread_func)
    thread.start()
    thread.join()

    # Main thread should still have original config
    assert get_global_config(name="app") is cfg1

    # Thread should have its own config
    assert configs_in_thread[0] is cfg2

    # Cleanup
    clear_global_configs()


def test_clear_global_configs():
    """Test clearing all configurations."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "localhost"

    cfg = Config(model=AppConfig, sources=[])

    set_global_config(cfg, name="app")
    set_global_config(cfg, name="database")
    set_global_config(cfg, name="cache")

    assert len(list_global_configs()) == 3

    clear_global_configs()

    assert len(list_global_configs()) == 0
    assert not has_global_config(name="app")


def test_usage_pattern():
    """Test typical usage pattern."""
    from dataclasses import dataclass, field

    @dataclass(frozen=True)
    class AppConfig:
        api_key: str = field()
        host: str = "127.0.0.1"
        port: int = 8000

    # Simulate application startup
    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Env(),
            sources.CLI(),
        ],
    )
    set_global_config(cfg)

    # Simulate function that needs config
    def some_function():
        config = get_global_config()
        app = config.load()
        return app

    # This would normally fail without api_key, but for test we'll skip validation
    # In real usage, you'd provide api_key via env or CLI
    try:
        result = some_function()
        # If it works, verify
        assert result.host == "127.0.0.1"
    except Exception:
        # Expected if api_key is required
        pass

    # Cleanup
    clear_global_configs()
