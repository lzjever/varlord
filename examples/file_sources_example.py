"""
Example demonstrating file-based sources (YAML, JSON, TOML).

This example shows:
- Loading configuration from YAML, JSON, and TOML files
- Multiple file sources with priority
- Nested configuration structures
- Missing file handling (graceful degradation)

Run with:
    python file_sources_example.py
    python file_sources_example.py -cv  # Check variables
"""

import os
import tempfile
from dataclasses import dataclass, field

from varlord import Config, sources


@dataclass(frozen=True)
class DBConfig:
    """Database configuration (nested dataclass - best practice)."""

    host: str = field(default="localhost", metadata={"description": "Database host"})
    port: int = field(default=5432, metadata={"description": "Database port"})


@dataclass(frozen=True)
class AppConfig:
    """Application configuration model."""

    host: str = field(default="127.0.0.1", metadata={"description": "Server host address"})
    port: int = field(default=8000, metadata={"description": "Server port number"})
    debug: bool = field(default=False, metadata={"description": "Enable debug mode"})
    api_key: str = field(default="default-key", metadata={"description": "API key"})
    # Use nested dataclass for nested structure (best practice)
    db: DBConfig = field(
        default_factory=DBConfig, metadata={"description": "Database configuration"}
    )


def example_yaml_source():
    """Example: YAML source."""
    print("=== Example 1: YAML Source ===\n")

    yaml_content = """
host: 0.0.0.0
port: 8080
debug: true
api_key: yaml-api-key
db:
  host: db.example.com
  port: 3306
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        cfg = Config(
            model=AppConfig,
            sources=[
                sources.YAML(yaml_path, model=AppConfig),
            ],
        )

        app = cfg.load()
        print("✅ Config loaded from YAML:")
        print(f"   host: {app.host}")
        print(f"   port: {app.port}")
        print(f"   debug: {app.debug}")
        print(f"   db.host: {app.db.host}")
        print(f"   db.port: {app.db.port}")
    finally:
        os.unlink(yaml_path)


def example_json_source():
    """Example: JSON source."""
    print("\n=== Example 2: JSON Source ===\n")

    json_content = """{
    "host": "0.0.0.0",
    "port": 8080,
    "debug": true,
    "api_key": "json-api-key",
    "db": {
        "host": "db.example.com",
        "port": 3306
    }
}
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(json_content)
        json_path = f.name

    try:
        cfg = Config(
            model=AppConfig,
            sources=[
                sources.JSON(json_path, model=AppConfig),
            ],
        )

        app = cfg.load()
        print("✅ Config loaded from JSON:")
        print(f"   host: {app.host}")
        print(f"   port: {app.port}")
        print(f"   debug: {app.debug}")
        print(f"   db.host: {app.db.host}")
        print(f"   db.port: {app.db.port}")
    finally:
        os.unlink(json_path)


def example_toml_source():
    """Example: TOML source."""
    print("\n=== Example 3: TOML Source ===\n")

    toml_content = """
host = "0.0.0.0"
port = 8080
debug = true
api_key = "toml-api-key"

[db]
host = "db.example.com"
port = 3306
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        toml_path = f.name

    try:
        cfg = Config(
            model=AppConfig,
            sources=[
                sources.TOML(toml_path, model=AppConfig),
            ],
        )

        app = cfg.load()
        print("✅ Config loaded from TOML:")
        print(f"   host: {app.host}")
        print(f"   port: {app.port}")
        print(f"   debug: {app.debug}")
        print(f"   db.host: {app.db.host}")
        print(f"   db.port: {app.db.port}")
    finally:
        os.unlink(toml_path)


def example_multiple_file_sources():
    """Example: Multiple file sources with priority."""
    print("\n=== Example 4: Multiple File Sources (Priority) ===\n")

    # System config (lower priority)
    yaml1_content = """
host: system-host
port: 9000
api_key: system-key
"""
    # User config (higher priority)
    yaml2_content = """
host: user-host
port: 8080
debug: true
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix="_system.yaml", delete=False) as f:
        f.write(yaml1_content)
        yaml1_path = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix="_user.yaml", delete=False) as f:
        f.write(yaml2_content)
        yaml2_path = f.name

    try:
        cfg = Config(
            model=AppConfig,
            sources=[
                sources.YAML(yaml1_path, model=AppConfig, source_id="system-config"),
                sources.YAML(yaml2_path, model=AppConfig, source_id="user-config"),
            ],
        )

        app = cfg.load()
        print("✅ Config loaded from multiple YAML files:")
        print(f"   host: {app.host} (from user-config, overrides system-config)")
        print(f"   port: {app.port} (from user-config)")
        print(f"   debug: {app.debug} (from user-config)")
        print(f"   api_key: {app.api_key[:10]}... (from system-config)")
    finally:
        os.unlink(yaml1_path)
        os.unlink(yaml2_path)


def example_missing_file():
    """Example: Missing file handling (graceful degradation)."""
    print("\n=== Example 5: Missing File (Graceful Degradation) ===\n")

    # Try to load from a non-existent file
    non_existent_yaml = "/tmp/non_existent_config.yaml"

    cfg = Config(
        model=AppConfig,
        sources=[
            sources.YAML(non_existent_yaml, model=AppConfig, required=False),
            sources.Env(),  # Fallback to env vars
        ],
    )

    # Set some env vars as fallback
    os.environ["HOST"] = "env-host"
    os.environ["PORT"] = "7777"

    app = cfg.load()
    print("✅ Config loaded (missing file handled gracefully):")
    print(f"   host: {app.host} (from env, file not found)")
    print(f"   port: {app.port} (from env)")
    print("   Note: Missing file shows as 'Not Available' in -cv output")


def main():
    """Main function."""
    example_yaml_source()
    example_json_source()
    example_toml_source()
    example_multiple_file_sources()
    example_missing_file()

    print("\n💡 Tip: Run with -cv to see detailed source information and status")
    print("   Example: python file_sources_example.py -cv")


if __name__ == "__main__":
    main()
