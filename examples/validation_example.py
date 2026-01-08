"""
Example demonstrating configuration validation.

This example shows how to use validators to ensure configuration values
meet your requirements.

Run with:
    python validation_example.py
    python validation_example.py --port 99999  # Will fail validation
    python validation_example.py -cv  # Check variables
"""

import os
import sys
from dataclasses import dataclass, field

from varlord import Config, sources
from varlord.validators import ValidationError, validate_range, validate_regex

# Set environment variables for testing
os.environ["APP_PORT"] = "9000"
os.environ["APP_HOST"] = "0.0.0.0"


@dataclass(frozen=True)
class AppConfig:
    """Application configuration with validation."""

    host: str = field(default="127.0.0.1", metadata={"description": "Server host address"})
    port: int = field(default=8000, metadata={"description": "Server port number"})

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate port range
        validate_range(self.port, min=1, max=65535)
        # Validate host format (simple IP check)
        validate_regex(self.host, r"^\d+\.\d+\.\d+\.\d+$")


def main():
    """Main function."""
    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Env(),  # Model defaults applied automatically, model auto-injected
            sources.CLI(),  # CLI arguments can override env vars
        ],
    )

    # Handle CLI commands
    cfg.handle_cli_commands()

    try:
        app = cfg.load()
        print("✅ Configuration loaded and validated successfully!")
        print(f"   Host: {app.host}")
        print(f"   Port: {app.port}")
    except ValidationError as e:
        print(f"❌ Validation error: {e.key} = {e.value}")
        print(f"   {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
