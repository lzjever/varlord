"""
Example demonstrating validation with nested configuration.
"""

import os
import sys
from dataclasses import dataclass
from varlord import Config, sources
from varlord.validators import validate_range, validate_regex, validate_not_empty, ValidationError

# Set environment variables for testing
os.environ["APP_DB__HOST"] = "localhost"
os.environ["APP_DB__PORT"] = "5432"
os.environ["APP_API__TIMEOUT"] = "30"


@dataclass(frozen=True)
class DBConfig:
    """Database configuration."""

    host: str = "127.0.0.1"
    port: int = 5432
    max_connections: int = 10

    def __post_init__(self):
        """Validate database configuration."""
        validate_not_empty(self.host)
        validate_range(self.port, min=1, max=65535)
        validate_range(self.max_connections, min=1, max=100)


@dataclass(frozen=True)
class APIConfig:
    """API configuration."""

    timeout: int = 30
    retries: int = 3
    base_url: str = "https://api.example.com"

    def __post_init__(self):
        """Validate API configuration."""
        validate_range(self.timeout, min=1, max=300)
        validate_range(self.retries, min=0, max=10)
        validate_regex(self.base_url, r"^https?://.+")


@dataclass(frozen=True)
class AppConfig:
    """Application configuration with nested structures."""

    host: str = "0.0.0.0"
    port: int = 8000
    db: DBConfig = None  # type: ignore
    api: APIConfig = None  # type: ignore

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
    try:
        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.Env(prefix="APP_", separator="__"),
            ],
        )

        app = cfg.load()
        print("Config loaded successfully:")
        print(f"  Host: {app.host}:{app.port}")
        print(f"  DB: {app.db.host}:{app.db.port} (max_conn={app.db.max_connections})")
        print(f"  API: {app.api.base_url} (timeout={app.api.timeout}s, retries={app.api.retries})")
    except ValidationError as e:
        print(f"Validation error: {e.key} = {e.value}: {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
