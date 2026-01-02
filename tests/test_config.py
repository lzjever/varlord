"""
Tests for Config class.
"""

from varlord import Config, sources


def test_config_basic(sample_config_model):
    """Test basic config loading (no sources, only defaults)."""
    cfg = Config(
        model=sample_config_model,
        sources=[],  # No sources needed - defaults are automatic
    )

    app = cfg.load()
    assert app.host == "127.0.0.1"
    assert app.port == 8000
    assert app.debug is False


def test_config_with_env(sample_config_model, monkeypatch):
    """Test config with environment variables."""
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "9000")

    cfg = Config(
        model=sample_config_model,
        sources=[
            sources.Env(),  # No prefix - filtered by model
        ],
    )

    app = cfg.load()
    assert app.host == "0.0.0.0"  # Overridden by env
    assert app.port == 9000  # Overridden by env (type conversion works)
    assert app.debug is False


def test_config_priority(sample_config_model, monkeypatch):
    """Test config priority ordering."""
    monkeypatch.setenv("HOST", "env_value")

    # Priority is determined by sources order: later sources override earlier ones
    # Defaults are automatically applied first
    cfg = Config(
        model=sample_config_model,
        sources=[
            sources.Env(),  # Later source overrides defaults
        ],
    )

    app = cfg.load()
    assert app.host == "env_value"
