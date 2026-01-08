"""
Basic example of using Varlord.

This example demonstrates the most common use case:
loading configuration from defaults, environment variables, and CLI arguments.

Run with:
    python basic_example.py --api-key your_key
    python basic_example.py -cv  # Check variables
    python basic_example.py --help  # Show help
"""

from dataclasses import dataclass, field
from typing import Optional

from varlord import Config, sources
from varlord.model_validation import RequiredFieldError


@dataclass(frozen=True)
class AppConfig:
    """Application configuration model."""

    # Required field (no default value)
    api_key: str = field(metadata={"description": "API key for authentication"})

    # Optional fields (with default values)
    host: str = field(default="127.0.0.1", metadata={"description": "Server host address"})
    port: int = field(default=8000, metadata={"description": "Server port number"})
    debug: bool = field(default=False, metadata={"description": "Enable debug mode"})
    timeout: float = field(default=30.0, metadata={"description": "Request timeout in seconds"})
    hello_message: Optional[str] = field(
        default=None, metadata={"description": "Optional greeting message"}
    )


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

    # Handle CLI commands (--help, -cv, etc.)
    cfg.handle_cli_commands()

    # Load configuration
    # Note: api_key is required and must be provided via environment variable or CLI argument
    # Example: export API_KEY=your_key or python basic_example.py --api-key your_key
    try:
        app = cfg.load()
    except RequiredFieldError as e:
        # Show friendly error message with field descriptions
        print(f"Error loading configuration:\n{e}")
        print("\nTip: Provide required fields via:")
        print("  - Environment variable: export API_KEY=your_key")
        print("  - CLI argument: python basic_example.py --api-key your_key")
        print("  - For help: python basic_example.py --help")
        return
    except Exception as e:
        print(f"Unexpected error: {e}")
        return

    # Use configuration
    print(f"Starting server on {app.host}:{app.port}")
    print(f"Debug mode: {app.debug}")
    print(f"Timeout: {app.timeout}s")
    if app.hello_message:
        print(f"Message: {app.hello_message}")


if __name__ == "__main__":
    main()
