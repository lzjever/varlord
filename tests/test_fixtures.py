"""Tests for test fixtures functionality."""

from pathlib import Path


def test_datadir_fixture_exists(datadir):
    """Test that datadir fixture points to correct location."""
    assert datadir.exists()
    assert datadir.name == "fixtures"
    assert (datadir / "yaml").exists()
    assert (datadir / "json").exists()
    assert (datadir / "toml").exists()
    assert (datadir / "env").exists()


def test_yaml_datadir_fixture(yaml_datadir):
    """Test that yaml_datadir fixture points to YAML fixtures."""
    assert yaml_datadir.exists()
    assert yaml_datadir.name == "yaml"
    assert (yaml_datadir / "config_valid.yaml").exists()
    assert (yaml_datadir / "config_invalid_syntax.yaml").exists()
    assert (yaml_datadir / "config_nested.yaml").exists()


def test_json_datadir_fixture(json_datadir):
    """Test that json_datadir fixture points to JSON fixtures."""
    assert json_datadir.exists()
    assert json_datadir.name == "json"
    assert (json_datadir / "config_valid.json").exists()


def test_toml_datadir_fixture(toml_datadir):
    """Test that toml_datadir fixture points to TOML fixtures."""
    assert toml_datadir.exists()
    assert toml_datadir.name == "toml"
    assert (toml_datadir / "config_valid.toml").exists()


def test_env_datadir_fixture(env_datadir):
    """Test that env_datadir fixture points to ENV fixtures."""
    assert env_datadir.exists()
    assert env_datadir.name == "env"
    assert (env_datadir / "test_config.env").exists()


def test_yaml_fixture_content(yaml_datadir):
    """Test that YAML fixtures contain expected content."""
    yaml_file = yaml_datadir / "config_valid.yaml"
    content = yaml_file.read_text()

    assert "database:" in content
    assert "host: localhost" in content
    assert "port: 5432" in content


def test_json_fixture_content(json_datadir):
    """Test that JSON fixtures contain expected content."""
    json_file = json_datadir / "config_valid.json"
    content = json_file.read_text()

    assert '"database"' in content
    assert '"host": "localhost"' in content
    assert '"port": 5432' in content


def test_env_fixture_content(env_datadir):
    """Test that ENV fixtures contain expected content."""
    env_file = env_datadir / "test_config.env"
    content = env_file.read_text()

    assert "DATABASE_HOST=localhost" in content
    assert "DATABASE_PORT=5432" in content


def test_yaml_load_from_fixture(yaml_datadir):
    """Test loading YAML configuration from fixture."""
    from varlord.sources import YAML

    yaml_file = yaml_datadir / "config_valid.yaml"
    source = YAML(str(yaml_file))

    result = source.load()

    assert result["database.host"] == "localhost"
    assert result["database.port"] == 5432
    assert result["server.host"] == "0.0.0.0"
    assert result["server.port"] == 8000


def test_json_load_from_fixture(json_datadir):
    """Test loading JSON configuration from fixture."""
    from varlord.sources import JSON

    json_file = json_datadir / "config_valid.json"
    source = JSON(str(json_file))

    result = source.load()

    assert result["database.host"] == "localhost"
    assert result["database.port"] == 5432
    assert result["server.host"] == "0.0.0.0"
    assert result["server.port"] == 8000
