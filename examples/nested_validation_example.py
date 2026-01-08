"""
Example demonstrating validation with nested configuration.

This example shows:
- Nested dataclass structures (best practice)
- Validation at multiple levels
- Cross-field validation

Run with:
    python nested_validation_example.py
    python nested_validation_example.py -cv  # Check variables
"""

import os
import sys
from dataclasses import dataclass, field

from varlord import Config, sources
from varlord.validators import ValidationError, validate_not_empty, validate_range, validate_regex

# Set environment variables for testing
os.environ["DB__HOST"] = "localhost"
os.environ["DB__PORT"] = "5432"
os.environ["API__TIMEOUT"] = "30"


@dataclass(frozen=True)
class DBConfig:
    """Database configuration."""

    host: str = field(default="127.0.0.1", metadata={"description": "Database host"})
    port: int = field(default=5432, metadata={"description": "Database port"})
    max_connections: int = field(default=10, metadata={"description": "Maximum connections"})

    def __post_init__(self):
        """Validate database configuration."""
        validate_not_empty(self.host)
        validate_range(self.port, min=1, max=65535)
        validate_range(self.max_connections, min=1, max=100)


@dataclass(frozen=True)
class APIConfig:
    """API configuration."""

    timeout: int = field(default=30, metadata={"description": "Request timeout in seconds"})
    retries: int = field(default=3, metadata={"description": "Number of retries"})
    base_url: str = field(
        default="https://api.example.com", metadata={"description": "API base URL"}
    )

    def __post_init__(self):
        """Validate API configuration."""
        validate_range(self.timeout, min=1, max=300)
        validate_range(self.retries, min=0, max=10)
        validate_regex(self.base_url, r"^https?://.+")


@dataclass(frozen=True)
class AppConfig:
    """Application configuration with nested structures."""

    host: str = field(default="0.0.0.0", metadata={"description": "Server host address"})
    port: int = field(default=8000, metadata={"description": "Server port number"})
    # Use default_factory for nested dataclasses (best practice)
    db: DBConfig = field(
        default_factory=DBConfig, metadata={"description": "Database configuration"}
    )
    api: APIConfig = field(default_factory=APIConfig, metadata={"description": "API configuration"})

    def __post_init__(self):
        """Validate application configuration."""
        # Validate flat fields
        validate_not_empty(self.host)
        validate_range(self.port, min=1, max=65535)

        # Nested dataclasses are automatically validated when they are created
        # DBConfig's __post_init__ and APIConfig's __post_init__ are called automatically
        # No need to manually validate self.db or self.api here

        # Cross-field validation example
        # Validate that API timeout is reasonable compared to DB connection pool
        if self.db is not None and self.api is not None:
            if self.api.timeout > self.db.max_connections * 10:
                raise ValidationError(
                    "api.timeout",
                    self.api.timeout,
                    f"API timeout ({self.api.timeout}s) is too large compared to DB max_connections ({self.db.max_connections})",
                )


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
        print(f"   Host: {app.host}:{app.port}")
        print(f"   DB: {app.db.host}:{app.db.port} (max_conn={app.db.max_connections})")
        print(f"   API: {app.api.base_url} (timeout={app.api.timeout}s, retries={app.api.retries})")
    except ValidationError as e:
        print(f"❌ Validation error: {e.key} = {e.value}")
        print(f"   {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
