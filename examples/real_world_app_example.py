"""
Real-world application example demonstrating Varlord best practices.

This example shows:
- Project structure and file organization
- Configuration models with nested structures
- Configuration setup and initialization
- Using global configuration registry
- Accessing configuration in business code

Project Structure:
    myapp/
    ├── config/
    │   ├── __init__.py
    │   ├── models.py
    │   └── setup.py
    ├── src/
    │   ├── services/
    │   │   └── database.py
    │   └── main.py
    └── config/
        └── app.yaml
"""

from dataclasses import dataclass, field
from pathlib import Path

from varlord import Config, sources
from varlord.global_config import get_global_config, set_global_config

# ============================================================================
# Configuration Models (config/models.py)
# ============================================================================


@dataclass(frozen=True)
class DatabaseConfig:
    """Database configuration."""

    password: str = field(metadata={"description": "Database password"})
    host: str = field(default="localhost", metadata={"description": "Database host"})
    port: int = field(default=5432, metadata={"description": "Database port"})
    name: str = field(default="myapp", metadata={"description": "Database name"})
    user: str = field(default="postgres", metadata={"description": "Database user"})


@dataclass(frozen=True)
class APIConfig:
    """API server configuration."""

    host: str = field(default="0.0.0.0", metadata={"description": "API server host"})
    port: int = field(default=8000, metadata={"description": "API server port"})
    debug: bool = field(default=False, metadata={"description": "Enable debug mode"})


@dataclass(frozen=True)
class AppConfig:
    """Main application configuration."""

    secret_key: str = field(metadata={"description": "Secret key for encryption"})
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    app_name: str = field(default="MyApp", metadata={"description": "Application name"})


# ============================================================================
# Configuration Setup (config/setup.py)
# ============================================================================


def setup_config() -> Config:
    """Initialize and register application configuration.

    This function should be called once at application startup.
    """
    app_dir = Path(__file__).parent

    # Build sources list with priority order
    # Priority: CLI > Env > .env > App Config > Defaults
    config_sources = [
        # Application defaults (lowest priority)
        sources.YAML(str(app_dir / "config" / "app.yaml")),
        # Environment variables (common in containers/CI)
        sources.Env(),
        # Local development .env file
        sources.DotEnv(str(app_dir / ".env")),
        # Command-line arguments (highest priority, for debugging/overrides)
        sources.CLI(),
    ]

    # Create configuration
    cfg = Config(
        model=AppConfig,
        sources=config_sources,
    )

    # Handle CLI commands (--help, --check-variables)
    cfg.handle_cli_commands()

    # Register globally for easy access throughout the application
    set_global_config(cfg, name="app")

    return cfg


def get_config():
    """Get the application configuration (convenience function)."""
    config = get_global_config(name="app")
    return config.load()


# ============================================================================
# Business Code (src/services/database.py)
# ============================================================================


def get_db_connection():
    """Get database connection using global configuration."""
    config = get_global_config(name="app")
    app_config = config.load()

    db = app_config.database
    print(f"Connecting to database: {db.user}@{db.host}:{db.port}/{db.name}")
    # In real code, you would create and return the connection
    return {
        "host": db.host,
        "port": db.port,
        "database": db.name,
        "user": db.user,
        "password": db.password,
    }


# ============================================================================
# Application Entry Point (src/main.py)
# ============================================================================


def main():
    """Main application entry point."""
    import sys

    # Step 1: Initialize configuration (once at startup)
    try:
        setup_config()
        app_config = get_config()
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        print("\n💡 Tips:")
        print("   - Check required fields: python real_world_app_example.py --check-variables")
        print("   - See help: python real_world_app_example.py --help")
        sys.exit(1)

    # Step 2: Validate configuration (optional, but recommended)
    if app_config.api.debug:
        print("⚠️  Warning: Debug mode is enabled!")

    # Step 3: Start your application
    print(f"✅ Starting {app_config.app_name}")
    print(f"   API: http://{app_config.api.host}:{app_config.api.port}")
    print(f"   Database: {app_config.database.host}:{app_config.database.port}")

    # Step 4: Use configuration in business code
    db_conn = get_db_connection()
    print(f"   Database connection: {db_conn}")

    print("\n✅ Application initialized successfully!")
    print("   Configuration is now available globally via get_global_config()")


if __name__ == "__main__":
    main()
