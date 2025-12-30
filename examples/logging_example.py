"""
Example demonstrating logging support.
"""

import logging
from dataclasses import dataclass
from varlord import Config, sources, set_log_level

# Enable debug logging to see configuration loading details
set_log_level(logging.DEBUG)


@dataclass(frozen=True)
class AppConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False


def main():
    """Main function."""
    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Defaults(model=AppConfig),
            sources.Env(prefix="APP_"),
        ],
    )

    app = cfg.load()
    print(f"Config loaded: {app}")


if __name__ == "__main__":
    main()
