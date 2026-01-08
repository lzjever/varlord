"""
Example demonstrating global configuration registry.

This example shows how to use the global configuration feature to avoid
passing configuration objects around your application.

Run with:
    python global_config_example.py --api-key your_key
"""

from dataclasses import dataclass, field

from varlord import Config, sources
from varlord.global_config import get_global_config, set_global_config


@dataclass(frozen=True)
class AppConfig:
    """Application configuration model."""

    api_key: str = field(metadata={"description": "API key for authentication"})
    host: str = field(default="127.0.0.1", metadata={"description": "Server host address"})
    port: int = field(default=8000, metadata={"description": "Server port number"})
    debug: bool = field(default=False, metadata={"description": "Enable debug mode"})


def initialize_app():
    """Initialize application configuration (called once at startup)."""
    # Create and configure
    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Env(),
            sources.CLI(),
        ],
    )

    # Register globally - now available everywhere
    set_global_config(cfg)

    # Handle CLI commands
    cfg.handle_cli_commands()

    print("✅ Application configuration initialized")


def some_function_in_your_app():
    """Example: Any function in your application can access config."""
    # Get the global config (no need to pass it as parameter)
    config = get_global_config()

    # Load configuration
    app = config.load()

    return app


def another_function():
    """Another example function."""
    config = get_global_config()
    app = config.load()

    print(f"Function 2: Server running on {app.host}:{app.port}")


def main():
    """Main application entry point."""
    # Step 1: Initialize configuration (once at startup)
    initialize_app()

    # Step 2: Use configuration anywhere in your app
    app_config = some_function_in_your_app()
    print(f"Function 1: API key = {app_config.api_key[:10]}...")
    print(f"Function 1: Debug mode = {app_config.debug}")

    another_function()

    print("\n✅ All functions accessed configuration without passing it around!")


if __name__ == "__main__":
    main()
