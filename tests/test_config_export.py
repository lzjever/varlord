"""
Tests for configuration export functionality.
"""

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from varlord import Config, sources
from varlord.sources.base import Source


@dataclass
class DBConfig:
    """Database configuration."""

    host: str = field(default="localhost")
    port: int = field(default=5432)


@dataclass
class AppConfig:
    """Application configuration."""

    api_key: str = field()
    host: str = field(default="0.0.0.0")
    port: int = field(default=8000)
    debug: bool = field(default=False)
    db: DBConfig = field(default_factory=lambda: DBConfig())


class DictSource(Source):
    """Simple dict-based source for testing."""

    def __init__(self, data: dict, source_id: str = "dict"):
        """Initialize with dictionary data."""
        super().__init__(source_id=source_id)
        self._data = data

    def load(self):
        """Load configuration from dictionary."""
        return self._data

    @property
    def name(self) -> str:
        """Source name."""
        return "dict"


class TestConfigExport:
    """Test configuration export functionality."""

    def test_to_dict(self):
        """Test converting config to dictionary."""
        cfg = Config(
            model=AppConfig,
            sources=[DictSource({"api_key": "test-key"})],
        )

        config_dict = cfg.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["api_key"] == "test-key"
        assert config_dict["host"] == "0.0.0.0"
        assert config_dict["port"] == 8000
        assert isinstance(config_dict["db"], dict)
        assert config_dict["db"]["host"] == "localhost"

    def test_dump_json(self):
        """Test exporting config to JSON."""
        cfg = Config(
            model=AppConfig,
            sources=[DictSource({"api_key": "test-key", "port": 9000})],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            file_path = f.name

        try:
            cfg.dump_json(file_path)
            with open(file_path) as f:
                data = json.load(f)
            assert data["api_key"] == "test-key"
            assert data["port"] == 9000
            assert data["db"]["host"] == "localhost"
        finally:
            Path(file_path).unlink()

    def test_dump_yaml(self):
        """Test exporting config to YAML."""
        pytest.importorskip("yaml")

        cfg = Config(
            model=AppConfig,
            sources=[DictSource({"api_key": "test-key", "port": 9000})],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            file_path = f.name

        try:
            cfg.dump_yaml(file_path)
            import yaml

            with open(file_path) as f:
                data = yaml.safe_load(f)
            assert data["api_key"] == "test-key"
            assert data["port"] == 9000
            assert data["db"]["host"] == "localhost"
        finally:
            Path(file_path).unlink()

    def test_dump_toml(self):
        """Test exporting config to TOML."""
        pytest.importorskip("tomli_w")

        cfg = Config(
            model=AppConfig,
            sources=[DictSource({"api_key": "test-key", "port": 9000})],
        )

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".toml", delete=False) as f:
            file_path = f.name

        try:
            cfg.dump_toml(file_path)
            import tomli_w

            with open(file_path, "rb") as f:
                data = tomli_w.load(f)
            assert data["api_key"] == "test-key"
            assert data["port"] == 9000
            assert data["db"]["host"] == "localhost"
        finally:
            Path(file_path).unlink()

    def test_dump_env(self):
        """Test exporting config to .env file."""
        cfg = Config(
            model=AppConfig,
            sources=[DictSource({"api_key": "test-key", "port": 9000})],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            file_path = f.name

        try:
            cfg.dump_env(file_path, prefix="APP_", uppercase=True)
            with open(file_path) as f:
                content = f.read()

            # Check that keys are present
            assert "APP_API_KEY" in content
            assert "APP_PORT" in content
            assert "APP_DB__HOST" in content  # Nested keys use __ separator

            # Check values
            assert 'APP_API_KEY="test-key"' in content or "APP_API_KEY=test-key" in content
            assert "APP_PORT=9000" in content
            assert "APP_DB__PORT=5432" in content
        finally:
            Path(file_path).unlink()

    def test_dump_env_without_prefix(self):
        """Test exporting config to .env file without prefix."""
        cfg = Config(
            model=AppConfig,
            sources=[DictSource({"api_key": "test-key"})],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            file_path = f.name

        try:
            cfg.dump_env(file_path, prefix="", uppercase=False)
            with open(file_path) as f:
                content = f.read()

            # Check that keys are present without prefix and lowercase
            assert "api_key" in content.lower()
            assert "port" in content.lower()
        finally:
            Path(file_path).unlink()

    def test_export_with_env_source(self):
        """Test export using environment variables as source."""
        # Set environment variables
        os.environ["API_KEY"] = "env-test-key"
        os.environ["PORT"] = "7000"

        try:
            cfg = Config(
                model=AppConfig,
                sources=[sources.Env()],
            )

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                file_path = f.name

            try:
                cfg.dump_json(file_path)
                with open(file_path) as f:
                    data = json.load(f)
                assert data["api_key"] == "env-test-key"
                assert data["port"] == 7000
            finally:
                Path(file_path).unlink()
        finally:
            # Clean up
            os.environ.pop("API_KEY", None)
            os.environ.pop("PORT", None)
