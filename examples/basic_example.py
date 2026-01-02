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
    # Model defaults are automatically applied - no need for sources.Defaults
    # Sources filter by model fields automatically - model is auto-injected by Config
    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Env(),  # Environment variables (HOST, PORT, etc.) - model auto-injected
            sources.CLI(),  # Command-line arguments (--host, --port, etc.) - model auto-injected
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
