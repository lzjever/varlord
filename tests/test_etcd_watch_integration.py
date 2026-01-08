"""
Comprehensive integration tests for etcd watch, ConfigStore, and dynamic updates.

These tests verify:
1. Etcd source watch functionality (PUT, DELETE events)
2. Config.load_store() with watch support
3. ConfigStore.subscribe() callbacks
4. Multiple sources with watch support
5. Priority ordering with watch sources
6. Load behavior on watch-enabled source chains

To run these tests:
    pytest tests/test_etcd_watch_integration.py -m etcd
"""

import os
import threading
import time
import warnings
from collections import defaultdict
from dataclasses import dataclass, field

import pytest

# Suppress etcd3 deprecation warnings from protobuf
warnings.filterwarnings("ignore", category=DeprecationWarning, module="etcd3")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="etcd3.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="etcd3.etcdrpc.*")

# Mark all tests in this file as etcd integration tests
# Tests will be automatically deselected if etcd3 is not installed (via conftest.py)
try:
    import etcd3
except (ImportError, TypeError):
    # TypeError can occur with protobuf version incompatibility
    etcd3 = None

pytestmark = [pytest.mark.etcd, pytest.mark.integration, pytest.mark.requires_etcd]


# Etcd connection configuration
# All values must be provided via environment variables (no defaults)
# Required: ETCD_HOST, ETCD_PORT
# Optional: ETCD_CA_CERT, ETCD_CERT_KEY, ETCD_CERT_CERT
ETCD_HOST = os.environ.get("ETCD_HOST")
ETCD_PORT = os.environ.get("ETCD_PORT")
ETCD_CA_CERT = os.environ.get("ETCD_CA_CERT")
ETCD_CERT_KEY = os.environ.get("ETCD_CERT_KEY")
ETCD_CERT_CERT = os.environ.get("ETCD_CERT_CERT")


def require_etcd_config():
    """Check that required etcd configuration is available from environment variables."""
    if not ETCD_HOST or not ETCD_PORT:
        pytest.skip(
            "ETCD_HOST and ETCD_PORT environment variables are required. "
            "No default values are used. "
            "Example: export ETCD_HOST=192.168.0.220 ETCD_PORT=2379"
        )


def get_etcd_client():
    """Get a direct etcd client for test setup/teardown."""
    require_etcd_config()

    client_kwargs = {
        "host": ETCD_HOST,
        "port": int(ETCD_PORT),
    }

    if ETCD_CA_CERT and os.path.exists(ETCD_CA_CERT):
        client_kwargs["ca_cert"] = ETCD_CA_CERT
    if ETCD_CERT_KEY and os.path.exists(ETCD_CERT_KEY):
        client_kwargs["cert_key"] = ETCD_CERT_KEY
    if ETCD_CERT_CERT and os.path.exists(ETCD_CERT_CERT):
        client_kwargs["cert_cert"] = ETCD_CERT_CERT

    return etcd3.client(**client_kwargs)


def get_etcd_source_kwargs():
    """Get kwargs for creating Etcd source from environment variables."""
    require_etcd_config()

    kwargs = {
        "host": ETCD_HOST,
        "port": int(ETCD_PORT),
    }

    if ETCD_CA_CERT and os.path.exists(ETCD_CA_CERT):
        kwargs["ca_cert"] = ETCD_CA_CERT
    if ETCD_CERT_KEY and os.path.exists(ETCD_CERT_KEY):
        kwargs["cert_key"] = ETCD_CERT_KEY
    if ETCD_CERT_CERT and os.path.exists(ETCD_CERT_CERT):
        kwargs["cert_cert"] = ETCD_CERT_CERT

    return kwargs


@pytest.fixture
def etcd_client():
    """Fixture providing a direct etcd client for test setup."""
    require_etcd_config()

    # Check if certificates are provided and exist
    missing_certs = []
    if ETCD_CA_CERT and not os.path.exists(ETCD_CA_CERT):
        missing_certs.append(f"CA cert: {ETCD_CA_CERT}")
    if ETCD_CERT_KEY and not os.path.exists(ETCD_CERT_KEY):
        missing_certs.append(f"Client key: {ETCD_CERT_KEY}")
    if ETCD_CERT_CERT and not os.path.exists(ETCD_CERT_CERT):
        missing_certs.append(f"Client cert: {ETCD_CERT_CERT}")

    if missing_certs:
        pytest.skip(f"Etcd certificates not found. Missing: {', '.join(missing_certs)}")

    client = get_etcd_client()
    try:
        client.get("/test")
    except Exception as e:
        pytest.skip(f"Cannot connect to etcd at {ETCD_HOST}:{ETCD_PORT}: {e}")
    yield client


