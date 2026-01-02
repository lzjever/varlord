"""
Integration tests for etcd source.

These tests require a running etcd instance with TLS authentication.
They are separated from core unit tests and should be run explicitly.

To run these tests:
    pytest tests/test_sources_etcd_integration.py -m etcd

To skip these tests:
    pytest -m "not etcd"
"""

import os
import time
import threading
import warnings
from dataclasses import dataclass, field
from typing import Optional

import pytest

# Suppress etcd3 deprecation warnings from protobuf
warnings.filterwarnings("ignore", category=DeprecationWarning, module="etcd3")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="etcd3.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="etcd3.etcdrpc.*")

# Skip all tests in this file if etcd3 is not installed
try:
    import etcd3
except ImportError:
    etcd3 = None
    pytestmark = pytest.mark.skip(reason="etcd3 not installed")
else:
    # Mark all tests in this file as etcd integration tests
    pytestmark = [pytest.mark.etcd, pytest.mark.integration]


# Etcd connection configuration
# These can be overridden via environment variables
ETCD_HOST = os.environ.get("ETCD_HOST", "127.0.0.1")
ETCD_PORT = int(os.environ.get("ETCD_PORT", "2379"))
ETCD_CA_CERT = os.environ.get("ETCD_CA_CERT", "./cert/AgentsmithLocal.cert.pem")
ETCD_CERT_KEY = os.environ.get("ETCD_CERT_KEY", "./cert/etcd-client-lzj-local/key.pem")
ETCD_CERT_CERT = os.environ.get("ETCD_CERT_CERT", "./cert/etcd-client-lzj-local/cert.pem")


def get_etcd_client():
    """Get a direct etcd client for test setup/teardown."""
    client_kwargs = {
        "host": ETCD_HOST,
        "port": ETCD_PORT,
    }

    # Add TLS certificates if they exist
    if os.path.exists(ETCD_CA_CERT):
        client_kwargs["ca_cert"] = ETCD_CA_CERT
    if os.path.exists(ETCD_CERT_KEY):
        client_kwargs["cert_key"] = ETCD_CERT_KEY
    if os.path.exists(ETCD_CERT_CERT):
        client_kwargs["cert_cert"] = ETCD_CERT_CERT

    return etcd3.client(**client_kwargs)


@pytest.fixture
def etcd_client():
    """Fixture providing a direct etcd client for test setup."""
    # Check if certificates exist
    missing_certs = []
    if not os.path.exists(ETCD_CA_CERT):
        missing_certs.append(f"CA cert: {ETCD_CA_CERT}")
    if not os.path.exists(ETCD_CERT_KEY):
        missing_certs.append(f"Client key: {ETCD_CERT_KEY}")
    if not os.path.exists(ETCD_CERT_CERT):
        missing_certs.append(f"Client cert: {ETCD_CERT_CERT}")

    if missing_certs:
        pytest.skip(
            f"Etcd certificates not found. Missing: {', '.join(missing_certs)}. "
            f"Please set ETCD_CA_CERT, ETCD_CERT_KEY, and ETCD_CERT_CERT environment variables."
        )

    client = get_etcd_client()
    try:
        # Test connection
        client.get("/test")
    except Exception as e:
        pytest.skip(f"Cannot connect to etcd at {ETCD_HOST}:{ETCD_PORT}: {e}")
    yield client


@pytest.fixture
def etcd_cleanup(etcd_client):
    """Fixture to clean up etcd keys after tests."""
    keys_to_cleanup = []

    def _add_key(key: str):
        keys_to_cleanup.append(key)

    yield _add_key

    # Cleanup
    for key in keys_to_cleanup:
        try:
            etcd_client.delete(key)
        except Exception:
            pass


@dataclass(frozen=True)
class SampleAppConfig:
    """Test configuration model."""

    host: str = field()
    port: int = field(default=8000)
    debug: bool = field(default=False)
    timeout: Optional[float] = field(default=None)


@dataclass(frozen=True)
class DBConfig:
    """Nested database configuration."""

    host: str = field()
    port: int = field(default=5432)


@dataclass(frozen=True)
class NestedTestConfig:
    """Test configuration with nested fields."""

    db: DBConfig = field()
    api_key: str = field(default="")


