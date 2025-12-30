"""
Example demonstrating priority ordering.

Shows two ways to customize priority:
1. Reorder sources (recommended)
2. Use PriorityPolicy for per-key rules
"""

from dataclasses import dataclass
from varlord import Config, sources, PriorityPolicy


@dataclass(frozen=True)
class AppConfig:
    """Application configuration model."""

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    api_key: str = "default-key"
    db_host: str = "localhost"


def example_1_reorder_sources():
    """Method 1: Reorder sources (recommended - simplest)."""
    print("=== Example 1: Reorder Sources ===")

    # Priority is determined by sources order: later sources override earlier ones
    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Defaults(model=AppConfig),  # Lowest priority
            sources.Env(prefix="APP_"),
            sources.CLI(),  # Highest priority (last)
        ],
    )

    app = cfg.load()
    print(f"Config loaded: {app}")


def example_2_priority_policy():
    """Method 2: Use PriorityPolicy (advanced: per-key rules)."""
    print("\n=== Example 2: PriorityPolicy ===")

    # Use when you need different priority rules for different keys
    cfg = Config(
        model=AppConfig,
        sources=[
            sources.Defaults(model=AppConfig),
            sources.Env(prefix="APP_"),
            sources.CLI(),
        ],
        policy=PriorityPolicy(
            default=["defaults", "env", "cli"],
            overrides={
                "api_key": ["defaults", "env"],  # API key: env can override, but not CLI
                "db.*": ["defaults", "env"],  # DB config: env can override, but not CLI
            },
        ),
    )

    app = cfg.load()
    print(f"Config loaded: {app}")


def main():
    """Main function."""
    example_1_reorder_sources()
    example_2_priority_policy()


if __name__ == "__main__":
    main()
