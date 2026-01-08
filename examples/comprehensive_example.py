"""
Comprehensive example demonstrating Varlord's power in real-world scenarios.

This example shows:
- Multiple configuration sources from different locations (system, app, user)
- Different file types (YAML, JSON, TOML)
- Clear priority ordering
- Built-in diagnostics with --check-variables (-cv)
- Automatic CLI command handling

Run with:
    python comprehensive_example.py --help
    python comprehensive_example.py -cv
    python comprehensive_example.py --api-key your_key
"""

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from varlord import Config, sources
from varlord.model_validation import RequiredFieldError


@dataclass(frozen=True)
class AppConfig:
    """Application configuration with clear structure and validation."""

    # Required field - must be provided
    api_key: str = field(metadata={"description": "API key for authentication"})

    # Optional fields with sensible defaults
    host: str = field(default="127.0.0.1", metadata={"description": "Server host address"})
    port: int = field(default=8000, metadata={"description": "Server port number"})
    debug: bool = field(default=False, metadata={"description": "Enable debug mode"})
    timeout: float = field(default=30.0, metadata={"description": "Request timeout in seconds"})
    hello_message: Optional[str] = field(
        default=None, metadata={"description": "Optional greeting message"}
    )


def create_test_configs():
    """Create temporary config files for demonstration."""
    temp_dir = Path(tempfile.mkdtemp(prefix="varlord_demo_"))

    # System config (lowest priority)
    system_config = temp_dir / "system_config.yaml"
    system_config.write_text("""host: 0.0.0.0
port: 9000
timeout: 60.0
""")

    # App config
    app_config = temp_dir / "app_config.json"
    app_config.write_text("""{
    "host": "192.168.1.1",
    "port": 8080,
    "debug": true
}
""")

    # User config (higher priority)
    user_config = temp_dir / "user_config.yaml"
    user_config.write_text("""host: 10.0.0.1
port: 3000
debug: false
timeout: 45.0
""")

    # User TOML config (alternative)
    user_toml = temp_dir / "user_config.toml"
    user_toml.write_text("""host = "172.16.0.1"
port = 5000
""")

    # .env file for local development
    env_file = temp_dir / ".env"
    env_file.write_text("""HOST=localhost
PORT=7000
DEBUG=true
TIMEOUT=20.0
""")

    return temp_dir, {
        "system": system_config,
        "app": app_config,
        "user": user_config,
        "user_toml": user_toml,
        "env": env_file,
    }


def main():
    """Main function demonstrating comprehensive configuration management."""
    # Create temporary config files for demo
    temp_dir, config_files = create_test_configs()

    try:
        # Define configuration sources with clear priority order
        # Priority: CLI (highest) > User Config > App Config > System Config > Env > .env > Defaults (lowest)
        cfg = Config(
            model=AppConfig,
            sources=[
                # System-wide configuration (lowest priority, rarely overridden)
                sources.YAML(str(config_files["system"])),  # System config
                # Application-level configuration
                sources.JSON(str(config_files["app"])),  # App directory
                # User-specific configuration (overrides system and app configs)
                sources.YAML(str(config_files["user"])),  # User directory
                sources.TOML(str(config_files["user_toml"])),  # Alternative user config
                # Environment variables (common in containers/CI)
                sources.Env(),
                sources.DotEnv(str(config_files["env"])),  # Local development
                # Command-line arguments (highest priority, for debugging/overrides)
                sources.CLI(),
            ],
        )

        # One line to add comprehensive CLI management: --help, --check-variables, etc.
        # This single call adds:
        #   - --help / -h: Auto-generated help from your model metadata
        #   - --check-variables / -cv: Complete configuration diagnostics
        #   - Automatic validation and error reporting
        #   - Exit handling (exits if help/cv is requested)
        cfg.handle_cli_commands()  # Handles --help, -cv automatically, exits if needed

        # Load configuration - type-safe, validated, ready to use
        app = cfg.load()

        # Your application code
        print("✅ Configuration loaded successfully!")
        print(f"   Server: {app.host}:{app.port}")
        print(f"   Debug: {app.debug}, Timeout: {app.timeout}s")
        if app.hello_message:
            print(f"   Message: {app.hello_message}")

    except RequiredFieldError as e:
        print(f"❌ Configuration error: {e}")
        print("\n💡 Tip: Provide required fields via:")
        print("   - Environment variable: export API_KEY=your_key")
        print("   - CLI argument: python comprehensive_example.py --api-key your_key")
        print("   - Config file: Add 'api_key: your_key' to any config file")
        print("   - For diagnostics: python comprehensive_example.py -cv")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    exit(main())
