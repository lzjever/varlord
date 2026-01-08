"""
Tests for tutorial examples.

These tests verify that all code examples in the tutorial documentation
work correctly.
"""

import pytest

# ============================================================================
# Tutorial: Getting Started
# ============================================================================


def test_getting_started_basic():
    """Test basic example from getting_started.rst."""
    from dataclasses import dataclass, field

    from varlord import Config

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="127.0.0.1",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821
        debug: bool = field(
            default=False,
        )  # noqa: F821
        app_name: str = field(
            default="MyApp",
        )  # noqa: F821

    cfg = Config(
        model=AppConfig,
        sources=[],
    )

    app = cfg.load()
    assert app.app_name == "MyApp"
    assert app.host == "127.0.0.1"
    assert app.port == 8000
    assert app.debug is False


def test_getting_started_access():
    """Test accessing configuration values."""
    from dataclasses import dataclass, field

    from varlord import Config

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="127.0.0.1",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821

    cfg = Config(
        model=AppConfig,
        sources=[],
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
    from dataclasses import dataclass, field

    from varlord import Config, sources

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="127.0.0.1",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821
        debug: bool = field(
            default=False,
        )  # noqa: F821

    try:
        os.environ["HOST"] = "0.0.0.0"
        os.environ["PORT"] = "9000"

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Env(model=AppConfig),
            ],
        )

        app = cfg.load()
        assert app.host == "0.0.0.0"  # From env
        assert app.port == 9000  # From env
        assert app.debug is False  # From defaults
    finally:
        os.environ.pop("HOST", None)
        os.environ.pop("PORT", None)


def test_multiple_sources_cli():
    """Test CLI arguments from multiple_sources.rst."""
    import sys
    from dataclasses import dataclass, field

    from varlord import Config, sources

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="127.0.0.1",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821
        debug: bool = field(
            default=False,
        )  # noqa: F821

    original_argv = sys.argv[:]
    try:
        sys.argv = ["app.py", "--host", "192.168.1.1", "--port", "8080", "--debug"]

        cfg = Config(
            model=AppConfig,
            sources=[
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
    from dataclasses import dataclass, field

    from varlord import Config

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="127.0.0.1",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821

    try:
        os.environ["HOST"] = "0.0.0.0"
        os.environ["PORT"] = "9000"

        cfg = Config.from_model(
            model=AppConfig,
            cli=False,
        )

        app = cfg.load()
        assert app.host == "0.0.0.0"
        assert app.port == 9000
    finally:
        os.environ.pop("PORT", None)
        os.environ.pop("HOST", None)


# ============================================================================
# Tutorial: Nested Configuration
# ============================================================================


def test_nested_configuration_basic():
    """Test basic nested configuration."""
    from dataclasses import dataclass, field

    from varlord import Config

    @dataclass(frozen=True)  # noqa: F821
    class DBConfig:
        host: str = field(
            default="localhost",
        )  # noqa: F821
        port: int = field(
            default=5432,
        )  # noqa: F821
        database: str = field(
            default="mydb",
        )  # noqa: F821

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="0.0.0.0",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821
        db: DBConfig = field(
            default_factory=lambda: DBConfig(),
        )  # noqa: F821

    cfg = Config(
        model=AppConfig,
        sources=[],
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

    @dataclass(frozen=True)  # noqa: F821
    class DBConfig:
        host: str = field(
            default="localhost",
        )  # noqa: F821
        port: int = field(
            default=5432,
        )  # noqa: F821
        database: str = field(
            default="mydb",
        )  # noqa: F821

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="0.0.0.0",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821
        db: DBConfig = field(
            default_factory=lambda: DBConfig(),
        )  # noqa: F821

    try:
        os.environ["DB__HOST"] = "db.example.com"
        os.environ["DB__PORT"] = "3306"
        os.environ["DB__DATABASE"] = "production"

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Env(model=AppConfig),
            ],
        )

        app = cfg.load()
        assert app.db.host == "db.example.com"
        assert app.db.port == 3306
        assert app.db.database == "production"
    finally:
        os.environ.pop("PORT", None)
        os.environ.pop("PORT", None)
        os.environ.pop("PORT", None)


def test_nested_configuration_cli():
    """Test nested configuration from CLI arguments."""
    import sys
    from dataclasses import dataclass, field

    from varlord import Config, sources

    @dataclass(frozen=True)  # noqa: F821
    class DBConfig:
        host: str = field(
            default="localhost",
        )  # noqa: F821
        port: int = field(
            default=5432,
        )  # noqa: F821

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="0.0.0.0",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821
        db: DBConfig = field(
            default_factory=lambda: DBConfig(),
        )  # noqa: F821

    original_argv = sys.argv[:]
    try:
        sys.argv = ["app.py", "--db-host", "db.example.com", "--db-port", "3306"]

        cfg = Config(
            model=AppConfig,
            sources=[
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

    @dataclass(frozen=True)  # noqa: F821
    class CacheConfig:
        enabled: bool = field(
            default=False,
        )  # noqa: F821
        ttl: int = field(
            default=3600,
        )  # noqa: F821

    @dataclass(frozen=True)  # noqa: F821
    class DBConfig:
        host: str = field(
            default="localhost",
        )  # noqa: F821
        port: int = field(
            default=5432,
        )  # noqa: F821
        cache: CacheConfig = field(  # noqa: F821
            default_factory=lambda: CacheConfig(),
        )

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="0.0.0.0",
        )  # noqa: F821
        db: DBConfig = field(
            default_factory=lambda: DBConfig(),
        )  # noqa: F821

    try:
        os.environ["DB__CACHE__ENABLED"] = "true"
        os.environ["DB__CACHE__TTL"] = "7200"

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Env(model=AppConfig),
            ],
        )

        app = cfg.load()
        assert app.db.cache.enabled is True
        assert app.db.cache.ttl == 7200
    finally:
        os.environ.pop("PORT", None)
        os.environ.pop("PORT", None)


