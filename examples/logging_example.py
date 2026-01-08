"""
Example demonstrating logging and diagnostic features.

This example shows:
- How to enable debug logging
- How to use check-variables to inspect configuration
- Source status tracking

Run with:
    python logging_example.py
    python logging_example.py -cv  # Check variables with detailed info
"""

import logging
import os
from dataclasses import dataclass, field

from varlord import Config, set_log_level, sources

# Enable debug logging to see configuration loading details
# This shows merge operations, source loads, etc.
set_log_level(logging.DEBUG)

# Set some environment variables for demonstration
os.environ["HOST"] = "0.0.0.0"
os.environ["PORT"] = "9000"


@dataclass(frozen=True)
class AppConfig:
    """Application configuration model."""

    host: str = field(default="127.0.0.1", metadata={"description": "Server host address"})
    port: int = field(default=8000, metadata={"description": "Server port number"})
    debug: bool = field(default=False, metadata={"description": "Enable debug mode"})


def main():
    """Main function."""
    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Env(),  # Model defaults applied automatically, model auto-injected
            sources.CLI(),  # CLI arguments can override env vars
        ],
    )

    # Handle CLI commands (including -cv for check-variables)
    cfg.handle_cli_commands()

    # Load configuration
    # With DEBUG logging enabled, you'll see detailed logs about:
    # - Source loading
    # - Configuration merging
    # - Value overrides
    app = cfg.load()

    print("\n✅ Configuration loaded successfully!")
    print(f"   Host: {app.host}")
    print(f"   Port: {app.port}")
    print(f"   Debug: {app.debug}")
    print("\n💡 Tip: Run with -cv to see detailed source information and status")


if __name__ == "__main__":
    main()