@pytest.fixture
def etcd_cleanup(etcd_client):
    """Fixture to clean up etcd keys after each test."""
    prefixes_to_clean = []

    def cleanup(prefix: str):
        """Register a prefix for cleanup."""
        prefixes_to_clean.append(prefix)
        # Clean up existing keys
        try:
            for value, meta in etcd_client.get_prefix(prefix):
                etcd_client.delete(meta.key.decode("utf-8"))
        except Exception:
            pass

    yield cleanup

    # Cleanup after test
    for prefix in prefixes_to_clean:
        try:
            for value, meta in etcd_client.get_prefix(prefix):
                etcd_client.delete(meta.key.decode("utf-8"))
        except Exception:
            pass


# Test models
@dataclass
class SimpleConfig:
    host: str = field()
    port: int = field(default=8000)
    debug: bool = field(default=False)


@dataclass
class NestedConfig:
    api_key: str = field()
    db_host: str = field()
    db_port: int = field(default=5432)


class TestEtcdWatchBasic:
    """Test basic etcd watch functionality."""

    def test_watch_put_event_single_key(self, etcd_client, etcd_cleanup):
        """Test watching for a single PUT event."""
        from varlord.sources.base import ChangeEvent
        from varlord.sources.etcd import Etcd

        prefix = "/test/watch/put/single/"
        etcd_cleanup(prefix)

        kwargs = get_etcd_source_kwargs()
        kwargs.update(
            {
                "prefix": prefix,
                "watch": True,
                "model": SimpleConfig,
            }
        )
        source = Etcd(**kwargs)

        events_received = []
        stop_event = threading.Event()

        def watch_thread():
            try:
                for event in source.watch():
                    events_received.append(event)
                    if len(events_received) >= 1:
                        stop_event.set()
                        break
            except Exception as e:
                print(f"Watch error: {e}")

        watch_thread_obj = threading.Thread(target=watch_thread, daemon=True)
        watch_thread_obj.start()

        # Wait for watch to establish
        time.sleep(1.0)

        # Trigger PUT event
        etcd_client.put(f"{prefix}host", "example.com")
        time.sleep(0.5)

        # Wait for event
        stop_event.wait(timeout=10.0)

        # Verify
        assert len(events_received) >= 1
        event = events_received[0]
        assert isinstance(event, ChangeEvent)
        assert event.key == "host"
        assert event.new_value == "example.com"
        assert event.event_type in ["added", "modified"]

    def test_watch_put_event_multiple_keys(self, etcd_client, etcd_cleanup):
        """Test watching for multiple PUT events."""
        from varlord.sources.etcd import Etcd

        prefix = "/test/watch/put/multiple/"
        etcd_cleanup(prefix)

        kwargs = get_etcd_source_kwargs()
        kwargs.update(
            {
                "prefix": prefix,
                "watch": True,
                "model": SimpleConfig,
            }
        )
        source = Etcd(**kwargs)

        events_received = []
        stop_event = threading.Event()

        def watch_thread():
            try:
                for event in source.watch():
                    events_received.append(event)
                    if len(events_received) >= 3:
                        stop_event.set()
                        break
            except Exception as e:
                print(f"Watch error: {e}")

        watch_thread_obj = threading.Thread(target=watch_thread, daemon=True)
        watch_thread_obj.start()

        time.sleep(1.0)

        # Trigger multiple PUT events
        etcd_client.put(f"{prefix}host", "example.com")
        time.sleep(0.3)
        etcd_client.put(f"{prefix}port", "9000")
        time.sleep(0.3)
        etcd_client.put(f"{prefix}debug", "true")
        time.sleep(0.5)

        stop_event.wait(timeout=10.0)

        # Verify
        assert len(events_received) >= 3
        keys_received = {e.key for e in events_received}
        assert keys_received == {"host", "port", "debug"}

    def test_watch_delete_event(self, etcd_client, etcd_cleanup):
        """Test watching for DELETE events."""
        from varlord.sources.etcd import Etcd

        prefix = "/test/watch/delete/"
        etcd_cleanup(prefix)

        # Setup: Put a key first
        etcd_client.put(f"{prefix}host", "example.com")
        time.sleep(0.2)

        kwargs = get_etcd_source_kwargs()
        kwargs.update(
            {
                "prefix": prefix,
                "watch": True,
                "model": SimpleConfig,
            }
        )
        source = Etcd(**kwargs)

        events_received = []
        stop_event = threading.Event()

        def watch_thread():
            try:
                for event in source.watch():
                    events_received.append(event)
                    if event.event_type == "deleted":
                        stop_event.set()
                        break
            except Exception as e:
                print(f"Watch error: {e}")

        watch_thread_obj = threading.Thread(target=watch_thread, daemon=True)
        watch_thread_obj.start()

        time.sleep(1.0)

        # Trigger DELETE event
        etcd_client.delete(f"{prefix}host")
        time.sleep(0.5)

        stop_event.wait(timeout=10.0)

        # Verify
        assert len(events_received) >= 1
        delete_events = [e for e in events_received if e.event_type == "deleted"]
        assert len(delete_events) >= 1
        assert delete_events[0].key == "host"


