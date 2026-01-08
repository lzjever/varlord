Subcommands and Command Routing
=================================

Varlord focuses on configuration management and does not include built-in support for
command-line subcommands. This guide explains why and shows you how to implement subcommands
in your application using standard Python libraries.

Why No Built-in Subcommand Support?
------------------------------------

Varlord's CLI source is designed to handle **flat configuration arguments** only. This is
a deliberate design decision:

1. **Separation of Concerns**: Configuration management and command routing are different concerns
2. **Flexibility**: Different applications need different subcommand structures
3. **Simplicity**: Keeping varlord focused makes it easier to use and maintain
4. **Standard Libraries**: Python's ``argparse`` already provides excellent subcommand support

Recommended Approach
--------------------

The recommended approach is to handle subcommands at the **application layer** using
standard ``argparse``, then use varlord to load configuration for each subcommand.

Basic Pattern
~~~~~~~~~~~~~

The basic pattern is:

1. Use ``argparse`` to parse subcommands at the application level
2. Create separate configuration models for each subcommand (if needed)
3. Use varlord's ``Config`` class to load configuration for the selected subcommand
4. Execute the appropriate command handler

Example: Simple Two-Level Subcommands
--------------------------------------

Here's a complete example showing how to implement subcommands:

.. code-block:: python
   :linenos:

   import argparse
   import sys
   from dataclasses import dataclass, field
   from typing import Optional

   from varlord import Config, sources
   from varlord.model_validation import RequiredFieldError

   # Configuration models for different subcommands
   @dataclass(frozen=True)
   class ConsoleConfig:
       """Configuration for console commands."""
       username: str = field(metadata={"description": "Username for login"})
       password: Optional[str] = field(
           default=None, metadata={"description": "Password (optional, may prompt)"}
       )
       verbose: bool = field(
           default=False, metadata={"description": "Enable verbose output"}
       )

   @dataclass(frozen=True)
   class GUIConfig:
       """Configuration for GUI commands."""
       position: str = field(metadata={"description": "Window position (e.g., 'fixed', 'floating')"})
       width: int = field(default=800, metadata={"description": "Window width"})
       height: int = field(default=600, metadata={"description": "Window height"})
       fullscreen: bool = field(
           default=False, metadata={"description": "Start in fullscreen mode"}
       )

   def handle_console_login(args, remaining_args):
       """Handle 'console login' subcommand."""
       # Option 1: Set positional argument as environment variable for varlord
       import os
       if args.username:
           os.environ["USERNAME"] = args.username

       # Option 2: Or create a custom source that provides the username
       # from argparse args (see "Advanced: Custom Source for Positional Args" below)

       # Create config for console login
       cfg = Config(
           model=ConsoleConfig,
           sources=[
               sources.Env(),
               sources.CLI(argv=remaining_args),  # Pass remaining args to CLI source
           ],
       )

       # Handle standard CLI commands (--help, --check-variables)
       cfg.handle_cli_commands()

       try:
           config = cfg.load()
           print(f"Logging in as: {config.username}")
           if config.verbose:
               print("Verbose mode enabled")
           # Your login logic here
       except RequiredFieldError as e:
           print(f"Error: {e}")
           sys.exit(1)

   def handle_gui_fixed_position(args, remaining_args):
       """Handle 'gui fixed-position' subcommand."""
       # Create config for GUI
       cfg = Config(
           model=GUIConfig,
           sources=[
               sources.Env(),
               sources.CLI(argv=remaining_args),
           ],
       )

       cfg.handle_cli_commands()

       try:
           config = cfg.load()
           print(f"Starting GUI with fixed position: {config.position}")
           print(f"Window size: {config.width}x{config.height}")
           if config.fullscreen:
               print("Fullscreen mode enabled")
           # Your GUI logic here
       except RequiredFieldError as e:
           print(f"Error: {e}")
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
       gui_subparsers = gui_parser.add_subparsers(
           dest="gui_command", help="GUI subcommands"
       )

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

**Key Points**:

1. **Application-level routing**: ``argparse`` handles subcommand parsing
2. **Separate config models**: Each subcommand can have its own configuration model
3. **Pass remaining args**: Use ``sources.CLI(argv=remaining_args)`` to pass remaining arguments
   to varlord's CLI source
4. **Standard CLI support**: Each subcommand still supports ``--help`` and ``--check-variables``

Usage Examples
~~~~~~~~~~~~~~

With the above code, users can:

.. code-block:: bash

   # Show main help
   python app.py --help

   # Show console help
   python app.py console --help

   # Show login help (includes varlord's --help and --check-variables)
   python app.py console login --help

   # Login with username (password from env or prompt)
   python app.py console login lzjever --verbose

   # Check configuration for login
   python app.py console login lzjever --check-variables

   # GUI with fixed position
   python app.py gui fixed-position top-left --width 1024 --height 768

   # GUI fullscreen
   python app.py gui fixed-position center --fullscreen

Advanced Pattern: Shared Configuration
---------------------------------------

For applications where multiple subcommands share some configuration, you can:

1. Create a base configuration model with shared fields
2. Create subcommand-specific models that extend or compose the base model
3. Use nested dataclasses for organization

Example:

.. code-block:: python

   @dataclass(frozen=True)
   class BaseConfig:
       """Shared configuration for all commands."""
       debug: bool = field(default=False, metadata={"description": "Enable debug mode"})
       log_level: str = field(default="INFO", metadata={"description": "Logging level"})

   @dataclass(frozen=True)
   class ConsoleConfig:
       """Console-specific configuration."""
       base: BaseConfig = field(default_factory=BaseConfig)
       username: str = field(metadata={"description": "Username"})
       # ... console-specific fields

   @dataclass(frozen=True)
   class GUIConfig:
       """GUI-specific configuration."""
       base: BaseConfig = field(default_factory=BaseConfig)
       position: str = field(metadata={"description": "Window position"})
       # ... GUI-specific fields

Best Practices
--------------

1. **Separate Configuration Models**
   - Each subcommand should have its own configuration model if it has unique requirements
   - This provides type safety and clear documentation

2. **Use ``parse_known_args()``**
   - Use ``parser.parse_known_args()`` to separate subcommand arguments from configuration arguments
   - Pass remaining arguments to varlord's CLI source

3. **Handle Standard Options**
   - Always call ``cfg.handle_cli_commands()`` for each subcommand
   - This ensures ``--help`` and ``--check-variables`` work correctly

4. **Error Handling**
   - Catch ``RequiredFieldError`` for user-friendly error messages
   - Provide clear guidance on how to fix configuration issues

5. **Help Text**
   - Use descriptive help text in argparse parsers
   - Use field metadata (``description``, ``help``) in configuration models
   - This provides comprehensive help at both the routing and configuration levels

6. **Testing**
   - Test each subcommand independently
   - Test with ``--help`` and ``--check-variables``
   - Test error cases (missing required fields, invalid values)

Common Patterns
---------------

Pattern 1: Simple Command with Arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For simple commands that just need arguments (no sub-subcommands):

.. code-block:: python

   parser = argparse.ArgumentParser()
   parser.add_argument("command", choices=["start", "stop", "status"])
   args, remaining = parser.parse_known_args()

   if args.command == "start":
       cfg = Config(model=StartConfig, sources=[sources.Env(), sources.CLI(argv=remaining)])
       cfg.handle_cli_commands()
       config = cfg.load()
       # Handle start

Pattern 2: Nested Subcommands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For deeply nested subcommands:

.. code-block:: python

   parser = argparse.ArgumentParser()
   subparsers = parser.add_subparsers(dest="command")

   db_parser = subparsers.add_parser("db")
   db_subparsers = db_parser.add_subparsers(dest="db_command")

   migrate_parser = db_subparsers.add_parser("migrate")
   migrate_subparsers = migrate_parser.add_subparsers(dest="migrate_command")

   up_parser = migrate_subparsers.add_parser("up")
   # ... handle db migrate up

Pattern 3: Command with Positional Arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For commands that need positional arguments before configuration:

.. code-block:: python

   parser = argparse.ArgumentParser()
   subparsers = parser.add_subparsers(dest="command")

   login_parser = subparsers.add_parser("login")
   login_parser.add_argument("username", help="Username")
   # username is handled by argparse, remaining args go to varlord

   args, remaining = parser.parse_known_args()
   if args.command == "login":
       # args.username is available here
       # remaining contains configuration arguments for varlord
       cfg = Config(model=LoginConfig, sources=[sources.CLI(argv=remaining)])

Advanced: Custom Source for Positional Args
--------------------------------------------

If you prefer not to set environment variables, you can create a custom source that provides
positional arguments from argparse:

.. code-block:: python

   from varlord.sources.base import Source, normalize_key
   from varlord.metadata import get_all_field_keys
   from typing import Mapping, Any

   class ArgparseSource(Source):
       """Source that provides values from argparse positional arguments."""
       
       def __init__(self, values: dict[str, Any], model=None, source_id=None):
           super().__init__(model=model, source_id=source_id or "argparse")
           self._values = values
       
       @property
       def name(self) -> str:
           return "argparse"
       
       def _generate_id(self) -> str:
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

   # Usage:
   def handle_console_login(args, remaining_args):
       # Create custom source for positional args
       argparse_source = ArgparseSource(
           {"username": args.username},
           model=ConsoleConfig,
           source_id="argparse",
       )
       
       cfg = Config(
           model=ConsoleConfig,
           sources=[
               argparse_source,  # Positional args (highest priority)
               sources.Env(),
               sources.CLI(argv=remaining_args),
           ],
       )
       
       cfg.handle_cli_commands()
       config = cfg.load()
       # ...

This approach is cleaner than setting environment variables and gives you more control over
priority ordering.

Summary
-------

- **Varlord handles configuration**: Use varlord for loading and managing configuration
- **Application handles routing**: Use ``argparse`` for subcommand routing
- **Separate models**: Create separate configuration models for each subcommand
- **Pass remaining args**: Use ``sources.CLI(argv=remaining_args)`` to pass configuration arguments
- **Standard support**: Each subcommand automatically supports ``--help`` and ``--check-variables``
- **Positional arguments**: Either set as environment variables or use a custom source

This approach keeps varlord simple and focused while giving you full flexibility to implement
any subcommand structure your application needs.

See :doc:`../examples/subcommands_example` for a complete working example.

