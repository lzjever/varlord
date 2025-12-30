"""
Basic example of using Varlord.

This example demonstrates the most common use case:
loading configuration from defaults, environment variables, and CLI arguments.
"""

from dataclasses import dataclass
from varlord import Config, sources


@dataclass(frozen=True)
class AppConfig:
    """Application configuration model."""

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    timeout: float = 30.0


def main():
    """Main function."""
    # Create config with multiple sources
    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Defaults(model=AppConfig),  # Baseline defaults
            sources.Env(prefix="APP_"),  # Environment variables (APP_HOST, APP_PORT, etc.)
            sources.CLI(model=AppConfig),  # Command-line arguments (--host, --port, etc.)
        ],
    )

    # Load configuration
    app = cfg.load()

    # Use configuration
    print(f"Starting server on {app.host}:{app.port}")
    print(f"Debug mode: {app.debug}")
    print(f"Timeout: {app.timeout}s")


if __name__ == "__main__":
    main()
