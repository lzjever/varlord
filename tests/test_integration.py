"""
Integration tests for the complete configuration system.
"""

import os
import sys
from dataclasses import dataclass

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from varlord import Config, PriorityPolicy, sources  # noqa: E402

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


def test_full_workflow():
    """Test complete configuration workflow."""
    from dataclasses import field

    @dataclass(frozen=True)
    class AppConfig:
        host: str = field(
            default="127.0.0.1",
        )
        port: int = field(
            default=8000,
        )
        debug: bool = field(
            default=False,
        )
        timeout: float = field(
            default=30.0,
        )
        api_key: str = field(
            default=None,
        )  # Use str instead of Optional[str]

    # Set environment variables
    os.environ["HOST"] = "0.0.0.0"
    os.environ["PORT"] = "9000"
    os.environ["DEBUG"] = "true"
    os.environ["TIMEOUT"] = "60.5"

    try:
        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Env(model=AppConfig),
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
        for key in ["HOST", "PORT", "DEBUG", "TIMEOUT"]:
            os.environ.pop(key, None)


def test_priority_workflow():
    """Test priority ordering workflow."""
    from dataclasses import field

    @dataclass(frozen=True)
    class AppConfig:
        value: str = field(
            default="default",
        )

    os.environ["VALUE"] = "env"

    try:
        # Test 1: Default priority (sources order - later overrides earlier)
        # Defaults are automatically applied first, then Env
        cfg1 = Config(
            model=AppConfig,
            sources=[
                sources.Env(model=AppConfig),  # Overrides defaults
            ],
        )
        app1 = cfg1.load()
        assert app1.value == "env"

        # Test 2: Only defaults (no env)
        cfg2 = Config(
            model=AppConfig,
            sources=[],  # Only defaults
        )
        app2 = cfg2.load()
        assert app2.value == "default"

        print("✓ Priority workflow test passed")
    finally:
        os.environ.pop("VALUE", None)


def test_per_key_priority():
    """Test per-key priority policy."""
    from dataclasses import field

    @dataclass(frozen=True)
    class AppConfig:
        public: str = field(
            default="default-public",
        )
        secret: str = field(
            default="default-secret",
        )

    os.environ["PUBLIC"] = "env-public"
    os.environ["SECRET"] = "env-secret"

    try:
        cfg = Config(
            model=AppConfig,
            sources=[
                sources.Env(model=AppConfig),
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
        os.environ.pop("PUBLIC", None)
        os.environ.pop("SECRET", None)


if __name__ == "__main__":
    print("Running integration tests...")
    test_full_workflow()
    test_priority_workflow()
    test_per_key_priority()
    print("\n✅ All integration tests passed!")
