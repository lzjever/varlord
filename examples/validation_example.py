"""
Example demonstrating configuration validation.
"""

import os
from dataclasses import dataclass

from varlord import Config, sources
from varlord.validators import validate_range, validate_regex

# Set environment variables for testing
os.environ["APP_PORT"] = "9000"
os.environ["APP_HOST"] = "0.0.0.0"


@dataclass(frozen=True)
class AppConfig:
    host: str = "127.0.0.1"
    port: int = 8000

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate port range
        validate_range(self.port, min=1, max=65535)
        # Validate host format (simple IP check)
        validate_regex(self.host, r"^\d+\.\d+\.\d+\.\d+$")


def main():
    """Main function."""
    try:
        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Env(),  # Model defaults applied automatically, model auto-injected
            ],
        )

        app = cfg.load()
        print(f"Config loaded: {app}")
    except Exception as e:
        print(f"Validation error: {e}")


if __name__ == "__main__":
    main()