class TestConfigStoreWithWatch:
    """Test Config.load_store() with etcd watch support."""

    def test_load_store_with_watch_enabled(self, etcd_client, etcd_cleanup):
        """Test Config.load_store() automatically enables watch."""
        from varlord import Config
        from varlord.sources import Etcd

        prefix = "/test/store/watch/"
        etcd_cleanup(prefix)

        # Setup initial values
        etcd_client.put(f"{prefix}host", "initial.com")
        etcd_client.put(f"{prefix}port", "8000")
        time.sleep(0.2)

        cfg = Config(
            model=SimpleConfig,
            sources=[
                Etcd(**{**get_etcd_source_kwargs(), "prefix": prefix, "watch": True}),
            ],
        )

        store = cfg.load_store()

        # Verify store is watching
        assert store._watch_thread is not None
        assert store._watch_thread.is_alive()

        # Verify initial config
        config = store.get()
        assert config.host == "initial.com"
        assert config.port == 8000

    def test_load_store_without_watch(self, etcd_client, etcd_cleanup):
        """Test Config.load_store() without watch (watch=False)."""
        from varlord import Config
        from varlord.sources import Etcd

        prefix = "/test/store/no-watch/"
        etcd_cleanup(prefix)

        etcd_client.put(f"{prefix}host", "example.com")
        time.sleep(0.2)

        cfg = Config(
            model=SimpleConfig,
            sources=[
                Etcd(**{**get_etcd_source_kwargs(), "prefix": prefix, "watch": False}),
            ],
        )

        store = cfg.load_store()

        # Verify store is NOT watching
        assert store._watch_thread is None or not store._watch_thread.is_alive()

        # But store still works
        config = store.get()
        assert config.host == "example.com"


