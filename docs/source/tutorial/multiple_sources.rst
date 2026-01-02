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
   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="127.0.0.1")  # Default
       port: int = field(default=8000)          # Default
       debug: bool = field(default=False)       # Default

   # Set environment variable (no prefix needed - filtered by model)
   os.environ["HOST"] = "0.0.0.0"
   os.environ["PORT"] = "9000"

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Model auto-injected, defaults applied first, then env overrides
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

- Model defaults are automatically applied first (lowest priority)
- Environment variables override defaults
- Only environment variables that match model fields are loaded
- Fields not in environment keep their default values

Step 2: Adding Command-Line Arguments
--------------------------------------

Command-line arguments have the highest priority (when listed last):

.. code-block:: python
   :linenos:

   import sys
   import os
   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="127.0.0.1")
       port: int = field(default=8000)
       debug: bool = field(default=False)

   # Set environment variable
   os.environ["PORT"] = "9000"

   # Simulate command-line arguments
   sys.argv = ["app.py", "--host", "192.168.1.1", "--port", "8080", "--debug"]

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),         # 1. Environment (overrides defaults)
           sources.CLI(),         # 2. CLI (highest priority, overrides env)
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

1. Model defaults (automatically applied)
2. Environment variables
3. Command-line arguments

Step 3: Using Config.from_model() Convenience Method
------------------------------------------------------

Varlord provides a convenient method to set up common sources:

.. code-block:: python
   :linenos:

   import os
   from dataclasses import dataclass, field
   from varlord import Config

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="127.0.0.1")
       port: int = field(default=8000)
       debug: bool = field(default=False)

   # Set environment variables (no prefix needed)
   os.environ["HOST"] = "0.0.0.0"
   os.environ["PORT"] = "9000"

   # Convenient setup
   cfg = Config.from_model(
       model=AppConfig,
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
- Model is automatically injected to all sources
- Model defaults are automatically applied

Step 4: Environment Variable Naming
-----------------------------------

Environment variables are normalized to lowercase and use dot notation for
nested keys:

.. code-block:: python
   :linenos:

   import os
   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="127.0.0.1")
       port: int = field(default=8000)

   # Environment variables (filtered by model - no prefix needed)
   os.environ["HOST"] = "0.0.0.0"
   os.environ["PORT"] = "9000"
   os.environ["UNRELATED_VAR"] = "ignored"  # Will be filtered out

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Model auto-injected, only loads HOST and PORT (filtered by model)
       ],
   )

   app = cfg.load()
   print(f"Host: {app.host}")
   print(f"Port: {app.port}")

**Key Mapping Rules**:

- ``HOST`` → ``host`` (lowercase, matches model field)
- ``PORT`` → ``port`` (lowercase, matches model field)
- ``UNRELATED_VAR`` → ignored (not in model)
- For nested keys: ``DB__HOST`` → ``db.host`` (``__`` becomes ``.``)

Step 5: Command-Line Argument Format
-------------------------------------

Command-line arguments use kebab-case and are converted to dot notation:

.. code-block:: python
   :linenos:

   import sys
   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="127.0.0.1")
       port: int = field(default=8000)
       debug: bool = field(default=False)

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
           sources.CLI(),  # Model auto-injected, only parses model fields
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
   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="127.0.0.1")
       port: int = field(default=8000)
       debug: bool = field(default=False)
       app_name: str = field(default="MyApp")

   def main():
       # Set environment variables (no prefix needed)
       os.environ["PORT"] = "9000"
       os.environ["DEBUG"] = "true"

       # Simulate CLI arguments
       sys.argv = ["app.py", "--host", "0.0.0.0"]

       # Create configuration with multiple sources
       cfg = Config(
           model=AppConfig,
           sources=[
               sources.Env(),         # Priority 1 (overrides defaults)
               sources.CLI(),         # Priority 2 (highest, overrides env)
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
   :emphasize-lines: 5-6

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.CLI(),  # CLI first!
           sources.Env(),   # Env will override CLI
       ],
   )
   # CLI arguments will be overridden by env vars - probably not what you want!

**Solution**: Always put sources in priority order (lowest to highest):
Env → CLI (defaults are automatically applied first).

**Pitfall 2: Environment variables not matching model fields**

.. code-block:: python
   :emphasize-lines: 2, 7

   os.environ["MY_HOST"] = "0.0.0.0"  # Doesn't match model field

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Only loads fields defined in model
       ],
   )
   # MY_HOST won't be loaded because it doesn't match any model field

**Solution**: Use environment variable names that match model field names (normalized to uppercase). For ``host`` field, use ``HOST`` environment variable.

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

1. **Model defaults are automatic**: No need to include ``sources.Defaults``
2. **All sources filter by model**: Only model-defined fields are loaded
3. **Order sources by priority**: Env → CLI (defaults applied first automatically)
4. **Use Config.from_model() for common setups**: Reduces boilerplate
5. **Fields are automatically determined**: Use ``Optional[T]`` type annotation or default values for optional fields

Next Steps
----------

Now that you understand multiple sources, let's learn about :doc:`nested_configuration`
to handle complex configuration structures.

