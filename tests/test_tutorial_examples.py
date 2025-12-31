"""
Tests for tutorial examples.

These tests verify that all code examples in the tutorial documentation
work correctly.
"""

import pytest
import os
import sys
import tempfile
import json
from dataclasses import dataclass, field
from varlord import Config, sources, PriorityPolicy
from varlord.validators import (
    validate_port,
    validate_not_empty,
    validate_email,
    validate_url,
    validate_length,
    validate_range,
    ValidationError,
)


# ============================================================================
# Tutorial: Getting Started
# ============================================================================


def test_getting_started_basic():
    """Test basic example from getting_started.rst."""
    from dataclasses import dataclass
    from varlord import Config, sources

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "127.0.0.1"
        port: int = 8000
        debug: bool = False
        app_name: str = "MyApp"

    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Defaults(model=AppConfig),
        ],
    )

    app = cfg.load()
    assert app.app_name == "MyApp"
    assert app.host == "127.0.0.1"
    assert app.port == 8000
    assert app.debug is False


def test_getting_started_access():
    """Test accessing configuration values."""
    from dataclasses import dataclass
    from varlord import Config, sources

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "127.0.0.1"
        port: int = 8000

    cfg = Config(
        model=AppConfig,
        sources=[sources.Defaults(model=AppConfig)],
    )

    app = cfg.load()
    assert app.host == "127.0.0.1"
    assert app.port == 8000


# ============================================================================
# Tutorial: Multiple Sources
# ============================================================================


def test_multiple_sources_priority():
    """Test source priority from multiple_sources.rst."""
    import os
    from dataclasses import dataclass
    from varlord import Config, sources

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "127.0.0.1"
        port: int = 8000
        debug: bool = False

    try:
        os.environ["APP_HOST"] = "0.0.0.0"
        os.environ["APP_PORT"] = "9000"

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.Env(prefix="APP_"),
            ],
        )

        app = cfg.load()
        assert app.host == "0.0.0.0"  # From env
        assert app.port == 9000  # From env
        assert app.debug is False  # From defaults
    finally:
        os.environ.pop("APP_HOST", None)
        os.environ.pop("APP_PORT", None)


def test_multiple_sources_cli():
    """Test CLI arguments from multiple_sources.rst."""
    import sys
    from dataclasses import dataclass
    from varlord import Config, sources

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "127.0.0.1"
        port: int = 8000
        debug: bool = False

    original_argv = sys.argv[:]
    try:
        sys.argv = ["app.py", "--host", "192.168.1.1", "--port", "8080", "--debug"]

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.CLI(model=AppConfig),
            ],
        )

        app = cfg.load()
        assert app.host == "192.168.1.1"
        assert app.port == 8080
        assert app.debug is True
    finally:
        sys.argv = original_argv


def test_multiple_sources_from_model():
    """Test Config.from_model convenience method."""
    import os
    from dataclasses import dataclass
    from varlord import Config

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "127.0.0.1"
        port: int = 8000

    try:
        os.environ["APP_HOST"] = "0.0.0.0"
        os.environ["APP_PORT"] = "9000"

        cfg = Config.from_model(
            model=AppConfig,
            env_prefix="APP_",
            cli=False,
        )

        app = cfg.load()
        assert app.host == "0.0.0.0"
        assert app.port == 9000
    finally:
        os.environ.pop("APP_HOST", None)
        os.environ.pop("APP_PORT", None)


# ============================================================================
# Tutorial: Nested Configuration
# ============================================================================


def test_nested_configuration_basic():
    """Test basic nested configuration."""
    from dataclasses import dataclass, field
    from varlord import Config, sources

    @dataclass(frozen=True)
    class DBConfig:
        host: str = "localhost"
        port: int = 5432
        database: str = "mydb"

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "0.0.0.0"
        port: int = 8000
        db: DBConfig = field(default_factory=lambda: DBConfig())

    cfg = Config(
        model=AppConfig,
        sources=[sources.Defaults(model=AppConfig)],
    )

    app = cfg.load()
    assert app.db is not None
    assert app.db.host == "localhost"
    assert app.db.port == 5432