class TestEtcdSourceBasic:
    """Test basic etcd source functionality."""

    def test_etcd_source_creation(self):
        """Test creating etcd source with TLS."""
        from varlord.sources.etcd import Etcd

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix="/test/",
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        assert source.name == "etcd"
        assert source._host == ETCD_HOST
        assert source._port == ETCD_PORT
        assert source._prefix == "/test/"

    def test_etcd_source_load_empty(self, etcd_client, etcd_cleanup):
        """Test loading from empty etcd."""
        from varlord.sources.etcd import Etcd

        prefix = "/test/empty/"
        etcd_cleanup(prefix)

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix=prefix,
            model=SampleAppConfig,
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        result = source.load()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_etcd_source_load_simple(self, etcd_client, etcd_cleanup):
        """Test loading simple key-value pairs."""
        from varlord.sources.etcd import Etcd

        prefix = "/test/simple/"
        etcd_cleanup(prefix)

        # Setup: Put some keys
        etcd_client.put(f"{prefix}host", "example.com")
        etcd_client.put(f"{prefix}port", "9000")
        etcd_client.put(f"{prefix}debug", "true")

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix=prefix,
            model=SampleAppConfig,
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        result = source.load()

        assert "host" in result
        assert result["host"] == "example.com"
        assert "port" in result
        # Note: etcd source tries to parse JSON, so "9000" becomes 9000 (int)
        assert result["port"] in ("9000", 9000)
        assert "debug" in result
        assert result["debug"] in ("true", True)

    def test_etcd_source_load_with_nested_keys(self, etcd_client, etcd_cleanup):
        """Test loading with nested keys (using double underscore)."""
        from varlord.sources.etcd import Etcd

        prefix = "/test/nested/"
        etcd_cleanup(prefix)

        # Setup: Put nested keys using double underscore (normalized to db.host, db.port)
        etcd_client.put(f"{prefix}db__host", "db.example.com")
        etcd_client.put(f"{prefix}db__port", "5432")
        etcd_client.put(f"{prefix}api_key", "secret123")

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix=prefix,
            model=NestedTestConfig,
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        result = source.load()

        assert "db.host" in result
        assert result["db.host"] == "db.example.com"
        assert "db.port" in result
        # Note: etcd source tries to parse JSON, so "5432" becomes 5432 (int)
        assert result["db.port"] in ("5432", 5432)
        assert "api_key" in result
        assert result["api_key"] == "secret123"

    def test_etcd_source_load_with_slash_separator(self, etcd_client, etcd_cleanup):
        """Test loading with slash separator (converted to double underscore)."""
        from varlord.sources.etcd import Etcd

        prefix = "/test/slash/"
        etcd_cleanup(prefix)

        # Setup: Put keys with slash separator (converted to __ then normalized to db.host, db.port)
        etcd_client.put(f"{prefix}db/host", "db.example.com")
        etcd_client.put(f"{prefix}db/port", "5432")

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix=prefix,
            model=NestedTestConfig,
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        result = source.load()

        assert "db.host" in result
        assert result["db.host"] == "db.example.com"
        assert "db.port" in result
        # Note: etcd source tries to parse JSON, so "5432" becomes 5432 (int)
        assert result["db.port"] in ("5432", 5432)

    def test_etcd_source_load_json_values(self, etcd_client, etcd_cleanup):
        """Test loading JSON values (should be parsed)."""
        from varlord.sources.etcd import Etcd
        import json

        prefix = "/test/json/"
        etcd_cleanup(prefix)

        # Setup: Put JSON values
        etcd_client.put(f"{prefix}host", "example.com")
        etcd_client.put(f"{prefix}config", json.dumps({"timeout": 30, "retries": 3}))

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix=prefix,
            model=SampleAppConfig,
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        result = source.load()

        assert "host" in result
        assert result["host"] == "example.com"
        # Note: config is not in SampleAppConfig model, so it won't be loaded

    def test_etcd_source_prefix_filtering(self, etcd_client, etcd_cleanup):
        """Test that prefix filtering works correctly."""
        from varlord.sources.etcd import Etcd

        prefix = "/test/prefix/"
        other_prefix = "/test/other/"
        etcd_cleanup(prefix)
        etcd_cleanup(other_prefix)

        # Setup: Put keys in different prefixes
        etcd_client.put(f"{prefix}host", "example.com")
        etcd_client.put(f"{other_prefix}host", "other.com")

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix=prefix,
            model=SampleAppConfig,
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        result = source.load()

        assert "host" in result
        assert result["host"] == "example.com"
        # Should not include keys from other prefix

    def test_etcd_source_model_filtering(self, etcd_client, etcd_cleanup):
        """Test that only model fields are loaded."""
        from varlord.sources.etcd import Etcd

        prefix = "/test/model/"
        etcd_cleanup(prefix)

        # Setup: Put keys, some matching model, some not
        etcd_client.put(f"{prefix}host", "example.com")
        etcd_client.put(f"{prefix}port", "9000")
        etcd_client.put(f"{prefix}unknown_field", "value")
        etcd_client.put(f"{prefix}another_unknown", "value2")

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix=prefix,
            model=SampleAppConfig,
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        result = source.load()

        assert "host" in result
        assert "port" in result
        assert "unknown_field" not in result
        assert "another_unknown" not in result


