"""
Etcd source.

Loads configuration from ``etcd`` with optional watch support for dynamic updates.
This is an optional source that requires the ``etcd`` extra.
"""

from __future__ import annotations

import os
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
except ImportError:
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
    - Configuration from environment variables via from_env()

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

    From Environment Variables (Recommended):
        >>> # Set ETCD_HOST, ETCD_PORT, ETCD_CA_CERT, etc.
        >>> source = Etcd.from_env(prefix="/app/")
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

        Raises:
            ImportError: If etcd3 is not installed
        """
        super().__init__(model=model)
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

    @classmethod
    def from_env(
        cls,
        prefix: Optional[str] = None,
        watch: Optional[bool] = None,
        timeout: Optional[int] = None,
        model: Optional[Type[Any]] = None,
        env_prefix: str = "ETCD_",
    ) -> Etcd:
        """Create ``Etcd`` source from environment variables.

        Reads connection configuration from environment variables.

        Note: This method creates an ``Etcd`` source configured from environment
        variables. The service must be accessible for this source to work.

        The following environment variables are read:
        - ETCD_HOST (default: "127.0.0.1")
        - ETCD_PORT (default: 2379)
        - ETCD_PREFIX (default: "/")
        - ETCD_CA_CERT (optional: path to CA certificate)
        - ETCD_CERT_KEY (optional: path to client key)
        - ETCD_CERT_CERT (optional: path to client certificate)
        - ETCD_USER (optional: username for authentication)
        - ETCD_PASSWORD (optional: password for authentication)
        - ETCD_WATCH (optional: "true" or "1" to enable watch)
        - ETCD_TIMEOUT (optional: connection timeout in seconds)

        Args:
            prefix: Key prefix to load (overrides ETCD_PREFIX if provided)
            watch: Whether to enable watch support (overrides ETCD_WATCH if provided)
            timeout: Connection timeout in seconds (overrides ETCD_TIMEOUT if provided)
            model: Model to filter configuration keys (auto-injected by Config if not provided)
            env_prefix: Prefix for environment variable names (default: "ETCD_")

        Returns:
            :class:`Etcd` source instance configured from environment variables

        Example:
            >>> # Set environment variables:
            >>> # export ETCD_HOST=192.168.0.220
            >>> # export ETCD_PORT=2379
            >>> # export ETCD_CA_CERT=./cert/ca.cert.pem
            >>> # export ETCD_CERT_KEY=./cert/key.pem
            >>> # export ETCD_CERT_CERT=./cert/cert.pem
            >>> source = Etcd.from_env(prefix="/app/")
        """
        # Read configuration from environment variables
        host = os.environ.get(f"{env_prefix}HOST", "127.0.0.1")
        port = int(os.environ.get(f"{env_prefix}PORT", "2379"))

        # Use provided prefix or read from env
        if prefix is not None:
            etcd_prefix = prefix
        else:
            etcd_prefix = os.environ.get(f"{env_prefix}PREFIX")
            if etcd_prefix is None:
                etcd_prefix = "/"

        # TLS certificates (optional)
        ca_cert = os.environ.get(f"{env_prefix}CA_CERT")
        cert_key = os.environ.get(f"{env_prefix}CERT_KEY")
        cert_cert = os.environ.get(f"{env_prefix}CERT_CERT")

        # Authentication (optional)
        user = os.environ.get(f"{env_prefix}USER")
        password = os.environ.get(f"{env_prefix}PASSWORD")

        # Watch (can be overridden by parameter)
        # If watch parameter is explicitly provided (not None), use it
        # Otherwise, read from environment variable
        if watch is not None:
            etcd_watch = watch
        else:
            watch_env = os.environ.get(f"{env_prefix}WATCH", "").lower()
            etcd_watch = watch_env in ("true", "1", "yes", "on")

        # Timeout (can be overridden by parameter)
        etcd_timeout = timeout
        if etcd_timeout is None:
            timeout_str = os.environ.get(f"{env_prefix}TIMEOUT")
            if timeout_str:
                try:
                    etcd_timeout = int(timeout_str)
                except ValueError:
                    etcd_timeout = None

        return cls(
            host=host,
            port=port,
            prefix=etcd_prefix,
            watch=etcd_watch,
            timeout=etcd_timeout,
            model=model,
            ca_cert=ca_cert,
            cert_key=cert_key,
            cert_cert=cert_cert,
            user=user,
            password=password,
        )

    def __repr__(self) -> str:
        """Return string representation."""
        tls_info = ""
        if self._ca_cert:
            tls_info = ", tls=True"
        auth_info = ""
        if self._user:
            auth_info = f", user={self._user!r}"
        return f"<Etcd(host={self._host!r}, port={self._port}, prefix={self._prefix!r}, watch={self._watch}{tls_info}{auth_info})>"
