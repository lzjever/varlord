Global Configuration Registry
==============================

The global configuration registry provides optional access to configuration objects
without needing to pass them around your application. This is useful for
application-wide configuration that is initialized once at startup.

Overview
--------

The global configuration registry allows you to:

- Register configuration objects once at application startup
- Access configuration anywhere in your application without passing it as a parameter
- Support multiple named configurations (e.g., "app", "database", "cache")
- Use thread-local storage for thread safety

This is an **optional feature**. You can still use ``Config`` and ``ConfigStore``
normally without global registration.

Functions
---------

.. function:: set_global_config(config, name="default", overwrite=True)

   Register a configuration object globally.

   :param config: Config or ConfigStore instance to register
   :type config: Config | ConfigStore
   :param name: Name for the configuration (default: "default")
   :type name: str
   :param overwrite: Whether to overwrite existing configuration with same name (default: True)
   :type overwrite: bool
   :raises ValueError: If name already exists and overwrite=False
   :raises TypeError: If config is not a Config or ConfigStore instance

   Example:

   .. code-block:: python

      from varlord import Config, sources
      from varlord.global_config import set_global_config

      cfg = Config(
          model=AppConfig,
          sources=[sources.Env(), sources.CLI()],
      )
      set_global_config(cfg)

      # Or with a custom name
      set_global_config(cfg, name="app")

   Note:
      Configurations are stored per-thread (thread-local). This allows different
      threads to have different configurations if needed.

.. function:: get_global_config(name="default")

   Get a globally registered configuration object.

   :param name: Name of the configuration (default: "default")
   :type name: str
   :returns: Config or ConfigStore instance
   :raises KeyError: If configuration with given name is not found

   Example:

   .. code-block:: python

      from varlord.global_config import get_global_config

      # Get default configuration
      config = get_global_config()
      app = config.load()

      # Get named configuration
      app_config = get_global_config(name="app")
      db_config = get_global_config(name="database")

   Note:
      Returns the same instance that was registered. For ``Config`` instances,
      you still need to call ``load()`` or ``load_store()``. For ``ConfigStore``
      instances, you can directly call ``get()``.

.. function:: has_global_config(name="default")

   Check if a global configuration exists.

   :param name: Name of the configuration (default: "default")
   :type name: str
   :returns: True if configuration exists, False otherwise

   Example:

   .. code-block:: python

      from varlord.global_config import has_global_config, get_global_config

      if has_global_config():
          config = get_global_config()
          app = config.load()
      else:
          raise RuntimeError("Configuration not initialized")

.. function:: remove_global_config(name="default")

   Remove a globally registered configuration.

   :param name: Name of the configuration to remove (default: "default")
   :type name: str
   :raises KeyError: If configuration with given name is not found

   Example:

   .. code-block:: python

      from varlord.global_config import remove_global_config

      remove_global_config()
      # Or remove a named configuration
      remove_global_config(name="app")

.. function:: clear_global_configs()

   Clear all globally registered configurations.

   Example:

   .. code-block:: python

      from varlord.global_config import clear_global_configs

      clear_global_configs()

.. function:: list_global_configs()

   List all registered global configuration names.

   :returns: List of configuration names

   Example:

   .. code-block:: python

      from varlord.global_config import list_global_configs, set_global_config

      set_global_config(cfg1, name="app")
      set_global_config(cfg2, name="database")
      names = list_global_configs()
      # Returns: ['app', 'database']

Usage Patterns
--------------

**Pattern 1: Simple Application**

.. code-block:: python

   # At startup
   from varlord import Config, sources
   from varlord.global_config import set_global_config

   cfg = Config(model=AppConfig, sources=[sources.Env(), sources.CLI()])
   cfg.handle_cli_commands()
   set_global_config(cfg)

   # Anywhere in your code
   from varlord.global_config import get_global_config

   config = get_global_config()
   app = config.load()

**Pattern 2: Named Configurations**

.. code-block:: python

   # At startup
   app_cfg = Config(model=AppConfig, sources=[...])
   db_cfg = Config(model=DatabaseConfig, sources=[...])

   set_global_config(app_cfg, name="app")
   set_global_config(db_cfg, name="database")

   # In your code
   app_config = get_global_config(name="app").load()
   db_config = get_global_config(name="database").load()

**Pattern 3: ConfigStore for Dynamic Updates**

.. code-block:: python

   # At startup
   cfg = Config(model=AppConfig, sources=[...])
   store = cfg.load_store()  # Enable dynamic updates
   set_global_config(store, name="app")

   # In your code
   store = get_global_config(name="app")
   current = store.get()  # Thread-safe, always current

Thread Safety
-------------

The global configuration registry uses thread-local storage. This means:

- Each thread has its own registry
- Configurations set in one thread are not visible to other threads
- This is usually what you want for most applications

If you need to share configuration across threads, consider:

- Passing the config object explicitly as a parameter
- Using a shared ``ConfigStore`` instance (which is thread-safe)
- Using a different mechanism for cross-thread communication

Best Practices
--------------

1. **Initialize Once**: Call ``set_global_config()`` once at application startup

2. **Use Named Configurations**: Use descriptive names for multiple configurations

3. **Check Before Use**: Use ``has_global_config()`` if configuration might not be initialized

4. **Handle Errors**: Always handle ``KeyError`` when getting configurations

5. **Clean Up**: Use ``clear_global_configs()`` in tests to avoid state leakage

Example: Complete Application Setup
------------------------------------

.. code-block:: python

   """config/setup.py"""

   from varlord import Config, sources
   from varlord.global_config import set_global_config
   from .models import AppConfig

   def setup_config():
       """Initialize application configuration."""
       cfg = Config(
           model=AppConfig,
           sources=[
               sources.YAML("config/app.yaml"),
               sources.Env(),
               sources.DotEnv(".env"),
               sources.CLI(),
           ],
       )
       cfg.handle_cli_commands()
       set_global_config(cfg, name="app")
       return cfg

   """src/services/database.py"""

   from varlord.global_config import get_global_config

   def get_db_connection():
       """Get database connection using global configuration."""
       config = get_global_config(name="app")
       app_config = config.load()
       # Use app_config.database.host, etc.
       return create_connection(app_config.database)

See Also
--------

- :doc:`../user_guide/best_practices` for real-world usage patterns
- :doc:`config` for Config class documentation
- :doc:`store` for ConfigStore class documentation

