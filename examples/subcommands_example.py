"""
Example demonstrating subcommands with Varlord.

This example shows how to implement command-line subcommands at the application layer
while using Varlord for configuration management.

Run with:
    python subcommands_example.py --help
    python subcommands_example.py console --help
    python subcommands_example.py console login --help
    python subcommands_example.py console login lzjever --verbose
    python subcommands_example.py console login lzjever --check-variables
    python subcommands_example.py gui fixed-position top-left --width 1024
    python subcommands_example.py gui fixed-position center --fullscreen
"""

import argparse
import sys
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from varlord import Config, sources
from varlord.metadata import get_all_field_keys
from varlord.model_validation import RequiredFieldError
from varlord.sources.base import Source, normalize_key


# Configuration models for different subcommands
@dataclass(frozen=True)
class ConsoleConfig:
    """Configuration for console commands."""

    username: str = field(metadata={"description": "Username for login"})
    password: Optional[str] = field(
        default=None, metadata={"description": "Password (optional, may prompt)"}
    )
    verbose: bool = field(default=False, metadata={"description": "Enable verbose output"})


class ArgparseSource(Source):
    """Source that provides values from argparse positional arguments.

    This is a cleaner alternative to setting environment variables for
    positional arguments from argparse.
    """

    def __init__(self, values: dict[str, Any], model=None, source_id=None):
        super().__init__(model=model, source_id=source_id or "argparse")
        self._values = values

    @property
    def name(self) -> str:
        return "argparse"

    def _generate_id(self) -> str:
        """Generate unique ID for argparse source."""
        return "argparse"

    def load(self) -> Mapping[str, Any]:
        """Load configuration from argparse positional arguments."""
        # Reset status
        self._load_status = "unknown"
        self._load_error = None

        try:
            # Normalize keys to match model field names
            result = {}
            for key, value in self._values.items():
                normalized = normalize_key(key)
                if self._model:
                    # Only include keys that match model fields
                    valid_keys = get_all_field_keys(self._model)
                    if normalized in valid_keys:
                        result[normalized] = value
                else:
                    result[normalized] = value

            self._load_status = "success"
            return result
        except Exception as e:
            self._load_status = "failed"
            self._load_error = str(e)
            raise


@dataclass(frozen=True)
class GUIConfig:
    """Configuration for GUI commands."""

    position: str = field(metadata={"description": "Window position (e.g., 'fixed', 'floating')"})
    width: int = field(default=800, metadata={"description": "Window width"})
    height: int = field(default=600, metadata={"description": "Window height"})
    fullscreen: bool = field(default=False, metadata={"description": "Start in fullscreen mode"})


def handle_console_login(args, remaining_args):
    """Handle 'console login' subcommand."""
    # Option 1: Use custom source for positional arguments (recommended)
    # This is cleaner than setting environment variables
    argparse_source = ArgparseSource(
        {"username": args.username},
        model=ConsoleConfig,
        source_id="argparse",
    )

    # Create config for console login
    cfg = Config(
        model=ConsoleConfig,
        sources=[
            argparse_source,  # Positional args from argparse (highest priority)
            sources.Env(),
            sources.CLI(argv=remaining_args),  # Pass remaining args to CLI source
        ],
    )

    # Option 2: Alternative approach using environment variables
    # import os
    # if args.username:
    #     os.environ["USERNAME"] = args.username
    # cfg = Config(
    #     model=ConsoleConfig,
    #     sources=[
    #         sources.Env(),
    #         sources.CLI(argv=remaining_args),
    #     ],
    # )

    # Handle standard CLI commands (--help, --check-variables)
    cfg.handle_cli_commands()

    try:
        config = cfg.load()
        print(f"✅ Logging in as: {config.username}")
        if config.password:
            print(f"   Password provided: {'*' * len(config.password)}")
        if config.verbose:
            print("   Verbose mode enabled")
        # Your login logic here
    except RequiredFieldError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)


def handle_gui_fixed_position(args, remaining_args):
    """Handle 'gui fixed-position' subcommand."""
    # Use custom source for positional arguments (recommended)
    argparse_source = ArgparseSource(
        {"position": args.position},
        model=GUIConfig,
        source_id="argparse",
    )

    # Create config for GUI
    cfg = Config(
        model=GUIConfig,
        sources=[
            argparse_source,  # Positional args from argparse (highest priority)
            sources.Env(),
            sources.CLI(argv=remaining_args),
        ],
    )

    cfg.handle_cli_commands()

    try:
        config = cfg.load()
        print(f"✅ Starting GUI with fixed position: {config.position}")
        print(f"   Window size: {config.width}x{config.height}")
        if config.fullscreen:
            print("   Fullscreen mode enabled")
        # Your GUI logic here
    except RequiredFieldError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)


def main():
    """Main entry point with subcommand routing."""
    parser = argparse.ArgumentParser(
        description="Example application with subcommands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Create subparsers for top-level commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Console command
    console_parser = subparsers.add_parser("console", help="Console commands")
    console_subparsers = console_parser.add_subparsers(
        dest="console_command", help="Console subcommands"
    )

    # Console login subcommand
    login_parser = console_subparsers.add_parser("login", help="Login to console")
    login_parser.add_argument("username", help="Username to login")

    # GUI command
    gui_parser = subparsers.add_parser("gui", help="GUI commands")
    gui_subparsers = gui_parser.add_subparsers(dest="gui_command", help="GUI subcommands")

    # GUI fixed-position subcommand
    fixed_position_parser = gui_subparsers.add_parser(
        "fixed-position", help="Start GUI with fixed position"
    )
    fixed_position_parser.add_argument(
        "position", help="Window position (e.g., 'top-left', 'center')"
    )

    # Parse arguments
    args, remaining = parser.parse_known_args()

    # Route to appropriate handler
    if args.command == "console":
        if args.console_command == "login":
            handle_console_login(args, remaining)
        else:
            console_parser.print_help()
            sys.exit(1)
    elif args.command == "gui":
        if args.gui_command == "fixed-position":
            handle_gui_fixed_position(args, remaining)
        else:
            gui_parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