class TestConfigStoreSubscribe:
    """Test ConfigStore.subscribe() with etcd watch."""

    def test_subscribe_single_callback(self, etcd_client, etcd_cleanup):
        """Test subscribing a single callback."""
        from varlord import Config
        from varlord.sources import Etcd

        prefix = "/test/subscribe/single/"
        etcd_cleanup(prefix)

        # Setup initial values
        etcd_client.put(f"{prefix}host", "initial.com")
        etcd_client.put(f"{prefix}port", "8000")
        time.sleep(0.2)

        cfg = Config(
            model=SimpleConfig,
            sources=[
                Etcd(**{**get_etcd_source_kwargs(), "prefix": prefix, "watch": True}),
            ],
        )

        store = cfg.load_store()

        # Track callbacks
        callbacks_received = []
        callback_lock = threading.Lock()

        def on_change(new_config, diff):
            with callback_lock:
                callbacks_received.append((new_config, diff))

        store.subscribe(on_change)

        # Wait for watch to establish
        time.sleep(1.0)

        # Trigger change
        etcd_client.put(f"{prefix}host", "updated.com")
        time.sleep(1.0)

        # Wait for callback
        max_wait = 10.0
        start_time = time.time()
        while len(callbacks_received) == 0 and (time.time() - start_time) < max_wait:
            time.sleep(0.1)

        # Verify callback was called
        assert len(callbacks_received) >= 1
        new_config, diff = callbacks_received[0]
        assert new_config.host == "updated.com"
        assert "host" in diff.modified

    def test_subscribe_multiple_callbacks(self, etcd_client, etcd_cleanup):
        """Test subscribing multiple callbacks."""
        from varlord import Config
        from varlord.sources import Etcd

        prefix = "/test/subscribe/multiple/"
        etcd_cleanup(prefix)

        etcd_client.put(f"{prefix}host", "initial.com")
        time.sleep(0.2)

        cfg = Config(
            model=SimpleConfig,
            sources=[
                Etcd(**{**get_etcd_source_kwargs(), "prefix": prefix, "watch": True}),
            ],
        )

        store = cfg.load_store()

        callbacks_received = defaultdict(list)
        callback_lock = threading.Lock()

        def callback1(new_config, diff):
            with callback_lock:
                callbacks_received["callback1"].append((new_config, diff))

        def callback2(new_config, diff):
            with callback_lock:
                callbacks_received["callback2"].append((new_config, diff))

        store.subscribe(callback1)
        store.subscribe(callback2)

        time.sleep(1.0)

        # Trigger change
        etcd_client.put(f"{prefix}host", "updated.com")
        time.sleep(1.0)

        # Wait for callbacks
        max_wait = 10.0
        start_time = time.time()
        while (
            len(callbacks_received["callback1"]) == 0 or len(callbacks_received["callback2"]) == 0
        ) and (time.time() - start_time) < max_wait:
            time.sleep(0.1)

        # Verify both callbacks were called
        assert len(callbacks_received["callback1"]) >= 1
        assert len(callbacks_received["callback2"]) >= 1

    def test_subscribe_multiple_changes(self, etcd_client, etcd_cleanup):
        """Test subscribing to multiple configuration changes."""
        from varlord import Config
        from varlord.sources import Etcd

        prefix = "/test/subscribe/multiple-changes/"
        etcd_cleanup(prefix)

        etcd_client.put(f"{prefix}host", "initial.com")
        etcd_client.put(f"{prefix}port", "8000")
        time.sleep(0.2)

        cfg = Config(
            model=SimpleConfig,
            sources=[
                Etcd(**{**get_etcd_source_kwargs(), "prefix": prefix, "watch": True}),
            ],
        )

        store = cfg.load_store()

        callbacks_received = []
        callback_lock = threading.Lock()

        def on_change(new_config, diff):
            with callback_lock:
                callbacks_received.append((new_config, diff))

        store.subscribe(on_change)

        time.sleep(1.0)

        # Trigger multiple changes
        etcd_client.put(f"{prefix}host", "updated1.com")
        time.sleep(0.5)
        etcd_client.put(f"{prefix}port", "9000")
        time.sleep(0.5)
        etcd_client.put(f"{prefix}host", "updated2.com")
        time.sleep(1.0)

        # Wait for callbacks
        max_wait = 10.0
        start_time = time.time()
        while len(callbacks_received) < 3 and (time.time() - start_time) < max_wait:
            time.sleep(0.1)

        # Verify multiple callbacks were called
        assert len(callbacks_received) >= 2  # At least 2 changes

    def test_subscribe_with_added_key(self, etcd_client, etcd_cleanup):
        """Test subscribe callback with added key."""
        from varlord import Config
        from varlord.sources import Etcd

        prefix = "/test/subscribe/added/"
        etcd_cleanup(prefix)

        etcd_client.put(f"{prefix}host", "example.com")
        time.sleep(0.2)

        cfg = Config(
            model=SimpleConfig,
            sources=[
                Etcd(**{**get_etcd_source_kwargs(), "prefix": prefix, "watch": True}),
            ],
        )

        store = cfg.load_store()

        callbacks_received = []
        callback_lock = threading.Lock()

        def on_change(new_config, diff):
            with callback_lock:
                callbacks_received.append((new_config, diff))

        store.subscribe(on_change)

        time.sleep(1.0)

        # Add a new key
        etcd_client.put(f"{prefix}port", "9000")
        time.sleep(1.0)

        # Wait for callback
        max_wait = 10.0
        start_time = time.time()
        while len(callbacks_received) == 0 and (time.time() - start_time) < max_wait:
            time.sleep(0.1)

        # Verify
        assert len(callbacks_received) >= 1
        new_config, diff = callbacks_received[0]
        assert "port" in diff.added or "port" in diff.modified
        assert new_config.port == 9000

    def test_subscribe_with_deleted_key(self, etcd_client, etcd_cleanup):
        """Test subscribe callback with deleted key."""
        from varlord import Config
        from varlord.sources import Etcd

        prefix = "/test/subscribe/deleted/"
        etcd_cleanup(prefix)

        etcd_client.put(f"{prefix}host", "example.com")
        etcd_client.put(f"{prefix}port", "9000")  # Different from default (8000)
        time.sleep(0.2)

        cfg = Config(
            model=SimpleConfig,
            sources=[
                Etcd(**{**get_etcd_source_kwargs(), "prefix": prefix, "watch": True}),
            ],
        )

        store = cfg.load_store()

        # Initial config should have both keys
        initial_config = store.get()
        assert initial_config.host == "example.com"
        assert initial_config.port == 9000  # From etcd

        callbacks_received = []
        callback_lock = threading.Lock()

        def on_change(new_config, diff):
            with callback_lock:
                callbacks_received.append((new_config, diff))

        store.subscribe(on_change)

        time.sleep(1.0)

        # Delete a key (port will change from 9000 to default 8000)
        etcd_client.delete(f"{prefix}port")
        time.sleep(1.0)

        # Wait for callback
        max_wait = 10.0
        start_time = time.time()
        while len(callbacks_received) == 0 and (time.time() - start_time) < max_wait:
            time.sleep(0.1)

        # Verify callback was called (port changed from 9000 to 8000)
        assert len(callbacks_received) >= 1
        new_config, diff = callbacks_received[0]
        # After deletion, port should fall back to default (8000)
        assert new_config.port == 8000  # Default value
        # Port should be in modified (changed from 9000 to 8000)
        assert "port" in diff.modified


