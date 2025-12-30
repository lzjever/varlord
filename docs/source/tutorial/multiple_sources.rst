Multiple Sources
================

In this tutorial, you'll learn how to combine configuration from multiple
sources, understanding how priority works and how later sources override
earlier ones.

Learning Objectives
-------------------

By the end of this tutorial, you'll be able to:

- Load configuration from multiple sources (defaults, environment, CLI)
- Understand source priority and override behavior
- Use the convenient ``Config.from_model()`` method

Step 1: Understanding Source Priority
--------------------------------------

Varlord merges configurations from multiple sources. **Later sources override
earlier ones**. Let's see this in action:

.. code-block:: python
   :linenos:

   import os
   from dataclasses import dataclass
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = "127.0.0.1"  # Default
       port: int = 8000          # Default
       debug: bool = False       # Default

   # Set environment variable
   os.environ["APP_HOST"] = "0.0.0.0"
   os.environ["APP_PORT"] = "9000"

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Defaults(model=AppConfig),  # 1. Loads defaults
           sources.Env(prefix="APP_"),         # 2. Overrides with env vars
       ],
   )

   app = cfg.load()
   print(f"Host: {app.host}")  # From env: 0.0.0.0
   print(f"Port: {app.port}")  # From env: 9000
   print(f"Debug: {app.debug}")  # From defaults: False

**Expected Output**:

.. code-block:: text

   Host: 0.0.0.0
   Port: 9000
   Debug: False

**Key Points**:

- Defaults are loaded first (lowest priority)
- Environment variables override defaults
- Fields not in environment keep their default values

Step 2: Adding Command-Line Arguments
--------------------------------------

Command-line arguments have the highest priority (when listed last):

.. code-block:: python
   :linenos:

   import sys
   import os
   from dataclasses import dataclass
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = "127.0.0.1"
       port: int = 8000
       debug: bool = False

   # Set environment variable
   os.environ["APP_PORT"] = "9000"

   # Simulate command-line arguments
   sys.argv = ["app.py", "--host", "192.168.1.1", "--port", "8080", "--debug"]

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Defaults(model=AppConfig),  # 1. Defaults
           sources.Env(prefix="APP_"),         # 2. Environment
           sources.CLI(model=AppConfig),       # 3. CLI (highest priority)
       ],
   )

   app = cfg.load()
   print(f"Host: {app.host}")   # From CLI: 192.168.1.1
   print(f"Port: {app.port}")   # From CLI: 8080 (overrides env)
   print(f"Debug: {app.debug}")  # From CLI: True

**Expected Output**:

.. code-block:: text

   Host: 192.168.1.1
   Port: 8080
   Debug: True

**Priority Order** (lowest to highest):

1. Defaults
2. Environment variables
3. Command-line arguments

Step 3: Using Config.from_model() Convenience Method
------------------------------------------------------

Varlord provides a convenient method to set up common sources:

.. code-block:: python
   :linenos:

   import os
   from dataclasses import dataclass
   from varlord import Config

   @dataclass(frozen=True)
   class AppConfig:
       host: str = "127.0.0.1"
       port: int = 8000
       debug: bool = False

   # Set environment variables
   os.environ["APP_HOST"] = "0.0.0.0"
   os.environ["APP_PORT"] = "9000"

   # Convenient setup
   cfg = Config.from_model(
       model=AppConfig,
       env_prefix="APP_",
       cli=True,  # Enable CLI arguments
   )

   app = cfg.load()
   print(f"Host: {app.host}")
   print(f"Port: {app.port}")

**Expected Output**:

.. code-block:: text

   Host: 0.0.0.0
   Port: 9000

**Benefits of ``Config.from_model()``**:

- Less boilerplate code
- Automatically sets up common sources
- Model is automatically injected to sources

Step 4: Environment Variable Naming
-----------------------------------

Environment variables are normalized to lowercase and use dot notation for
nested keys:

.. code-block:: python
   :linenos:

   import os
   from dataclasses import dataclass
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = "127.0.0.1"
       port: int = 8000

   # Environment variables with prefix
   os.environ["APP_HOST"] = "0.0.0.0"
   os.environ["APP_PORT"] = "9000"

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Defaults(model=AppConfig),
           sources.Env(prefix="APP_"),  # Prefix filters variables
       ],
   )

   app = cfg.load()
   print(f"Host: {app.host}")
   print(f"Port: {app.port}")

