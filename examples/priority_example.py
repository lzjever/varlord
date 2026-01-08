"""
Example demonstrating priority ordering.

Shows three ways to customize priority:
1. Reorder sources (recommended - simplest)
2. Use PriorityPolicy for per-key rules
3. Multiple sources of the same type with custom IDs

Run with:
    python priority_example.py
    python priority_example.py --host 0.0.0.0 --port 9999
"""

import os
import tempfile
from dataclasses import dataclass, field

from varlord import Config, PriorityPolicy, sources

# Set environment variables for testing
os.environ["HOST"] = "env-host"
os.environ["PORT"] = "8888"
os.environ["API_KEY"] = "env-api-key"


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


def example_1_reorder_sources():
    """Method 1: Reorder sources (recommended - simplest)."""
    print("=== Example 1: Reorder Sources ===")
    print("Priority: defaults < env < cli (later sources override earlier ones)\n")

    # Priority is determined by sources order: later sources override earlier ones
    # Model defaults are automatically applied first (lowest priority)
    # Model is auto-injected to all sources by Config
    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Env(),  # Overrides defaults - model auto-injected
            sources.CLI(),  # Highest priority (last) - model auto-injected
        ],
    )

    app = cfg.load()
    print("✅ Config loaded:")
    print(f"   host: {app.host} (from {'CLI' if '--host' in str(cfg._sources) else 'env'})")
    print(f"   port: {app.port}")
    print(f"   api_key: {app.api_key[:10]}...")


def example_2_priority_policy():
    """Method 2: Use PriorityPolicy (advanced: per-key rules)."""
    print("\n=== Example 2: PriorityPolicy ===")
    print("Custom priority: api_key and db.* only from defaults and env (CLI ignored)\n")

    # Use when you need different priority rules for different keys
    # Model is auto-injected to all sources by Config
    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Env(),  # Model defaults applied automatically, model auto-injected
            sources.CLI(),  # Model auto-injected
        ],
        policy=PriorityPolicy(
            default=["defaults", "env", "cli"],  # Default: all sources in order
            overrides={
                "api_key": ["defaults", "env"],  # API key: env can override, but not CLI
                "db.host": ["defaults", "env"],  # DB host: env can override, but not CLI
                "db.port": ["defaults", "env"],  # DB port: env can override, but not CLI
            },
        ),
    )

    app = cfg.load()
    print("✅ Config loaded:")
    print(f"   host: {app.host} (CLI can override)")
    print(f"   api_key: {app.api_key[:10]}... (CLI cannot override)")
    print(f"   db.host: {app.db.host} (CLI cannot override)")


def example_3_multiple_sources_same_type():
    """Method 3: Multiple sources of the same type."""
    print("\n=== Example 3: Multiple Sources of Same Type ===")
    print("System config (lower priority) + User config (higher priority)\n")

    # Create two YAML files
    yaml1_content = """
host: system-host
port: 9000
api_key: system-key
"""
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
        # Create two YAML sources with different IDs
        yaml1 = sources.YAML(yaml1_path, model=AppConfig, source_id="system-config")
        yaml2 = sources.YAML(yaml2_path, model=AppConfig, source_id="user-config")

        cfg = Config(
            model=AppConfig,
            sources=[
                yaml1,  # System config (lower priority)
                yaml2,  # User config (higher priority - overrides system)
            ],
        )

        app = cfg.load()
        print("✅ Config loaded:")
        print(f"   host: {app.host} (from user-config, overrides system-config)")
        print(f"   port: {app.port} (from user-config)")
        print(f"   debug: {app.debug} (from user-config)")
        print(
            f"   api_key: {app.api_key[:10]}... (from system-config, user-config doesn't have it)"
        )
    finally:
        import os

        os.unlink(yaml1_path)
        os.unlink(yaml2_path)


def main():
    """Main function."""
    example_1_reorder_sources()
    example_2_priority_policy()
    example_3_multiple_sources_same_type()


if __name__ == "__main__":
    main()
