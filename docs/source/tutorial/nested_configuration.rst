Nested Configuration
====================

In this tutorial, you'll learn how to work with nested configuration structures,
mapping flat keys to nested dataclass hierarchies.

Learning Objectives
-------------------

By the end of this tutorial, you'll be able to:

- Define nested configuration models
- Use dot notation for nested keys
- Load nested configuration from multiple sources

Step 1: Defining Nested Models
--------------------------------

Let's create a configuration with nested structures:

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config

   @dataclass(frozen=True)
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)
       database: str = field(default="mydb")

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)
       db: DBConfig = field(default_factory=lambda: DBConfig())  # Nested configuration

   # Initialize with defaults (automatic)
   cfg = Config(
       model=AppConfig,
       sources=[],  # Defaults are automatically applied
   )

   app = cfg.load()
   print(f"App: {app.host}:{app.port}")
   print(f"DB: {app.db.host}:{app.db.port}/{app.db.database}")

**Expected Output**:

.. code-block:: text

   App: 0.0.0.0:8000
   DB: localhost:5432/mydb

Step 2: Using Default Factory for Nested Objects
-------------------------------------------------

To provide default nested objects, use ``field(default_factory=...)``:

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config

   @dataclass(frozen=True)
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)
       database: str = field(default="mydb")

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)
       db: DBConfig = field(default_factory=lambda: DBConfig())

   cfg = Config(
       model=AppConfig,
       sources=[],  # Defaults are automatically applied
   )

   app = cfg.load()
   print(f"App: {app.host}:{app.port}")
   print(f"DB: {app.db.host}:{app.db.port}/{app.db.database}")

**Expected Output**:

.. code-block:: text

   App: 0.0.0.0:8000
   DB: localhost:5432/mydb

**Key Points**:

- Use ``field(default_factory=...)`` to create default nested objects
- The factory function is called to create a new instance each time

Step 3: Loading Nested Configuration from Environment
------------------------------------------------------

Environment variables use double underscore (``__``) as a separator for nested
keys:

.. code-block:: python
   :linenos:

   import os
   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)
       database: str = field(default="mydb")

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)
       db: DBConfig = field(default_factory=lambda: DBConfig())

   # Set nested environment variables (no prefix needed - filtered by model)
   os.environ["DB__HOST"] = "db.example.com"
   os.environ["DB__PORT"] = "3306"
   os.environ["DB__DATABASE"] = "production"

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Only loads DB__HOST, DB__PORT, DB__DATABASE (filtered by model)
       ],
   )

   app = cfg.load()
   print(f"App: {app.host}:{app.port}")
   print(f"DB: {app.db.host}:{app.db.port}/{app.db.database}")

**Expected Output**:

.. code-block:: text

   App: 0.0.0.0:8000
   DB: db.example.com:3306/production

**Key Mapping**:

- ``DB__HOST`` → ``db.host``
- ``DB__PORT`` → ``db.port``
- ``DB__DATABASE`` → ``db.database``

The double underscore (``__``) is converted to a dot (``.``) for nested
structure mapping. Only environment variables that match model fields are loaded.

Step 4: Loading Nested Configuration from CLI
-----------------------------------------------

Command-line arguments use hyphens for nested keys:

.. code-block:: python
   :linenos:

   import sys
   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)
       db: DBConfig = field(default_factory=lambda: DBConfig())

   # Command-line arguments for nested fields
   sys.argv = [
       "app.py",
       "--db-host", "db.example.com",
       "--db-port", "3306",
   ]

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.CLI(),  # Model auto-injected, only parses model fields
       ],
   )

   app = cfg.load()
   print(f"DB: {app.db.host}:{app.db.port}")

**Expected Output**:

.. code-block:: text

   DB: db.example.com:3306

**CLI Nested Key Format**:

- ``--db-host`` → ``db.host``
- ``--db-port`` → ``db.port``

Hyphens are converted to dots for nested structure mapping.

Step 5: Deeply Nested Configuration
------------------------------------

You can nest multiple levels:

.. code-block:: python
   :linenos:

   import os
   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class CacheConfig:
       enabled: bool = field(default=False)
       ttl: int = field(default=3600)

   @dataclass(frozen=True)
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)
       cache: CacheConfig = field(default_factory=lambda: CacheConfig())

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       db: DBConfig = field(default_factory=lambda: DBConfig())

   # Set deeply nested environment variables (no prefix needed)
   os.environ["DB__CACHE__ENABLED"] = "true"
   os.environ["DB__CACHE__TTL"] = "7200"

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Only loads variables matching model fields
       ],
   )

   app = cfg.load()
   print(f"DB Cache Enabled: {app.db.cache.enabled}")
   print(f"DB Cache TTL: {app.db.cache.ttl}")

**Expected Output**:

.. code-block:: text

   DB Cache Enabled: True
   DB Cache TTL: 7200

**Deep Nesting Mapping**:

- ``DB__CACHE__ENABLED`` → ``db.cache.enabled``
- ``DB__CACHE__TTL`` → ``db.cache.ttl``

Step 6: Complete Example
------------------------

Here's a complete example with multiple nested structures:

.. code-block:: python
   :name: nested_configuration_complete
   :linenos:

   import os
   import sys
   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)
       database: str = field(default="mydb")

   @dataclass(frozen=True)
   class RedisConfig:
       host: str = field(default="localhost")
       port: int = field(default=6379)

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)
       db: DBConfig = field(default_factory=lambda: DBConfig())
       redis: RedisConfig = field(default_factory=lambda: RedisConfig())

   def main():
       # Set environment variables (no prefix needed)
       os.environ["DB__HOST"] = "db.example.com"
       os.environ["DB__PORT"] = "3306"
       os.environ["REDIS__HOST"] = "redis.example.com"

       # Set CLI arguments
       sys.argv = ["app.py", "--port", "9000"]

       cfg = Config(
           model=AppConfig,
           sources=[
               sources.Env(),  # Priority 1 (overrides defaults)
               sources.CLI(),  # Priority 2 (highest, overrides env)
           ],
       )

       app = cfg.load()

       print("Configuration loaded:")
       print(f"  App: {app.host}:{app.port}")
       print(f"  DB: {app.db.host}:{app.db.port}/{app.db.database}")
       print(f"  Redis: {app.redis.host}:{app.redis.port}")

   if __name__ == "__main__":
       main()

**Expected Output**:

.. code-block:: text

   Configuration loaded:
     App: 0.0.0.0:9000
     DB: db.example.com:3306/mydb
     Redis: redis.example.com:6379

Common Pitfalls
---------------

**Pitfall 1: Forgetting default_factory for nested objects**

.. code-block:: python
   :emphasize-lines: 8

   @dataclass(frozen=True)
   class AppConfig:
       host: str = "0.0.0.0"
       db: DBConfig = None  # This will be None!

   # If no source provides db values, app.db will be None
   app = cfg.load()
   print(app.db.host)  # AttributeError: 'NoneType' object has no attribute 'host'

**Solution**: Use ``field(default_factory=lambda: DBConfig())`` to provide
default nested objects.

**Pitfall 2: Wrong separator in environment variables**

.. code-block:: python
   :emphasize-lines: 2, 8

   os.environ["DB_HOST"] = "db.example.com"  # Single underscore

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Looking for DB__HOST (double underscore)
       ],
   )
   # DB_HOST won't be recognized as nested key (becomes flat key "db_host")

**Solution**: Use double underscore (``__``) as separator for nested keys in
environment variables. For ``db.host``, use ``DB__HOST``.

**Pitfall 3: Mixing flat and nested keys incorrectly**

.. code-block:: python
   :emphasize-lines: 2

   os.environ["DB_HOST"] = "db.example.com"  # This becomes flat key "db_host"

   # If your model has db.host (nested), this won't map correctly
   # Use DB__HOST instead

**Solution**: Always use the correct separator (``__`` for env, ``-`` for CLI)
for nested keys.

Best Practices
--------------

1. **Use default_factory for nested objects**: Ensures defaults are always available
2. **Use consistent naming**: Keep nested structure consistent across sources
3. **Document your structure**: Comment complex nested configurations
4. **Test with different sources**: Verify nested keys work from all sources

Next Steps
----------

Now that you understand nested configuration, let's add :doc:`validation` to
ensure configuration values are correct.