**Key Mapping Rules**:

- ``APP_HOST`` → ``host`` (prefix removed, lowercase)
- ``APP_PORT`` → ``port`` (prefix removed, lowercase)
- For nested keys: ``APP_DB__HOST`` → ``db.host`` (``__`` becomes ``.``)

Step 5: Command-Line Argument Format
-------------------------------------

Command-line arguments use kebab-case and are converted to dot notation:

.. code-block:: python
   :linenos:

   import sys
   from dataclasses import dataclass
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = "127.0.0.1"
       port: int = 8000
       debug: bool = False

   # Command-line arguments
   sys.argv = [
       "app.py",
       "--host", "0.0.0.0",
       "--port", "8080",
       "--debug",  # Boolean flag (no value needed)
   ]

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Defaults(model=AppConfig),
           sources.CLI(model=AppConfig),
       ],
   )

   app = cfg.load()
   print(f"Host: {app.host}")
   print(f"Port: {app.port}")
   print(f"Debug: {app.debug}")

**Expected Output**:

.. code-block:: text

   Host: 0.0.0.0
   Port: 8080
   Debug: True

**CLI Argument Rules**:

- Use ``--field-name`` for regular fields
- Use ``--flag`` for boolean True, ``--no-flag`` for boolean False
- Arguments are automatically converted to the correct type

Step 6: Complete Example
------------------------

Here's a complete example combining all sources:

.. code-block:: python
   :name: multiple_sources_complete
   :linenos:

   import os
   import sys
   from dataclasses import dataclass
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = "127.0.0.1"
       port: int = 8000
       debug: bool = False
       app_name: str = "MyApp"

   def main():
       # Set environment variables
       os.environ["APP_PORT"] = "9000"
       os.environ["APP_DEBUG"] = "true"

       # Simulate CLI arguments
       sys.argv = ["app.py", "--host", "0.0.0.0"]

       # Create configuration with multiple sources
       cfg = Config(
           model=AppConfig,
           sources=[
               sources.Defaults(model=AppConfig),  # Priority 1 (lowest)
               sources.Env(prefix="APP_"),         # Priority 2
               sources.CLI(model=AppConfig),       # Priority 3 (highest)
           ],
       )

       app = cfg.load()

       print("Configuration (merged from all sources):")
       print(f"  Host: {app.host}")      # From CLI: 0.0.0.0
       print(f"  Port: {app.port}")      # From Env: 9000
       print(f"  Debug: {app.debug}")   # From Env: True
       print(f"  App Name: {app.app_name}")  # From Defaults: MyApp

   if __name__ == "__main__":
       main()

**Expected Output**:

.. code-block:: text

   Configuration (merged from all sources):
     Host: 0.0.0.0
     Port: 9000
     Debug: True
     App Name: MyApp

Common Pitfalls
---------------

**Pitfall 1: Wrong source order**

.. code-block:: python
   :emphasize-lines: 5-7

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.CLI(model=AppConfig),  # CLI first!
           sources.Env(prefix="APP_"),   # Env will override CLI
           sources.Defaults(model=AppConfig),
       ],
   )
   # CLI arguments will be overridden by env vars - probably not what you want!

**Solution**: Always put sources in priority order (lowest to highest):
Defaults → Env → CLI.

**Pitfall 2: Missing prefix in environment variables**

.. code-block:: python
   :emphasize-lines: 2, 7

   os.environ["HOST"] = "0.0.0.0"  # No prefix

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(prefix="APP_"),  # Looking for APP_* variables
       ],
   )
   # HOST won't be loaded because it doesn't have APP_ prefix

**Solution**: Use the correct prefix, or use ``prefix=None`` to load all
environment variables (not recommended for production).

**Pitfall 3: Type conversion issues**

.. code-block:: python
   :emphasize-lines: 2

   os.environ["APP_PORT"] = "not-a-number"

   # This will raise ValueError during type conversion
   app = cfg.load()

**Solution**: Ensure environment variables can be converted to the target type.
Varlord automatically converts strings to the appropriate types.

Best Practices
--------------

1. **Always include Defaults first**: Provides fallback values
2. **Use prefixes for environment variables**: Prevents conflicts
3. **Order sources by priority**: Defaults → Env → CLI
4. **Use Config.from_model() for common setups**: Reduces boilerplate

Next Steps
----------

Now that you understand multiple sources, let's learn about :doc:`nested_configuration`
to handle complex configuration structures.

