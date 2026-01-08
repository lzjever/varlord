"""
Global configuration registry.

Provides optional global access to configuration objects without needing
to pass them around. This is useful for application-wide configuration
that is initialized once at startup.

Note: This is an optional feature. You can still use Config and ConfigStore
normally without global registration.

Example:
    # At application startup
    from varlord import Config, sources
    from varlord.global_config import set_global_config, get_global_config

    cfg = Config(
        model=AppConfig,
        sources=[sources.Env(), sources.CLI()],
    )
    set_global_config(cfg)

    # Anywhere in your application
    config = get_global_config()
    app = config.load()

    # Or with named configurations
    set_global_config(cfg, name="app")
    set_global_config(db_cfg, name="database")
    app_config = get_global_config(name="app")
    db_config = get_global_config(name="database")
"""

from __future__ import annotations

import threading
from typing import Any, Dict

from varlord.config import Config
from varlord.store import ConfigStore

# Thread-local storage for global configurations
_thread_local = threading.local()


def _get_registry() -> Dict[str, Any]:
    """Get thread-local registry for configurations."""
    if not hasattr(_thread_local, "registry"):
        _thread_local.registry = {}
    return _thread_local.registry


def set_global_config(
    config: Config | ConfigStore,
    name: str = "default",
    overwrite: bool = True,
) -> None:
    """Register a configuration object globally.

    Args:
        config: Config or ConfigStore instance to register
        name: Name for the configuration (default: "default")
        overwrite: Whether to overwrite existing configuration with same name (default: True)

    Raises:
        ValueError: If name already exists and overwrite=False
        TypeError: If config is not a Config or ConfigStore instance

    Example:
        >>> cfg = Config(model=AppConfig, sources=[sources.Env()])
        >>> set_global_config(cfg)
        >>> # Later, anywhere in your code
        >>> config = get_global_config()
        >>> app = config.load()

    Note:
        - Configurations are stored per-thread (thread-local)
        - This allows different threads to have different configurations if needed
        - For most use cases, you'll use the default name
    """
    if not isinstance(config, (Config, ConfigStore)):
        raise TypeError(
            f"config must be a Config or ConfigStore instance, got {type(config).__name__}"
        )

    registry = _get_registry()

    if name in registry and not overwrite:
        raise ValueError(
            f"Configuration '{name}' already exists. Use overwrite=True to replace it."
        )

    registry[name] = config


def get_global_config(name: str = "default") -> Config | ConfigStore:
    """Get a globally registered configuration object.

    Args:
        name: Name of the configuration (default: "default")

    Returns:
        Config or ConfigStore instance

    Raises:
        KeyError: If configuration with given name is not found

    Example:
        >>> config = get_global_config()
        >>> app = config.load()

        >>> # With named configurations
        >>> app_config = get_global_config(name="app")
        >>> db_config = get_global_config(name="database")

    Note:
        - Returns the same instance that was registered
        - For Config instances, you still need to call load() or load_store()
        - For ConfigStore instances, you can directly call get()
    """
    registry = _get_registry()

    if name not in registry:
        raise KeyError(
            f"Configuration '{name}' not found. "
            f"Available configurations: {list(registry.keys())}. "
            f"Did you forget to call set_global_config()?"
        )

    return registry[name]


def has_global_config(name: str = "default") -> bool:
    """Check if a global configuration exists.

    Args:
        name: Name of the configuration (default: "default")

    Returns:
        True if configuration exists, False otherwise

    Example:
        >>> if has_global_config():
        ...     config = get_global_config()
        ...     app = config.load()
    """
    registry = _get_registry()
    return name in registry


def remove_global_config(name: str = "default") -> None:
    """Remove a globally registered configuration.

    Args:
        name: Name of the configuration to remove (default: "default")

    Raises:
        KeyError: If configuration with given name is not found

    Example:
        >>> remove_global_config()
        >>> # Or remove a named configuration
        >>> remove_global_config(name="app")
    """
    registry = _get_registry()

    if name not in registry:
        raise KeyError(f"Configuration '{name}' not found")

    del registry[name]


def clear_global_configs() -> None:
    """Clear all globally registered configurations.

    Example:
        >>> clear_global_configs()
    """
    registry = _get_registry()
    registry.clear()


def list_global_configs() -> list[str]:
    """List all registered global configuration names.

    Returns:
        List of configuration names

    Example:
        >>> set_global_config(cfg1, name="app")
        >>> set_global_config(cfg2, name="database")
        >>> names = list_global_configs()
        >>> print(names)  # ['app', 'database']
    """
    registry = _get_registry()
    return list(registry.keys())