class TestMultipleSourcesWithWatch:
    """Test multiple sources with watch support."""

    def test_multiple_etcd_sources_with_watch(self, etcd_client, etcd_cleanup):
        """Test multiple etcd sources with watch enabled."""
        from varlord import Config
        from varlord.sources import Etcd

        prefix1 = "/test/multi/etcd1/"
        prefix2 = "/test/multi/etcd2/"
        etcd_cleanup(prefix1)
        etcd_cleanup(prefix2)

        # Setup initial values
        etcd_client.put(f"{prefix1}host", "etcd1.com")
        etcd_client.put(f"{prefix2}port", "9000")
        time.sleep(0.2)

        cfg = Config(
            model=SimpleConfig,
            sources=[
                Etcd(**{**get_etcd_source_kwargs(), "prefix": prefix1, "watch": True}),
                Etcd(**{**get_etcd_source_kwargs(), "prefix": prefix2, "watch": True}),
            ],
        )

        store = cfg.load_store()

        # Verify store is watching
        assert store._watch_thread is not None
        assert store._watch_thread.is_alive()

        # Verify initial config (prefix2 overrides prefix1 due to priority)
        config = store.get()
        assert config.host == "etcd1.com"  # From prefix1
        assert config.port == 9000  # From prefix2 (overrides default)

        callbacks_received = []
        callback_lock = threading.Lock()

        def on_change(new_config, diff):
            with callback_lock:
                callbacks_received.append((new_config, diff))

        store.subscribe(on_change)

        time.sleep(1.0)

        # Change in prefix2 (should override prefix1)
        etcd_client.put(f"{prefix2}host", "etcd2.com")
        time.sleep(1.0)

        # Wait for callback
        max_wait = 10.0
        start_time = time.time()
        while len(callbacks_received) == 0 and (time.time() - start_time) < max_wait:
            time.sleep(0.1)

        # Verify callback and new config
        assert len(callbacks_received) >= 1
        new_config, diff = callbacks_received[0]
        assert new_config.host == "etcd2.com"  # prefix2 overrides prefix1

    def test_etcd_with_env_source(self, etcd_client, etcd_cleanup, monkeypatch):
        """Test etcd source with env source (etcd has watch, env doesn't)."""
        from varlord import Config
        from varlord.sources import Env, Etcd

        prefix = "/test/multi/etcd-env/"
        etcd_cleanup(prefix)

        etcd_client.put(f"{prefix}host", "etcd.com")
        etcd_client.put(f"{prefix}port", "8000")
        time.sleep(0.2)

        # Set env variable
        monkeypatch.setenv("PORT", "9000")

        cfg = Config(
            model=SimpleConfig,
            sources=[
                Etcd(**{**get_etcd_source_kwargs(), "prefix": prefix, "watch": True}),
                Env(),  # Env overrides etcd
            ],
        )

        store = cfg.load_store()

        # Verify store is watching (because etcd supports watch)
        assert store._watch_thread is not None
        assert store._watch_thread.is_alive()

        # Verify initial config (env overrides etcd)
        config = store.get()
        assert config.host == "etcd.com"  # From etcd
        assert config.port == 9000  # From env (overrides etcd)

        callbacks_received = []
        callback_lock = threading.Lock()

        def on_change(new_config, diff):
            with callback_lock:
                callbacks_received.append((new_config, diff))

        store.subscribe(on_change)

        time.sleep(1.0)

        # Change host in etcd (should trigger callback because host is not overridden by env)
        etcd_client.put(f"{prefix}host", "updated.com")
        time.sleep(1.0)

        # Wait for callback
        max_wait = 10.0
        start_time = time.time()
        while len(callbacks_received) == 0 and (time.time() - start_time) < max_wait:
            time.sleep(0.1)

        # Verify callback was called
        assert len(callbacks_received) >= 1
        new_config, diff = callbacks_received[0]
        assert new_config.host == "updated.com"  # Host changed
        assert new_config.port == 9000  # Port still from env (overrides etcd)
        assert "host" in diff.modified