class TestEtcdSourceWatch:
    """Test etcd source watch functionality."""

    def test_etcd_source_watch_enabled(self):
        """Test that watch can be enabled."""
        from varlord.sources.etcd import Etcd

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix="/test/",
            watch=True,
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        assert source.supports_watch() is True

    def test_etcd_source_watch_disabled(self):
        """Test that watch is disabled by default."""
        from varlord.sources.etcd import Etcd

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix="/test/",
            watch=False,
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        assert source.supports_watch() is False

    def test_etcd_source_watch_put_event(self, etcd_client, etcd_cleanup):
        """Test watching for PUT events (add/modify)."""
        from varlord.sources.etcd import Etcd
        from varlord.sources.base import ChangeEvent

        prefix = "/test/watch/put/"
        etcd_cleanup(prefix)

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix=prefix,
            watch=True,
            model=SampleAppConfig,
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        events_received = []
        stop_watching = threading.Event()

        def watch_thread():
            try:
                for event in source.watch():
                    events_received.append(event)
                    if len(events_received) >= 2:
                        stop_watching.set()
                        break
            except Exception as e:
                print(f"Watch error: {e}")

        # Start watching in background
        watch_thread_obj = threading.Thread(target=watch_thread, daemon=True)
        watch_thread_obj.start()

        # Wait a bit for watch to start (watch needs time to establish connection)
        time.sleep(1.0)

        # Trigger events
        etcd_client.put(f"{prefix}host", "example.com")
        time.sleep(0.5)
        etcd_client.put(f"{prefix}port", "9000")
        time.sleep(0.5)

        # Wait for events (give more time for watch to process)
        stop_watching.wait(timeout=10.0)

        # Verify events
        assert len(events_received) >= 1
        event = events_received[0]
        assert isinstance(event, ChangeEvent)
        assert event.key in ["host", "port"]
        assert event.event_type in ["added", "modified"]

    def test_etcd_source_watch_delete_event(self, etcd_client, etcd_cleanup):
        """Test watching for DELETE events."""
        from varlord.sources.etcd import Etcd
        from varlord.sources.base import ChangeEvent

        prefix = "/test/watch/delete/"
        etcd_cleanup(prefix)

        # Setup: Put a key first
        etcd_client.put(f"{prefix}host", "example.com")
        time.sleep(0.2)

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix=prefix,
            watch=True,
            model=SampleAppConfig,
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        events_received = []
        stop_watching = threading.Event()

        def watch_thread():
            try:
                for event in source.watch():
                    events_received.append(event)
                    if event.event_type == "deleted":
                        stop_watching.set()
                        break
            except Exception as e:
                print(f"Watch error: {e}")

        # Start watching in background
        watch_thread_obj = threading.Thread(target=watch_thread, daemon=True)
        watch_thread_obj.start()

        # Wait a bit for watch to start (watch needs time to establish connection)
        time.sleep(1.0)

        # Delete the key
        etcd_client.delete(f"{prefix}host")
        time.sleep(0.5)

        # Wait for event (give more time for watch to process)
        stop_watching.wait(timeout=10.0)

        # Verify event
        assert len(events_received) >= 1
        delete_events = [e for e in events_received if e.event_type == "deleted"]
        assert len(delete_events) >= 1
        event = delete_events[0]
        assert isinstance(event, ChangeEvent)
        assert event.key == "host"
        assert event.event_type == "deleted"
        assert event.new_value is None


class TestEtcdSourceIntegration:
    """Test etcd source integration with Config."""

    def test_etcd_source_with_config(self, etcd_client, etcd_cleanup):
        """Test using etcd source with Config class."""
        from varlord import Config
        from varlord.sources import Etcd

        prefix = "/test/config/"
        etcd_cleanup(prefix)

        # Setup: Put configuration
        etcd_client.put(f"{prefix}host", "example.com")
        etcd_client.put(f"{prefix}port", "9000")
        etcd_client.put(f"{prefix}debug", "true")

        cfg = Config(
            model=SampleAppConfig,
            sources=[
                Etcd(
                    host=ETCD_HOST,
                    port=ETCD_PORT,
                    prefix=prefix,
                    ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
                    cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
                    cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
                )
            ],
        )

        app = cfg.load()

        assert app.host == "example.com"
        assert app.port == 9000
        assert app.debug is True

    def test_etcd_source_priority(self, etcd_client, etcd_cleanup):
        """Test etcd source priority with other sources."""
        from varlord import Config
        from varlord.sources import Etcd, Env

        prefix = "/test/priority/"
        etcd_cleanup(prefix)

        # Setup: Put in etcd
        etcd_client.put(f"{prefix}host", "etcd.example.com")
        etcd_client.put(f"{prefix}port", "9000")

        # Set environment variable
        os.environ["HOST"] = "env.example.com"

        try:
            cfg = Config(
                model=SampleAppConfig,
                sources=[
                    Etcd(
                        host=ETCD_HOST,
                        port=ETCD_PORT,
                        prefix=prefix,
                        ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
                        cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
                        cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
                    ),
                    Env(),
                ],
            )

            app = cfg.load()

            # Env should override etcd (later sources override earlier)
            assert app.host == "env.example.com"
            assert app.port == 9000  # From etcd (env doesn't have PORT)
        finally:
            os.environ.pop("HOST", None)


