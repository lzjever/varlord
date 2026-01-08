"""
Tests for DotEnv source.
"""

import os
import tempfile
from dataclasses import dataclass, field

import pytest

# Mark all tests in this file as requiring dotenv
# Tests will be automatically deselected if python-dotenv is not installed (via conftest.py)
try:
    from varlord.sources.dotenv import DotEnv
except ImportError:
    DotEnv = None  # type: ignore

# DotEnv is now a core dependency, no longer requires integration marker


@dataclass
class DotEnvTestConfig:
    api_key: str = field()
    host: str = field(
        default="localhost",
    )
    port: int = field(
        default=8000,
    )


def test_dotenv_basic():
    """Test basic DotEnv loading."""
    # DotEnv availability is checked by conftest.py, but we need runtime check here
    if DotEnv is None:
        pytest.skip("python-dotenv not installed")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("HOST=0.0.0.0\n")
        f.write("PORT=9000\n")
        env_file = f.name

    try:
        source = DotEnv(dotenv_path=env_file, model=DotEnvTestConfig)
        config = source.load()

        assert config["host"] == "0.0.0.0"
        assert config["port"] == "9000"  # DotEnv returns strings
    finally:
        os.unlink(env_file)


def test_dotenv_model_filtering():
    """Test that DotEnv only loads model fields."""
    if DotEnv is None:
        pytest.skip("python-dotenv not installed")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("HOST=0.0.0.0\n")
        f.write("UNRELATED_VAR=value\n")
        env_file = f.name

    try:
        source = DotEnv(dotenv_path=env_file, model=DotEnvTestConfig)
        config = source.load()

        assert "host" in config
        assert "unrelated_var" not in config  # Filtered out
    finally:
        os.unlink(env_file)


def test_dotenv_nested_keys():
    """Test DotEnv with nested keys."""

    @dataclass
    class DBConfig:
        host: str = field()
        port: int = field(
            default=5432,
        )

    @dataclass
    class AppConfig:
        db: DBConfig = field()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("DB__HOST=localhost\n")
        f.write("DB__PORT=5432\n")
        env_file = f.name

    try:
        if DotEnv is None:
            pytest.skip("python-dotenv not installed")
        source = DotEnv(dotenv_path=env_file, model=AppConfig)
        config = source.load()

        assert config["db.host"] == "localhost"
        assert config["db.port"] == "5432"
    finally:
        os.unlink(env_file)


def test_dotenv_name():
    """Test source name."""
    if DotEnv is None:
        pytest.skip("python-dotenv not installed")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("HOST=0.0.0.0\n")
        env_file = f.name

    try:
        source = DotEnv(dotenv_path=env_file, model=DotEnvTestConfig)
        assert source.name == "dotenv"
    finally:
        os.unlink(env_file)


def test_dotenv_no_model_error():
    """Test that DotEnv raises error without model."""
    if DotEnv is None:
        pytest.skip("python-dotenv not installed")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("HOST=0.0.0.0\n")
        env_file = f.name

    try:
        source = DotEnv(dotenv_path=env_file)

        with pytest.raises(ValueError) as exc_info:
            source.load()

        assert "model" in str(exc_info.value).lower()
    finally:
        os.unlink(env_file)


def test_dotenv_missing_file():
    """Test DotEnv with missing file."""
    if DotEnv is None:
        pytest.skip("python-dotenv not installed")
    source = DotEnv(dotenv_path="/nonexistent/file.env", model=DotEnvTestConfig)
    config = source.load()

    # Should return empty dict if file doesn't exist
    assert config == {}


def test_dotenv_empty_file():
    """Test DotEnv with empty file."""
    if DotEnv is None:
        pytest.skip("python-dotenv not installed")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        env_file = f.name

    try:
        source = DotEnv(dotenv_path=env_file, model=DotEnvTestConfig)
        config = source.load()

        assert config == {}
    finally:
        os.unlink(env_file)
