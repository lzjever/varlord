"""
Tests for file-based sources (YAML, JSON, TOML).

Tests cover:
- Basic loading from files
- Nested structure flattening
- Source ID system
- Multiple sources of same type
- Missing file handling
"""

import os
import tempfile
from dataclasses import dataclass, field

from varlord import Config, sources


@dataclass(frozen=True)
class DBConfig:
    """Database configuration."""

    host: str = field(default="localhost", metadata={"description": "Database host"})
    port: int = field(default=5432, metadata={"description": "Database port"})


@dataclass(frozen=True)
class AppConfig:
    """Test configuration model."""

    host: str = field(metadata={"description": "Server host address"})
    port: int = field(metadata={"description": "Server port number"})
    debug: bool = field(metadata={"description": "Enable debug mode"})
    timeout: float = field(metadata={"description": "Request timeout in seconds"})
    api_key: str = field(metadata={"description": "API key for authentication"})
    # Use nested dataclass for nested structure (best practice)
    db: DBConfig = field(
        default_factory=DBConfig, metadata={"description": "Database configuration"}
    )


class TestJSONSource:
    """Tests for JSON source."""

    def test_json_basic_loading(self):
        """Test basic JSON loading."""
        json_content = """{
    "host": "0.0.0.0",
    "port": 8080,
    "debug": true,
    "timeout": 60.0,
    "api_key": "test_json_key",
    "db": {
        "host": "localhost",
        "port": 5432
    }
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_content)
            json_path = f.name

        try:
            json_source = sources.JSON(json_path, model=AppConfig)
            assert json_source.id == f"json:{os.path.abspath(json_path)}"
            assert json_source.name == "json"

            config = json_source.load()
            assert json_source.load_status == "success"
            assert config.get("host") == "0.0.0.0"
            assert config.get("port") == 8080
            assert config.get("db.host") == "localhost"
            assert config.get("db.port") == 5432

            # Test that nested structure works correctly with Config
            cfg = Config(model=AppConfig, sources=[json_source])
            app = cfg.load()
            assert app.db.host == "localhost"
            assert app.db.port == 5432
        finally:
            os.unlink(json_path)

    def test_json_missing_file(self):
        """Test JSON source with missing file."""
        non_existent_json = "/tmp/non_existent_config.json"
        json_source = sources.JSON(non_existent_json, model=AppConfig, required=False)
        config = json_source.load()

        assert json_source.load_status == "not_found"
        assert json_source.load_error is None  # Should not record error for not_found
        assert config == {}

    def test_json_custom_source_id(self):
        """Test JSON source with custom source ID."""
        json_content = '{"host": "0.0.0.0", "port": 8080}'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_content)
            json_path = f.name

        try:
            json_source = sources.JSON(json_path, model=AppConfig, source_id="custom_json")
            assert json_source.id == "custom_json"
        finally:
            os.unlink(json_path)


class TestYAMLSource:
    """Tests for YAML source."""

    def test_yaml_basic_loading(self):
        """Test basic YAML loading."""
        yaml_content = """
host: 0.0.0.0
port: 8080
debug: true
timeout: 60.0
api_key: test_yaml_key
db:
  host: localhost
  port: 5432
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            yaml_source = sources.YAML(yaml_path, model=AppConfig)
            assert yaml_source.id == f"yaml:{os.path.abspath(yaml_path)}"
            assert yaml_source.name == "yaml"

            config = yaml_source.load()
            assert yaml_source.load_status == "success"
            assert config.get("host") == "0.0.0.0"
            assert config.get("port") == 8080
            assert config.get("db.host") == "localhost"
            assert config.get("db.port") == 5432

            # Test that nested structure works correctly with Config
            cfg = Config(model=AppConfig, sources=[yaml_source])
            app = cfg.load()
            assert app.db.host == "localhost"
            assert app.db.port == 5432
        finally:
            os.unlink(yaml_path)

    def test_yaml_missing_file(self):
        """Test YAML source with missing file."""
        non_existent_yaml = "/tmp/non_existent_config.yaml"
        yaml_source = sources.YAML(non_existent_yaml, model=AppConfig, required=False)
        config = yaml_source.load()

        assert yaml_source.load_status == "not_found"
        assert yaml_source.load_error is None
        assert config == {}


