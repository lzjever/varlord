"""
ConfigStore for runtime configuration management.

Provides thread-safe access to configuration with support for
dynamic updates and change subscriptions.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, is_dataclass
from typing import Any, Callable, Dict, Iterator, Optional, Type

from varlord.resolver import Resolver
from varlord.sources.base import ChangeEvent


@dataclass
class ConfigDiff:
    """Represents changes between two configuration snapshots."""

    added: Dict[str, Any]
    modified: Dict[str, tuple[Any, Any]]  # (old_value, new_value)
    deleted: Dict[str, Any]


class ConfigStore:
    """Thread-safe configuration store with dynamic update support.

    Provides:
    - Atomic configuration snapshots
    - Thread-safe get() and attribute access
    - Change subscriptions
    - Automatic validation on updates
    """

    def __init__(
        self,
        resolver: Resolver,
        model: Type[Any],
    ):
        """Initialize ConfigStore.

        Args:
            resolver: Resolver for merging sources
            model: Dataclass model for type conversion and validation

        Note:
            Watch is automatically enabled if any source supports it.
        """
        self._resolver = resolver
        self._model = model

        # Thread-safe storage
        self._lock = threading.RLock()
        self._config: Optional[Any] = None
        self._config_dict: Dict[str, Any] = {}

        # Subscribers
        self._subscribers: list[Callable[[Any, ConfigDiff], None]] = []

        # Watch thread
        self._watch_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Initial load
        self._reload()

        # Automatically enable watch if any source supports it
        if self._has_watchable_sources():
            self._start_watching()

    def _reload(self) -> None:
        """Reload configuration from all sources."""
        with self._lock:
            try:
                # Resolve configuration
                config_dict = self._resolver.resolve()

                # Convert to model instance
                new_config = self._dict_to_model(config_dict)

                # Validate (basic check - model instantiation validates types)
                # If validation fails, exception will be raised

                # Calculate diff
                diff = self._calculate_diff(self._config_dict, config_dict)

                # Atomically replace
                self._config = new_config
                self._config_dict = config_dict

                # Notify subscribers
                if diff.added or diff.modified or diff.deleted:
                    for callback in self._subscribers:
                        try:
                            callback(new_config, diff)
                        except Exception:
                            # Don't let subscriber errors break the update
                            pass

            except Exception:
                # Fail-safe: keep old configuration on error
                # In production, you might want to log this
                if self._config is None:
                    raise  # First load must succeed
                # Otherwise, silently keep old config

    def _dict_to_model(self, config_dict: Dict[str, Any]) -> Any:
        """Convert dictionary to model instance.

        Supports both flat keys (host) and nested keys (db.host) with automatic
        mapping to nested dataclass structures.

        Args:
            config_dict: Configuration dictionary with keys in dot notation (e.g., "db.host")

        Returns:
            Model instance
        """
        if not is_dataclass(self._model):
            raise TypeError(f"Model must be a dataclass, got {type(self._model)}")

        # Convert flat dict with dot notation to nested structure
        nested_dict = self._flatten_to_nested(config_dict, self._model)

        # Create model instance
        return self._model(**nested_dict)

    def _flatten_to_nested(self, flat_dict: Dict[str, Any], model: type) -> Dict[str, Any]:
        """Convert flat dict with dot notation to nested structure.

        Example:
            {"db.host": "localhost", "db.port": 5432, "host": "0.0.0.0"}
            → {"db": {"host": "localhost", "port": 5432}, "host": "0.0.0.0"}

        Args:
            flat_dict: Flat dictionary with dot-notation keys
            model: Dataclass model to map to

        Returns:
            Nested dictionary matching the model structure
        """
        from dataclasses import asdict, fields

        from varlord.converters import convert_value

        field_info = {f.name: f for f in fields(model)}
        result: Dict[str, Any] = {}

        # Step 1: Convert all dataclass instances in flat_dict to dicts
        flat_dict_processed = {}
        for key, value in flat_dict.items():
            if is_dataclass(type(value)):
                flat_dict_processed[key] = asdict(value)
            else:
                flat_dict_processed[key] = value

        # Step 2: Process flat keys first (non-nested)
        for key, value in flat_dict_processed.items():
            if "." not in key:
                if key in field_info:
                    field = field_info[key]
                    try:
                        converted_value = convert_value(value, field.type, key=key)
                        result[key] = converted_value
                    except (ValueError, TypeError):
                        result[key] = value

        # Step 3: Process nested keys
        for key, value in flat_dict_processed.items():
            if "." in key:
                parts = key.split(".", 1)
                parent_key = parts[0]
                child_key = parts[1]

                if parent_key in field_info:
                    field = field_info[parent_key]
                    if is_dataclass(field.type):
                        # Initialize parent dict if needed
                        if parent_key not in result:
                            # Use value from flat_dict_processed if available
                            if parent_key in flat_dict_processed:
                                parent_value = flat_dict_processed[parent_key]
                                if isinstance(parent_value, dict):
                                    result[parent_key] = parent_value.copy()
                                else:
                                    result[parent_key] = {}
                            else:
                                result[parent_key] = {}
                        elif not isinstance(result[parent_key], dict):
                            result[parent_key] = {}

                        # Recursively process nested structure
                        # First, get existing nested values to preserve them
                        existing_nested = {}
                        if parent_key in result and isinstance(result[parent_key], dict):
                            for k, v in result[parent_key].items():
                                if is_dataclass(type(v)):
                                    existing_nested[k] = asdict(v)
                                elif isinstance(v, dict):
                                    existing_nested[k] = v.copy()
                                else:
                                    existing_nested[k] = v

                        # Merge existing values with the new nested key
                        nested_flat = {child_key: value}
                        if existing_nested:
                            # Merge existing nested values into nested_flat for recursive processing
                            for k, v in existing_nested.items():
                                if k not in nested_flat:
                                    nested_flat[k] = v

                        nested_result = self._flatten_to_nested(nested_flat, field.type)

                        # Update result[parent_key] with nested_result (all values are now in nested_result)
                        for nested_key, nested_value in nested_result.items():
                            if is_dataclass(type(nested_value)):
                                result[parent_key][nested_key] = asdict(nested_value)
                            else:
                                result[parent_key][nested_key] = nested_value

        # Step 4: Convert nested dicts to dataclass instances with type conversion
        for key, value in list(result.items()):
            if key in field_info:
                field = field_info[key]
                if is_dataclass(field.type) and isinstance(value, dict):
                    # First, convert any dataclass instances in value to dicts
                    value_dict = {}
                    for nested_key, nested_value in value.items():
                        if is_dataclass(type(nested_value)):
                            value_dict[nested_key] = asdict(nested_value)
                        else:
                            value_dict[nested_key] = nested_value
                    # Recursively process and convert types
                    nested_instance = self._flatten_to_nested(value_dict, field.type)
                    # Convert all values to correct types
                    nested_fields = {f.name: f for f in fields(field.type)}
                    for nested_key, nested_value in nested_instance.items():
                        if nested_key in nested_fields:
                            nested_field = nested_fields[nested_key]
                            try:
                                nested_instance[nested_key] = convert_value(
                                    nested_value, nested_field.type, key=f"{key}.{nested_key}"
                                )
                            except (ValueError, TypeError):
                                pass
                    result[key] = field.type(**nested_instance)

        return result

    def _calculate_diff(self, old_dict: Dict[str, Any], new_dict: Dict[str, Any]) -> ConfigDiff:
        """Calculate difference between two configuration dictionaries.

        Args:
            old_dict: Old configuration
            new_dict: New configuration

        Returns:
            ConfigDiff object
        """
        added = {k: v for k, v in new_dict.items() if k not in old_dict}
        modified = {
            k: (old_dict[k], v) for k, v in new_dict.items() if k in old_dict and old_dict[k] != v
        }
        deleted = {k: old_dict[k] for k in old_dict if k not in new_dict}

        return ConfigDiff(added=added, modified=modified, deleted=deleted)

    def _has_watchable_sources(self) -> bool:
        """Check if any source supports watching.

        Returns:
            True if at least one source supports watching (supports_watch() returns True).
        """
        for source in self._resolver._sources:
            if source.supports_watch():
                return True
        return False

    def _start_watching(self) -> None:
        """Start watching for configuration changes."""
        if self._watch_thread and self._watch_thread.is_alive():
            return

        def watch_loop():
            """Watch loop for monitoring changes."""
            # Watch each source that supports watching
            watch_threads = []
            for source in self._resolver._sources:
                try:
                    # Only watch sources that explicitly support it
                    if source.supports_watch():
                        watch_iter = source.watch()

                        # Start a thread for each source's watch stream
                        def source_watch(source_name: str, watch_iter: Iterator[ChangeEvent]):
                            """Watch a single source."""
                            backoff = 1.0
                            max_backoff = 60.0
                            while not self._stop_event.is_set():
                                try:
                                    for event in watch_iter:
                                        if self._stop_event.is_set():
                                            break
                                        # On change, reload configuration
                                        self._reload()
                                        backoff = 1.0  # Reset backoff on success
                                except StopIteration:
                                    # Iterator exhausted, exit
                                    break
                                except Exception:
                                    # On error, try to reconnect after delay with backoff
                                    if not self._stop_event.is_set():
                                        time.sleep(backoff)
                                        backoff = min(backoff * 2, max_backoff)
                                        # Try to get a new iterator
                                        try:
                                            watch_iter = source.watch()
                                        except Exception:
                                            pass

                        t = threading.Thread(
                            target=source_watch,
                            args=(source.name, watch_iter),
                            daemon=True,
                        )
                        t.start()
                        watch_threads.append(t)
                except Exception:
                    # Source doesn't support watching or watch() failed
                    pass

            # Wait for stop event
            self._stop_event.wait()

        self._watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self._watch_thread.start()

    def get(self) -> Any:
        """Get current configuration (thread-safe).

        Returns:
            Current model instance
        """
        with self._lock:
            return self._config

    def to_dict(self) -> Dict[str, Any]:
        """Get current configuration as dictionary (thread-safe).

        Returns:
            Current configuration dictionary
        """
        with self._lock:
            return self._config_dict.copy()

    def subscribe(self, callback: Callable[[Any, ConfigDiff], None]) -> None:
        """Subscribe to configuration changes.

        Args:
            callback: Function called with (new_config, diff) on changes

        Note:
            Callbacks are called when:
            - Configuration changes are detected via watch (if any source supports it)
            - Manual reload() is called and configuration has changed

            If no sources support watch, callbacks will only be called on manual reload().
        """
        with self._lock:
            self._subscribers.append(callback)

    def reload(self) -> None:
        """Manually reload configuration from sources."""
        self._reload()

    def __getattr__(self, name: str) -> Any:
        """Allow attribute access to configuration."""
        config = self.get()
        return getattr(config, name)

    def __repr__(self) -> str:
        """Return string representation."""
        watching = self._watch_thread is not None and self._watch_thread.is_alive()
        return f"<ConfigStore(model={self._model.__name__}, watching={watching})>"