# ============================================================================
# Tutorial: Validation
# ============================================================================


def test_validation_basic():
    """Test basic validation from validation.rst."""
    from dataclasses import dataclass, field

    from varlord import Config
    from varlord.validators import validate_not_empty, validate_port

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="0.0.0.0",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821

        def __post_init__(self):
            validate_not_empty(self.host)
            validate_port(self.port)

    cfg = Config(
        model=AppConfig,
        sources=[],
    )

    app = cfg.load()
    assert app.host == "0.0.0.0"
    assert app.port == 8000


def test_validation_multiple_sources():
    """Test validation with multiple sources."""
    import os
    from dataclasses import dataclass, field

    from varlord import Config, sources
    from varlord.validators import ValidationError, validate_port

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        port: int = field(
            default=8000,
        )  # noqa: F821

        def __post_init__(self):
            validate_port(self.port)

    try:
        os.environ["PORT"] = "70000"  # Invalid

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Env(model=AppConfig),
            ],
        )

        with pytest.raises(ValidationError):
            cfg.load()
    finally:
        os.environ.pop("PORT", None)


def test_validation_nested():
    """Test validation with nested configuration."""
    from dataclasses import dataclass, field

    from varlord import Config
    from varlord.validators import validate_not_empty, validate_port

    @dataclass(frozen=True)  # noqa: F821
    class DBConfig:
        host: str = field(
            default="localhost",
        )  # noqa: F821
        port: int = field(
            default=5432,
        )  # noqa: F821

        def __post_init__(self):
            validate_not_empty(self.host)
            validate_port(self.port)

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="0.0.0.0",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821
        db: DBConfig = field(
            default_factory=lambda: DBConfig(),
        )  # noqa: F821

        def __post_init__(self):
            validate_port(self.port)

    cfg = Config(
        model=AppConfig,
        sources=[],
    )

    app = cfg.load()
    assert app.port == 8000
    assert app.db.port == 5432


def test_validation_cross_field():
    """Test cross-field validation."""
    from dataclasses import dataclass, field

    from varlord import Config
    from varlord.validators import ValidationError, validate_port

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        app_port: int = field(
            default=8000,
        )  # noqa: F821
        db_port: int = field(  # noqa: F821
            default=8000,
        )  # Same as app_port - will conflict!

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
        sources=[],
    )

    with pytest.raises(ValidationError):
        cfg.load()