class TestEtcdSourceErrorHandling:
    """Test etcd source error handling."""

    def test_etcd_source_invalid_host(self):
        """Test behavior with invalid host."""
        from varlord.sources.etcd import Etcd

        source = Etcd(
            host="invalid.host.example.com",
            port=2379,
            prefix="/test/",
            model=SampleAppConfig,
            timeout=1,  # Short timeout
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        # Should return empty dict on error (fail-safe)
        result = source.load()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_etcd_source_invalid_certificates(self):
        """Test behavior with invalid certificates."""
        from varlord.sources.etcd import Etcd

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix="/test/",
            model=SampleAppConfig,
            timeout=1,
            ca_cert="/nonexistent/ca.cert.pem",
            cert_key="/nonexistent/key.pem",
            cert_cert="/nonexistent/cert.pem",
        )

        # Should return empty dict on error (fail-safe)
        result = source.load()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_etcd_source_no_model(self):
        """Test that etcd source requires model."""
        from varlord.sources.etcd import Etcd

        source = Etcd(
            host=ETCD_HOST,
            port=ETCD_PORT,
            prefix="/test/",
            # model not provided
            ca_cert=ETCD_CA_CERT if os.path.exists(ETCD_CA_CERT) else None,
            cert_key=ETCD_CERT_KEY if os.path.exists(ETCD_CERT_KEY) else None,
            cert_cert=ETCD_CERT_CERT if os.path.exists(ETCD_CERT_CERT) else None,
        )

        with pytest.raises(ValueError, match="Etcd source requires model"):
            source.load()


class TestEtcdSourceFromEnv:
    """Test etcd source creation from environment variables."""

    def test_etcd_source_from_env_basic(self, monkeypatch):
        """Test creating etcd source from environment variables."""
        from varlord.sources.etcd import Etcd

        monkeypatch.setenv("ETCD_HOST", "192.168.0.220")
        monkeypatch.setenv("ETCD_PORT", "2379")
        monkeypatch.setenv("ETCD_PREFIX", "/test/")

        source = Etcd.from_env()

        assert source._host == "192.168.0.220"
        assert source._port == 2379
        assert source._prefix == "/test/"

    def test_etcd_source_from_env_with_tls(self, monkeypatch):
        """Test creating etcd source from env with TLS certificates."""
        from varlord.sources.etcd import Etcd

        monkeypatch.setenv("ETCD_HOST", "192.168.0.220")
        monkeypatch.setenv("ETCD_PORT", "2379")
        monkeypatch.setenv("ETCD_CA_CERT", "./cert/AgentsmithLocal.cert.pem")
        monkeypatch.setenv("ETCD_CERT_KEY", "./cert/etcd-client-lzj-local/key.pem")
        monkeypatch.setenv("ETCD_CERT_CERT", "./cert/etcd-client-lzj-local/cert.pem")

        source = Etcd.from_env()

        assert source._host == "192.168.0.220"
        assert source._ca_cert == "./cert/AgentsmithLocal.cert.pem"
        assert source._cert_key == "./cert/etcd-client-lzj-local/key.pem"
        assert source._cert_cert == "./cert/etcd-client-lzj-local/cert.pem"

    def test_etcd_source_from_env_with_watch(self, monkeypatch):
        """Test creating etcd source from env with watch enabled."""
        from varlord.sources.etcd import Etcd

        monkeypatch.setenv("ETCD_HOST", "127.0.0.1")
        monkeypatch.setenv("ETCD_WATCH", "true")

        source = Etcd.from_env()

        assert source._watch is True

    def test_etcd_source_from_env_override_params(self, monkeypatch):
        """Test that parameters override environment variables."""
        from varlord.sources.etcd import Etcd

        monkeypatch.setenv("ETCD_HOST", "127.0.0.1")
        monkeypatch.setenv("ETCD_PORT", "2379")
        monkeypatch.setenv("ETCD_PREFIX", "/env/")
        monkeypatch.setenv("ETCD_WATCH", "true")

        source = Etcd.from_env(prefix="/override/", watch=False)

        assert source._host == "127.0.0.1"  # From env
        assert source._port == 2379  # From env
        assert source._prefix == "/override/"  # Overridden
        assert source._watch is False  # Overridden