class TestLoadBehaviorWithWatch:
    """Test load() behavior with watch-enabled sources."""

    def test_load_after_watch_change(self, etcd_client, etcd_cleanup):
        """Test that load() reflects changes made via watch."""
        from varlord import Config
        from varlord.sources import Etcd

        prefix = "/test/load/watch/"
        etcd_cleanup(prefix)

        etcd_client.put(f"{prefix}host", "initial.com")
        time.sleep(0.2)

        cfg = Config(
            model=SimpleConfig,
            sources=[
                Etcd(**{**get_etcd_source_kwargs(), "prefix": prefix, "watch": True}),
            ],
        )

        # Initial load
        config1 = cfg.load()
        assert config1.host == "initial.com"

        # Create store to enable watch (store is used implicitly by watch mechanism)
        _ = cfg.load_store()
        time.sleep(1.0)

        # Change in etcd
        etcd_client.put(f"{prefix}host", "updated.com")
        time.sleep(1.0)

        # Load again - should reflect the change
        config2 = cfg.load()
        assert config2.host == "updated.com"

    def test_load_store_get_consistency(self, etcd_client, etcd_cleanup):
        """Test that store.get() and cfg.load() return consistent values."""
        from varlord import Config
        from varlord.sources import Etcd

        prefix = "/test/consistency/"
        etcd_cleanup(prefix)

        etcd_client.put(f"{prefix}host", "example.com")
        etcd_client.put(f"{prefix}port", "8000")
        time.sleep(0.2)

        cfg = Config(
            model=SimpleConfig,
            sources=[
                Etcd(**{**get_etcd_source_kwargs(), "prefix": prefix, "watch": True}),
            ],
        )

        store = cfg.load_store()

        # Both should return same values
        config_from_load = cfg.load()
        config_from_store = store.get()

        assert config_from_load.host == config_from_store.host
        assert config_from_load.port == config_from_store.port

        # After change, both should still be consistent
        time.sleep(1.0)
        etcd_client.put(f"{prefix}host", "updated.com")
        time.sleep(1.0)

        config_from_load2 = cfg.load()
        config_from_store2 = store.get()

        assert config_from_load2.host == config_from_store2.host
        assert config_from_load2.host == "updated.com"