# ============================================================================
# Tutorial: Dynamic Updates
# ============================================================================


def test_dynamic_updates_basic():
    """Test basic ConfigStore usage."""
    from dataclasses import dataclass, field

    from varlord import Config

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="0.0.0.0",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821

    cfg = Config(
        model=AppConfig,
        sources=[],
    )

    store = cfg.load_store()
    app = store.get()
    assert app.host == "0.0.0.0"
    assert app.port == 8000


def test_dynamic_updates_manual_reload():
    """Test manual reload."""
    import os
    from dataclasses import dataclass, field

    from varlord import Config, sources

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        port: int = field(
            default=8000,
        )  # noqa: F821

    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Env(model=AppConfig),
        ],
    )

    store = cfg.load_store()
    assert store.get().port == 8000

    try:
        os.environ["PORT"] = "9000"
        store.reload()
        assert store.get().port == 9000
    finally:
        os.environ.pop("PORT", None)


def test_dynamic_updates_subscribe():
    """Test subscribing to configuration changes."""
    import os
    from dataclasses import dataclass, field

    from varlord import Config, sources

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        port: int = field(
            default=8000,
        )  # noqa: F821

    changes = []

    def on_config_change(new_config, diff):
        changes.append((new_config, diff))

    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Env(model=AppConfig),
        ],
    )

    store = cfg.load_store()
    store.subscribe(on_config_change)

    try:
        os.environ["PORT"] = "9000"
        store.reload()
        assert len(changes) == 1
        assert changes[0][0].port == 9000
        assert "port" in changes[0][1].modified
    finally:
        os.environ.pop("PORT", None)


# ============================================================================
# Tutorial: Advanced Features
# ============================================================================


def test_advanced_priority_policy():
    """Test PriorityPolicy from advanced_features.rst."""
    import os
    from dataclasses import dataclass, field

    from varlord import Config, PriorityPolicy, sources

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="0.0.0.0",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821
        api_key: str = field(
            default="default-key",
        )  # noqa: F821

    try:
        os.environ["HOST"] = "env-host"
        os.environ["PORT"] = "9000"
        os.environ["API_KEY"] = "env-key"

        policy = PriorityPolicy(
            default=["defaults", "env"],
            overrides={
                "api_key": ["env", "defaults"],  # Defaults override env for api_key
            },
        )

        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Env(model=AppConfig),
            ],
            policy=policy,
        )

        app = cfg.load()
        assert app.host == "env-host"
        assert app.port == 9000
        assert app.api_key == "default-key"  # Defaults override env per policy
    finally:
        os.environ.pop("PORT", None)
        os.environ.pop("PORT", None)
        os.environ.pop("PORT", None)


def test_advanced_custom_source():
    """Test custom source from advanced_features.rst."""
    import json
    import os
    import tempfile
    from dataclasses import dataclass, field
    from typing import Any, Mapping

    from varlord import Config
    from varlord.sources.base import Source

    class JSONFileSource(Source):
        """Source that loads configuration from a JSON file."""

        def __init__(self, file_path: str, source_id: str = None):
            super().__init__(source_id=source_id or f"json_file:{os.path.abspath(file_path)}")
            self._file_path = file_path

        @property
        def name(self) -> str:
            return "json_file"

        def load(self) -> Mapping[str, Any]:
            """Load configuration from JSON file."""
            try:
                with open(self._file_path) as f:
                    data = json.load(f)
                    return {k.lower(): v for k, v in data.items()}
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

    @dataclass(frozen=True)  # noqa: F821
    class AppConfig:
        host: str = field(
            default="0.0.0.0",
        )  # noqa: F821
        port: int = field(
            default=8000,
        )  # noqa: F821

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"host": "json-host", "port": 7000}, f)
        json_path = f.name

    try:
        cfg = Config(
            model=AppConfig,
            sources=[
                JSONFileSource(json_path),
            ],
        )

        app = cfg.load()
        assert app.host == "json-host"
        assert app.port == 7000
    finally:
        os.unlink(json_path)