def test_nested_configuration_env():
    """Test nested configuration from environment variables."""
    import os
    from dataclasses import dataclass, field
    from varlord import Config, sources

    @dataclass(frozen=True)
    class DBConfig:
        host: str = "localhost"
        port: int = 5432
        database: str = "mydb"

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "0.0.0.0"
        port: int = 8000
        db: DBConfig = field(default_factory=lambda: DBConfig())

    try:
        os.environ["APP_DB__HOST"] = "db.example.com"
        os.environ["APP_DB__PORT"] = "3306"
        os.environ["APP_DB__DATABASE"] = "production"

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.Env(prefix="APP_"),
            ],
        )

        app = cfg.load()
        assert app.db.host == "db.example.com"
        assert app.db.port == 3306
        assert app.db.database == "production"
    finally:
        os.environ.pop("APP_DB__HOST", None)
        os.environ.pop("APP_DB__PORT", None)
        os.environ.pop("APP_DB__DATABASE", None)


def test_nested_configuration_cli():
    """Test nested configuration from CLI arguments."""
    import sys
    from dataclasses import dataclass, field
    from varlord import Config, sources

    @dataclass(frozen=True)
    class DBConfig:
        host: str = "localhost"
        port: int = 5432

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "0.0.0.0"
        port: int = 8000
        db: DBConfig = field(default_factory=lambda: DBConfig())

    original_argv = sys.argv[:]
    try:
        sys.argv = ["app.py", "--db-host", "db.example.com", "--db-port", "3306"]

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.CLI(model=AppConfig),
            ],
        )

        app = cfg.load()
        assert app.db.host == "db.example.com"
        assert app.db.port == 3306
    finally:
        sys.argv = original_argv


def test_nested_configuration_deep():
    """Test deeply nested configuration."""
    import os
    from dataclasses import dataclass, field
    from varlord import Config, sources

    @dataclass(frozen=True)
    class CacheConfig:
        enabled: bool = False
        ttl: int = 3600

    @dataclass(frozen=True)
    class DBConfig:
        host: str = "localhost"
        port: int = 5432
        cache: CacheConfig = field(default_factory=lambda: CacheConfig())

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "0.0.0.0"
        db: DBConfig = field(default_factory=lambda: DBConfig())

    try:
        os.environ["APP_DB__CACHE__ENABLED"] = "true"
        os.environ["APP_DB__CACHE__TTL"] = "7200"

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.Env(prefix="APP_"),
            ],
        )

        app = cfg.load()
        assert app.db.cache.enabled is True
        assert app.db.cache.ttl == 7200
    finally:
        os.environ.pop("APP_DB__CACHE__ENABLED", None)
        os.environ.pop("APP_DB__CACHE__TTL", None)


# ============================================================================
# Tutorial: Validation
# ============================================================================


def test_validation_basic():
    """Test basic validation from validation.rst."""
    from dataclasses import dataclass
    from varlord import Config, sources
    from varlord.validators import validate_port, validate_not_empty

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "0.0.0.0"
        port: int = 8000

        def __post_init__(self):
            validate_not_empty(self.host)
            validate_port(self.port)

    cfg = Config(
        model=AppConfig,
        sources=[sources.Defaults(model=AppConfig)],
    )

    app = cfg.load()
    assert app.host == "0.0.0.0"
    assert app.port == 8000


def test_validation_multiple_sources():
    """Test validation with multiple sources."""
    import os
    from dataclasses import dataclass
    from varlord import Config, sources
    from varlord.validators import validate_port, ValidationError

    @dataclass(frozen=True)
    class AppConfig:
        port: int = 8000

        def __post_init__(self):
            validate_port(self.port)

    try:
        os.environ["APP_PORT"] = "70000"  # Invalid

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.Env(prefix="APP_"),
            ],
        )

        with pytest.raises(ValidationError):
            cfg.load()
    finally:
        os.environ.pop("APP_PORT", None)


def test_validation_nested():
    """Test validation with nested configuration."""
    from dataclasses import dataclass, field
    from varlord import Config, sources
    from varlord.validators import validate_port, validate_not_empty

    @dataclass(frozen=True)
    class DBConfig:
        host: str = "localhost"
        port: int = 5432

        def __post_init__(self):
            validate_not_empty(self.host)
            validate_port(self.port)

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "0.0.0.0"
        port: int = 8000
        db: DBConfig = field(default_factory=lambda: DBConfig())

        def __post_init__(self):
            validate_port(self.port)

    cfg = Config(
        model=AppConfig,
        sources=[sources.Defaults(model=AppConfig)],
    )

    app = cfg.load()
    assert app.port == 8000
    assert app.db.port == 5432


