"""
Etcd source.

Loads configuration from ``etcd`` with optional watch support for dynamic updates.
This is an optional source that requires the ``etcd`` extra.
"""

from __future__ import annotations

import threading
import warnings
from typing import Any, Iterator, Mapping, Optional, Type

try:
    # Suppress etcd3 deprecation warnings from protobuf
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        import etcd3

        # Also suppress warnings from etcd3 submodules
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="etcd3")
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="etcd3.*")
except (ImportError, TypeError):
    # TypeError can occur with protobuf version incompatibility
    # If etcd3 is installed but incompatible, treat it as unavailable
    etcd3 = None  # type: ignore

from varlord.sources.base import ChangeEvent, Source, normalize_key


class Etcd(Source):
    """Source that loads configuration from ``etcd``.

    Requires the ``etcd`` extra: pip install varlord[etcd]

    Supports:
    - Loading configuration from a prefix
    - TLS/SSL certificate authentication
    - User authentication
    - Watching for changes (dynamic updates)
    - Automatic reconnection on connection loss

    Basic Example:
        >>> source = Etcd(
        ...     host="127.0.0.1",
        ...     port=2379,
        ...     prefix="/app/",
        ... )
        >>> source.load()
        {'host': '0.0.0.0', 'port': '9000'}

    With TLS:
        >>> source = Etcd(
        ...     host="192.168.0.220",
        ...     port=2379,
        ...     prefix="/app/",
        ...     ca_cert="./cert/ca.cert.pem",
        ...     cert_key="./cert/key.pem",
        ...     cert_cert="./cert/cert.pem",
        ... )

    Note:
        ⚠️ 重要变更：不再提供 from_env() 类方法。
        所有参数都通过 __init__ 传递，调用方负责获取初始配置信息。
        可以使用 Env source 或其他方式获取连接参数。
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 2379,
        prefix: str = "/",
        watch: bool = False,
        timeout: Optional[int] = None,
        model: Optional[Type[Any]] = None,
        ca_cert: Optional[str] = None,
        cert_key: Optional[str] = None,
        cert_cert: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> None:
        """Initialize Etcd source.

        Args:
            host: Etcd host
            port: Etcd port
            prefix: Key prefix to load (e.g., "/app/")
            watch: Whether to enable watch support
            timeout: Connection timeout in seconds
            model: Model to filter ``etcd`` keys.
                  Only keys that map to model fields will be loaded.
                  Model is required and will be auto-injected by Config.
            ca_cert: Path to CA certificate file for TLS
            cert_key: Path to client key file for TLS
            cert_cert: Path to client certificate file for TLS
            user: Username for authentication (optional)
            password: Password for authentication (optional)
            source_id: Optional unique identifier (default: auto-generated)

        Raises:
            ImportError: If etcd3 is not installed

        Note:
            ⚠️ 重要变更：不再提供 from_env() 类方法。
            所有参数都通过 __init__ 传递，调用方负责获取初始配置信息。
        """
        # Generate ID before calling super() if not provided
        if source_id is None:
            prefix_normalized = prefix.rstrip("/") + "/" if prefix else "/"
            source_id = f"etcd:{host}#{port}#{prefix_normalized}"
        super().__init__(model=model, source_id=source_id)
        if etcd3 is None:
            raise ImportError(
                "etcd3 is required for Etcd source. Install it with: pip install varlord[etcd]"
            )
        self._host = host
        self._port = port
        self._prefix = prefix.rstrip("/") + "/" if prefix else "/"
        self._watch = watch
        self._timeout = timeout
        self._ca_cert = ca_cert
        self._cert_key = cert_key
        self._cert_cert = cert_cert
        self._user = user
        self._password = password

        # Client will be created lazily
        self._client: Optional[Any] = None
        self._lock = threading.Lock()

    def _generate_id(self) -> str:
        """Generate unique ID for Etcd source.

        ⚠️ 注意：使用 # 作为分隔符，避免 host:port 格式导致两个冒号
        例如：etcd:127.0.0.1:2379 会变成 etcd:127.0.0.1:2379，有两个冒号
        使用 # 分隔：etcd:127.0.0.1#2379#/app/
        """
        return f"etcd:{self._host}#{self._port}#{self._prefix}"

    def _get_client(self):
        """Get or create ``etcd`` client."""
        if self._client is None:
            with self._lock:
                if self._client is None:
                    # Build client kwargs
                    client_kwargs = {
                        "host": self._host,
                        "port": self._port,
                    }
                    if self._timeout is not None:
                        client_kwargs["timeout"] = self._timeout
                    if self._ca_cert is not None:
                        client_kwargs["ca_cert"] = self._ca_cert
                    if self._cert_key is not None:
                        client_kwargs["cert_key"] = self._cert_key
                    if self._cert_cert is not None:
                        client_kwargs["cert_cert"] = self._cert_cert
                    if self._user is not None:
                        client_kwargs["user"] = self._user
                    if self._password is not None:
                        client_kwargs["password"] = self._password

                    self._client = etcd3.client(**client_kwargs)
        return self._client

    @property
    def name(self) -> str:
        """Return source name."""
        return "etcd"

    def load(self) -> Mapping[str, Any]:
        """Load configuration from ``etcd``, filtered by model fields.

        Returns:
            A mapping of configuration keys to values.
            Keys are normalized (prefix removed, converted to dot notation).
            Only includes keys that map to model fields.

        Raises:
            ValueError: If model is not provided
        """
        if not self._model:
            raise ValueError("Etcd source requires model (should be auto-injected by Config)")

        try:
            from varlord.metadata import get_all_field_keys

            # Get all valid field keys from model
            valid_keys = get_all_field_keys(self._model)

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
                # Convert / to __ (path separator to double underscore for nesting)
                key_str = key_str.replace("/", "__")
                # Apply unified normalization
                normalized_key = normalize_key(key_str)

                # Only load if it matches a model field
                if normalized_key not in valid_keys:
                    continue

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
        """Check if ``etcd`` source supports watching.

        Returns:
            True if watch is enabled.
        """
        return self._watch

    def watch(self) -> Iterator[ChangeEvent]:
        """Watch for configuration changes in ``etcd``.

        Yields:
            ChangeEvent objects representing configuration changes.

        Note:
            This method blocks and yields events as they occur.
            It should be run in a separate thread.
        """
        if not self._watch:
            return iter([])

        if not self._model:
            raise ValueError(
                "Etcd source requires model for watch (should be auto-injected by Config)"
            )

        from varlord.metadata import get_all_field_keys

        # Get all valid field keys from model (same as load method)
        valid_keys = get_all_field_keys(self._model)

        client = self._get_client()
        prefix_bytes = self._prefix.encode("utf-8")

        # Get initial state (decode values same way as load method)
        initial_state: dict[str, Any] = {}
        for value, metadata in client.get_prefix(prefix_bytes):
            if metadata is None:
                continue
            key_bytes = metadata.key
            if not key_bytes.startswith(prefix_bytes):
                continue
            key_str = key_bytes[len(prefix_bytes) :].decode("utf-8")
            key_str = key_str.replace("/", "__")
            normalized_key = normalize_key(key_str)

            # Only include keys that match model fields (same as load method)
            if normalized_key not in valid_keys:
                continue

            # Decode value same way as load method
            decoded_value = value
            if value:
                try:
                    decoded_value = value.decode("utf-8")
                    import json

                    try:
                        decoded_value = json.loads(decoded_value)
                    except (ValueError, TypeError):
                        pass
                except UnicodeDecodeError:
                    decoded_value = value
            initial_state[normalized_key] = decoded_value

        # Watch for changes
        # watch_prefix returns (events_iterator, cancel) tuple
        events_iterator, cancel = client.watch_prefix(prefix_bytes)

        for event in events_iterator:
            try:
                if event is None:
                    continue

                # Extract key
                key_bytes = event.key
                if not key_bytes.startswith(prefix_bytes):
                    continue

                key_str = key_bytes[len(prefix_bytes) :].decode("utf-8")
                key_str = key_str.replace("/", "__")
                normalized_key = normalize_key(key_str)

                # Only process events for keys that match model fields (same as load method)
                if normalized_key not in valid_keys:
                    continue

                # Determine event type and values
                # etcd3 events are PutEvent or DeleteEvent instances, not objects with type attribute
                if isinstance(event, etcd3.events.PutEvent):
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
                elif isinstance(event, etcd3.events.DeleteEvent):
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
        tls_info = ""
        if self._ca_cert:
            tls_info = ", tls=True"
        auth_info = ""
        if self._user:
            auth_info = f", user={self._user!r}"
        return f"<Etcd(host={self._host!r}, port={self._port}, prefix={self._prefix!r}, watch={self._watch}{tls_info}{auth_info})>"
