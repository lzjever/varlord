"""
Integration tests for the complete configuration system.
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from varlord import Config, sources, PriorityPolicy


def test_full_workflow():
    """Test complete configuration workflow."""

    @dataclass(frozen=True)
    class AppConfig:
        host: str = "127.0.0.1"
        port: int = 8000
        debug: bool = False
        timeout: float = 30.0
        api_key: Optional[str] = None

    # Set environment variables
    os.environ["APP_HOST"] = "0.0.0.0"
    os.environ["APP_PORT"] = "9000"
    os.environ["APP_DEBUG"] = "true"
    os.environ["APP_TIMEOUT"] = "60.5"

    try:
        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.Env(prefix="APP_"),
            ],
        )

        app = cfg.load()

        assert app.host == "0.0.0.0"
        assert app.port == 9000
        assert app.debug is True
        assert app.timeout == 60.5
        assert app.api_key is None

        print("✓ Full workflow test passed")
    finally:
        # Cleanup
        for key in ["APP_HOST", "APP_PORT", "APP_DEBUG", "APP_TIMEOUT"]:
            os.environ.pop(key, None)


def test_priority_workflow():
    """Test priority ordering workflow."""

    @dataclass(frozen=True)
    class AppConfig:
        value: str = "default"

    os.environ["APP_VALUE"] = "env"

    try:
        # Test 1: Default priority (sources order - later overrides earlier)
        cfg1 = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.Env(prefix="APP_"),  # Later source overrides
            ],
        )
        app1 = cfg1.load()
        assert app1.value == "env"

        # Test 2: Reversed order (defaults later, so it overrides env)
        cfg2 = Config(
            model=AppConfig,
            sources=[
                sources.Env(prefix="APP_"),
                sources.Defaults(model=AppConfig),  # Later source overrides
            ],
        )
        app2 = cfg2.load()
        assert app2.value == "default"

        print("✓ Priority workflow test passed")
    finally:
        os.environ.pop("APP_VALUE", None)


def test_per_key_priority():
    """Test per-key priority policy."""

    @dataclass(frozen=True)
    class AppConfig:
        public: str = "default-public"
        secret: str = "default-secret"

    os.environ["APP_PUBLIC"] = "env-public"
    os.environ["APP_SECRET"] = "env-secret"

    try:
        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Defaults(model=AppConfig),
                sources.Env(prefix="APP_"),
            ],
            policy=PriorityPolicy(
                default=["defaults", "env"],
                overrides={
                    "secret": ["defaults"],  # Secret should not use env
                },
            ),
        )

        app = cfg.load()
        assert app.public == "env-public"
        assert app.secret == "default-secret"

        print("✓ Per-key priority test passed")
    finally:
        os.environ.pop("APP_PUBLIC", None)
        os.environ.pop("APP_SECRET", None)


if __name__ == "__main__":
    print("Running integration tests...")
    test_full_workflow()
    test_priority_workflow()
    test_per_key_priority()
    print("\n✅ All integration tests passed!")
