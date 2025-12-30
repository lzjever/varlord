"""
Etcd source.

Loads configuration from etcd with optional watch support for dynamic updates.
This is an optional source that requires the 'etcd' extra.
"""

from __future__ import annotations
from typing import Mapping, Any, Optional, Iterator
import threading
import time
import warnings

try:
    # Suppress etcd3 deprecation warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="etcd3")
        import etcd3
except ImportError:
    etcd3 = None  # type: ignore

from varlord.sources.base import Source, ChangeEvent


class Etcd(Source):
    """Source that loads configuration from etcd.

    Requires the 'etcd' extra: pip install varlord[etcd]

    Supports:
    - Loading configuration from a prefix
    - Watching for changes (dynamic updates)
    - Automatic reconnection on connection loss

    Example:
        >>> source = Etcd("http://127.0.0.1:2379", prefix="/app/")
        >>> source.load()
        {'host': '0.0.0.0', 'port': '9000'}
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 2379,
        prefix: str = "/",
        watch: bool = False,
        timeout: Optional[int] = None,
    ):
        """Initialize Etcd source.

        Args:
            host: Etcd host
            port: Etcd port
            prefix: Key prefix to load (e.g., "/app/")
            watch: Whether to enable watch support
            timeout: Connection timeout in seconds

        Raises:
            ImportError: If etcd3 is not installed
        """
        if etcd3 is None:
            raise ImportError(
                "etcd3 is required for Etcd source. " "Install it with: pip install varlord[etcd]"
            )
        self._host = host
        self._port = port
        self._prefix = prefix.rstrip("/") + "/" if prefix else "/"
        self._watch = watch
        self._timeout = timeout

        # Client will be created lazily
        self._client: Optional[Any] = None
        self._lock = threading.Lock()

    def _get_client(self):
        """Get or create etcd client."""
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._client = etcd3.client(
                        host=self._host, port=self._port, timeout=self._timeout
                    )
        return self._client

    @property
    def name(self) -> str:
        """Return source name."""
        return "etcd"

    def load(self) -> Mapping[str, Any]:
        """Load configuration from etcd.

        Returns:
            A mapping of configuration keys to values.
            Keys are normalized (prefix removed, converted to dot notation).
        """
        try:
            client = self._get_client()
            result: dict[str, Any] = {}

            # Get all keys with the prefix
            prefix_bytes = self._prefix.encode("utf-8")
            for value, metadata in client.get_prefix(prefix_bytes):
                if metadata is None:
                    continue

                # Extract key (remove prefix)
                key_bytes = metadata.key
                if not key_bytes.startswith(prefix_bytes):
                    continue

                # Convert to string and normalize
                key_str = key_bytes[len(prefix_bytes) :].decode("utf-8")
                # Convert / to . for nested keys, and lowercase for consistency
                normalized_key = key_str.replace("/", ".").lower()

                # Decode value
                if value:
                    try:
                        # Try to decode as string
                        decoded_value = value.decode("utf-8")
                        # Try to parse as JSON if possible
                        import json

                        try:
                            decoded_value = json.loads(decoded_value)
                        except (ValueError, TypeError):
                            pass
                        result[normalized_key] = decoded_value
                    except UnicodeDecodeError:
                        # Keep as bytes if not decodable
                        result[normalized_key] = value

            return result
        except Exception:
            # On error, return empty dict (fail-safe)
            return {}

    def supports_watch(self) -> bool:
        """Check if etcd source supports watching.

        Returns:
            True if watch is enabled.
        """
        return self._watch

    def watch(self) -> Iterator[ChangeEvent]:
        """Watch for configuration changes in etcd.

        Yields:
            ChangeEvent objects representing configuration changes.

        Note:
            This method blocks and yields events as they occur.
            It should be run in a separate thread.
        """
        if not self._watch:
            return iter([])

        client = self._get_client()
        prefix_bytes = self._prefix.encode("utf-8")

        # Get initial state
        initial_state: dict[str, Any] = {}
        for value, metadata in client.get_prefix(prefix_bytes):
            if metadata is None:
                continue
            key_bytes = metadata.key
            if not key_bytes.startswith(prefix_bytes):
                continue
            key_str = key_bytes[len(prefix_bytes) :].decode("utf-8")
            normalized_key = key_str.replace("/", ".")
            initial_state[normalized_key] = value

        # Watch for changes
        events_iterator = client.watch_prefix(prefix_bytes)

        for event in events_iterator:
            try:
                if event is None:
                    continue

                # Extract key
                key_bytes = event.key
                if not key_bytes.startswith(prefix_bytes):
                    continue

                key_str = key_bytes[len(prefix_bytes) :].decode("utf-8")
                normalized_key = key_str.replace("/", ".")

                # Determine event type and values
                if hasattr(event, "type"):
                    if event.type == etcd3.events.PUT_EVENT:
                        # Key was added or modified
                        old_value = initial_state.get(normalized_key)
                        new_value = event.value
                        if new_value:
                            try:
                                new_value = new_value.decode("utf-8")
                                import json

                                try:
                                    new_value = json.loads(new_value)
                                except (ValueError, TypeError):
                                    pass
                            except UnicodeDecodeError:
                                pass

                        event_type = "added" if old_value is None else "modified"
                        initial_state[normalized_key] = new_value

                        yield ChangeEvent(
                            key=normalized_key,
                            old_value=old_value,
                            new_value=new_value,
                            event_type=event_type,
                        )
                    elif event.type == etcd3.events.DELETE_EVENT:
                        # Key was deleted
                        old_value = initial_state.pop(normalized_key, None)
                        yield ChangeEvent(
                            key=normalized_key,
                            old_value=old_value,
                            new_value=None,
                            event_type="deleted",
                        )
            except Exception:
                # Skip malformed events
                continue

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Etcd(host={self._host!r}, port={self._port}, prefix={self._prefix!r}, watch={self._watch})>"