def test_validation_cross_field():
    """Test cross-field validation."""
    from dataclasses import dataclass
    from varlord import Config, sources
    from varlord.validators import validate_port, ValidationError

    @dataclass(frozen=True)
    class AppConfig:
        app_port: int = 8000
        db_port: int = 8000  # Same as app_port - will conflict!

        def __post_init__(self):
            validate_port(self.app_port)
            validate_port(self.db_port)

            if self.app_port == self.db_port:
                raise ValidationError(
                    "app_port",
                    self.app_port,
                    f"App port conflicts with DB port {self.db_port}",
                )

    cfg = Config(
        model=AppConfig,
        sources=[sources.Defaults(model=AppConfig)],
    )

    with pytest.raises(ValidationError):
        cfg.load()


# ============================================================================
# Tutorial: Dynamic Updates
# ============================================================================


def test_dynamic_updates_basic():
    """Test basic ConfigStore usage."""
    from dataclasses import dataclass
    from varlord import Config, sources

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "0.0.0.0"
        port: int = 8000

    cfg = Config(
        model=AppConfig,
        sources=[sources.Defaults(model=AppConfig)],
    )

    store = cfg.load_store()
    app = store.get()
    assert app.host == "0.0.0.0"
    assert app.port == 8000
    assert store.host == "0.0.0.0"
    assert store.port == 8000


def test_dynamic_updates_manual_reload():
    """Test manual reload."""
    import os
    from dataclasses import dataclass
    from varlord import Config, sources

    @dataclass(frozen=True)
    class AppConfig:
        port: int = 8000

    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Defaults(model=AppConfig),
            sources.Env(prefix="APP_"),
        ],
    )

    store = cfg.load_store()
    assert store.port == 8000

    try:
        os.environ["APP_PORT"] = "9000"
        store.reload()
        assert store.port == 9000
    finally:
        os.environ.pop("APP_PORT", None)


def test_dynamic_updates_subscribe():
    """Test subscribing to configuration changes."""
    import os
    from dataclasses import dataclass
    from varlord import Config, sources

    @dataclass(frozen=True)
    class AppConfig:
        port: int = 8000

    changes = []

    def on_config_change(new_config, diff):
        changes.append((new_config, diff))

    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Defaults(model=AppConfig),
            sources.Env(prefix="APP_"),
        ],
    )

    store = cfg.load_store()
    store.subscribe(on_config_change)

    try:
        os.environ["APP_PORT"] = "9000"
        store.reload()
        assert len(changes) == 1
        assert changes[0][0].port == 9000
        assert "port" in changes[0][1].modified
    finally:
        os.environ.pop("APP_PORT", None)


# ============================================================================
# Tutorial: Advanced Features
# ============================================================================


def test_advanced_priority_policy():
    """Test PriorityPolicy from advanced_features.rst."""
    import os
    from dataclasses import dataclass
    from varlord import Config, sources, PriorityPolicy

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "0.0.0.0"
        port: int = 8000
        api_key: str = "default-key"

    try:
        os.environ["APP_HOST"] = "env-host"
        os.environ["APP_PORT"] = "9000"
        os.environ["APP_API_KEY"] = "env-key"

        policy = PriorityPolicy(
            default=["defaults", "env"],
            overrides={
                "api_key": ["env", "defaults"],  # Defaults override env for api_key
            },
        )

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.Env(prefix="APP_"),
            ],
            policy=policy,
        )

        app = cfg.load()
        assert app.host == "env-host"
        assert app.port == 9000
        assert app.api_key == "default-key"  # Defaults override env per policy
    finally:
        os.environ.pop("APP_HOST", None)
        os.environ.pop("APP_PORT", None)
        os.environ.pop("APP_API_KEY", None)


def test_advanced_custom_source():
    """Test custom source from advanced_features.rst."""
    import json
    import tempfile
    import os
    from typing import Mapping, Any
    from dataclasses import dataclass
    from varlord import Config
    from varlord.sources.base import Source

    class JSONFileSource(Source):
        """Source that loads configuration from a JSON file."""

        def __init__(self, file_path: str):
            self._file_path = file_path

        @property
        def name(self) -> str:
            return "json_file"

        def load(self) -> Mapping[str, Any]:
            """Load configuration from JSON file."""
            try:
                with open(self._file_path, "r") as f:
                    data = json.load(f)
                    return {k.lower(): v for k, v in data.items()}
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "0.0.0.0"
        port: int = 8000

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"host": "json-host", "port": 7000}, f)
        json_path = f.name

    try:
        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                JSONFileSource(json_path),
            ],
        )

        app = cfg.load()
        assert app.host == "json-host"
        assert app.port == 7000
    finally:
        os.unlink(json_path)
