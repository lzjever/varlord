CLI Commands
============

All applications using Varlord automatically support standard command-line options for
configuration management and diagnostics. This guide explains how to handle these commands
in your application.

Standard Command-Line Options
-----------------------------

Varlord provides two standard command-line options that all applications should support:

- ``--help, -h``: Display help message and exit
- ``--check-variables, -cv``: Display diagnostic table of all configuration variables and exit

These options are automatically handled by Varlord's ``Config.handle_cli_commands()`` method.

Basic Usage
-----------

To enable standard CLI command handling in your application, call ``handle_cli_commands()``
once at program startup, before calling ``load()``:

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=8000)

   def main():
       # Create config
       cfg = Config(
           model=AppConfig,
           sources=[sources.Env(), sources.CLI()],
       )

       # Handle CLI commands (--help, --check-variables)
       # This should be called once at startup
       cfg.handle_cli_commands()

       # Load configuration
       app = cfg.load()

       # Your application logic here
       print(f"Starting server on {app.host}:{app.port}")

   if __name__ == "__main__":
       main()

**Important**: ``handle_cli_commands()`` will exit the program if ``--help`` or ``-h`` is present,
or if ``--check-variables`` or ``-cv`` is present and required fields are missing.

The ``--help`` Option
---------------------

When users run your application with ``--help`` or ``-h``, Varlord displays:

1. **Standard Options**: Information about ``--help`` and ``--check-variables``
2. **Usage**: How to run the application
3. **Required Arguments**: All required configuration fields with their types and descriptions
4. **Optional Arguments**: All optional configuration fields with their types, defaults, and descriptions
5. **Boolean Flags**: Special handling for boolean fields (``--flag`` / ``--no-flag``)
6. **Variable Mapping Rules**: Link to documentation for detailed mapping rules

Example help output:

.. code-block:: text

   Standard Options:

     --help, -h
       Show this help message and exit

     --check-variables, -cv
       Show diagnostic table of all configuration variables and exit
       Displays variable status (Required/Optional, Loaded/Missing, Source, Value)

   ---
   Usage: app.py [OPTIONS]

   Required Arguments:
     --host STR
       Server host address

   Optional Arguments:
     --port INT (default: 8000)
       Server port number

   Boolean Flags:
     --debug / --no-debug
       Enable debug mode

   Variable Mapping Rules:

     For detailed mapping rules and examples for each source type, see:
     https://varlord.readthedocs.io/en/latest/user_guide/key_mapping.html

The ``--check-variables`` Option
---------------------------------

The ``--check-variables`` (or ``-cv``) option displays comprehensive diagnostic information
about your configuration:

1. **Variable Status Table**: Shows all configuration variables with:
   - Variable name
   - Required/Optional status
   - Current status (Loaded, Using Default, Missing, etc.)
   - Source (which source provided the value)
   - Value (truncated if too long)

2. **Source Information Table**: Shows detailed diagnostics for each source:
   - Priority order (1 = lowest, higher numbers = higher priority)
   - Source name (from source.name property)
   - Instance (source string representation via str(source))
   - Load time in milliseconds (for performance diagnostics)
   - Watch support status (Yes/No)
   - Last update time (N/A for now, extensible for future use)

Example diagnostic output:

.. code-block:: text

   +--------------------------------------------+----------+---------------+----------+--------+
   | Variable                                   | Required | Status        | Source   | Value  |
   +--------------------------------------------+----------+---------------+----------+--------+
   | host                                       | Required | Missing       | defaults | None   |
   | port                                       | Optional | Using Default | defaults | 8000   |
   | debug                                      | Optional | Using Default | defaults | False  |
   +--------------------------------------------+----------+---------------+----------+--------+

   Configuration Source Priority and Details:

   +------------+-------------+------------------------------+----------------+---------------+-------------+
   | Priority   | Source Name | Instance                     | Load Time (ms) | Watch Support | Last Update |
   +------------+-------------+------------------------------+----------------+---------------+-------------+
   | 1 (lowest) | defaults    | <Defaults(model=AppConfig)>  | 0.00           | No            | N/A         |
   | 2          | env         | <Env(model-based)>           | 0.20           | No            | N/A         |
   | 3          | cli         | <CLI()>                      | 0.27           | No            | N/A         |
   +------------+-------------+------------------------------+----------------+---------------+-------------+

   Note: Later sources override earlier ones (higher priority).

If required fields are missing, the diagnostic output is followed by a helpful error message:

.. code-block:: text

   ⚠️  Missing required fields: host
      Exiting with code 1. Please provide these fields and try again.
      For help, run: python app.py --help

Implementation Details
----------------------

The ``handle_cli_commands()`` method:

1. Checks for ``--help`` or ``-h`` flags and displays help if found, then exits
2. Checks for ``--check-variables`` or ``-cv`` flags and displays diagnostics if found
3. If ``--check-variables`` is present and required fields are missing, displays the diagnostic
   table, shows an error message, and exits with code 1
4. If ``--check-variables`` is present and all required fields are present, displays the diagnostic
   table and exits with code 0
5. Otherwise, returns normally and allows your application to continue

**Note**: The method uses ``sys.exit()`` internally, so it will terminate your program when
handling help or check-variables commands. This is intentional - these are diagnostic commands
that should not continue to normal execution.

Custom Help Text
----------------

Help text is automatically generated from your model's field metadata:

- **Description**: Use ``metadata={"description": "..."}`` for field descriptions
- **Help**: Use ``metadata={"help": "..."}`` for more detailed help text (takes precedence over description)

Example:

.. code-block:: python

   @dataclass
   class AppConfig:
       host: str = field(
           metadata={
               "description": "Server host address",
               "help": "The IP address or hostname where the server will listen"
           }
       )
       port: int = field(
           default=8000,
           metadata={
               
               "description": "Server port number"
           }
       )

Error Handling
--------------

When required fields are missing and ``--check-variables`` is used, Varlord:

1. Displays the diagnostic table showing which fields are missing
2. Shows a clear error message with the list of missing fields
3. Provides a hint to run ``--help`` for more information
4. Exits with code 1

This allows users to quickly diagnose configuration issues without running the full application.

Best Practices
--------------

1. **Always call ``handle_cli_commands()`` at startup**: This ensures users can access help
   and diagnostics even if configuration is invalid.

2. **Use descriptive field metadata**: Provide clear ``description`` or ``help`` text for
   all fields to make the help output more useful.

3. **Handle ``RequiredFieldError``**: Even after ``handle_cli_commands()``, you should still
   catch ``RequiredFieldError`` in your main code to provide application-specific error handling:

   .. code-block:: python

      from varlord.model_validation import RequiredFieldError

      try:
          cfg.handle_cli_commands()
          app = cfg.load()
      except RequiredFieldError as e:
          print(f"❌ Configuration error: {e}")
          sys.exit(1)

4. **Test your help output**: Run your application with ``--help`` to ensure all fields
   are properly documented.

5. **Use ``--check-variables`` for debugging**: When troubleshooting configuration issues,
   use ``--check-variables`` to see exactly which sources are providing which values.

Subcommands
-----------

Varlord's CLI source handles flat configuration arguments only. For applications that need
command-line subcommands (e.g., ``myapp console login``), handle subcommand routing at the
application layer using standard ``argparse``, then use varlord to load configuration for
each subcommand.

See :doc:`subcommands` for detailed guidance and examples on implementing subcommands with varlord.