class TestTOMLSource:
    """Tests for TOML source."""

    def test_toml_basic_loading(self):
        """Test basic TOML loading."""
        toml_content = """
host = "0.0.0.0"
port = 8080
debug = true
timeout = 60.0
api_key = "test_toml_key"

[db]
host = "localhost"
port = 5432
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            toml_path = f.name

        try:
            toml_source = sources.TOML(toml_path, model=AppConfig)
            assert toml_source.id == f"toml:{os.path.abspath(toml_path)}"
            assert toml_source.name == "toml"

            config = toml_source.load()
            assert toml_source.load_status == "success"
            assert config.get("host") == "0.0.0.0"
            assert config.get("port") == 8080
            assert config.get("db.host") == "localhost"
            assert config.get("db.port") == 5432

            # Test that nested structure works correctly with Config
            cfg = Config(model=AppConfig, sources=[toml_source])
            app = cfg.load()
            assert app.db.host == "localhost"
            assert app.db.port == 5432
        finally:
            os.unlink(toml_path)

    def test_toml_missing_file(self):
        """Test TOML source with missing file."""
        non_existent_toml = "/tmp/non_existent_config.toml"
        toml_source = sources.TOML(non_existent_toml, model=AppConfig, required=False)
        config = toml_source.load()

        assert toml_source.load_status == "not_found"
        assert toml_source.load_error is None
        assert config == {}


class TestMultipleSourcesSameType:
    """Tests for multiple sources of the same type."""

    def test_multiple_yaml_sources(self):
        """Test multiple YAML sources with priority."""
        yaml1_content = """
host: system_host
port: 9000
debug: false
timeout: 30.0
api_key: system_key
"""
        yaml2_content = """
host: user_host
port: 8080
debug: true
timeout: 60.0
api_key: user_key
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix="_system.yaml", delete=False) as f:
            f.write(yaml1_content)
            yaml1_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix="_user.yaml", delete=False) as f:
            f.write(yaml2_content)
            yaml2_path = f.name

        try:
            yaml1 = sources.YAML(yaml1_path, model=AppConfig)
            yaml2 = sources.YAML(yaml2_path, model=AppConfig)

            assert yaml1.id != yaml2.id
            assert yaml1.name == yaml2.name == "yaml"

            # Test with Config - user config should override system config
            cfg = Config(
                model=AppConfig,
                sources=[
                    yaml1,  # System config (lower priority)
                    yaml2,  # User config (higher priority)
                ],
            )

            app = cfg.load()
            assert app.host == "user_host"
            assert app.port == 8080
            assert app.debug is True
        finally:
            os.unlink(yaml1_path)
            os.unlink(yaml2_path)

    def test_multiple_json_sources(self):
        """Test multiple JSON sources with priority."""
        json1_content = """{
    "host": "system_host",
    "port": 9000,
    "debug": false,
    "timeout": 30.0,
    "api_key": "system_key"
}"""
        json2_content = """{
    "host": "user_host",
    "port": 8080,
    "debug": true,
    "timeout": 60.0,
    "api_key": "user_key"
}"""

        with tempfile.NamedTemporaryFile(mode="w", suffix="_system.json", delete=False) as f:
            f.write(json1_content)
            json1_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix="_user.json", delete=False) as f:
            f.write(json2_content)
            json2_path = f.name

        try:
            json1 = sources.JSON(json1_path, model=AppConfig)
            json2 = sources.JSON(json2_path, model=AppConfig)

            assert json1.id != json2.id
            assert json1.name == json2.name == "json"

            cfg = Config(
                model=AppConfig,
                sources=[json1, json2],
            )

            app = cfg.load()
            assert app.host == "user_host"
            assert app.port == 8080
        finally:
            os.unlink(json1_path)
            os.unlink(json2_path)


class TestSourceIDSystem:
    """Tests for source ID system."""

    def test_source_ids_unique(self):
        """Test that source IDs are unique."""
        env_source = sources.Env(model=AppConfig)
        cli_source = sources.CLI(model=AppConfig)

        assert env_source.id == "env"
        assert cli_source.id == "cli"
        assert env_source.id != cli_source.id

    def test_custom_source_id(self):
        """Test custom source ID."""
        custom_env = sources.Env(model=AppConfig, source_id="custom_env")
        assert custom_env.id == "custom_env"

    def test_file_source_id_generation(self):
        """Test file source ID generation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json_path = f.name

        try:
            json_source = sources.JSON(json_path, model=AppConfig)
            expected_id = f"json:{os.path.abspath(json_path)}"
            assert json_source.id == expected_id
        finally:
            os.unlink(json_path)
