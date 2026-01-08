Best Practices for Real-World Applications
===========================================

This guide shows you how to structure and use Varlord in real-world applications,
including file organization, initialization patterns, and using the global configuration
registry.

Project Structure
-----------------

Here's a recommended project structure for a real-world application using Varlord:

.. code-block:: text

   myapp/
   ├── config/
   │   ├── __init__.py          # Export config models and setup function
   │   ├── models.py            # Configuration models (dataclasses)
   │   └── setup.py             # Configuration initialization
   ├── src/
   │   ├── __init__.py
   │   ├── api/
   │   │   ├── __init__.py
   │   │   └── routes.py        # Uses global config
   │   ├── services/
   │   │   ├── __init__.py
   │   │   └── database.py      # Uses global config
   │   └── main.py              # Application entry point
   ├── config/
   │   ├── app.yaml             # Application defaults
   │   └── production.yaml      # Production overrides
   ├── .env.example             # Example environment variables
   ├── .env                     # Local development (gitignored)
   └── requirements.txt

Configuration Models
--------------------

Define your configuration models in ``config/models.py``:

.. code-block:: python
   :linenos:

   """Configuration models for the application."""

   from dataclasses import dataclass, field
   from pathlib import Path
   from typing import Optional

   @dataclass(frozen=True)
   class DatabaseConfig:
       """Database configuration."""
       password: str = field(metadata={"description": "Database password"})
       host: str = field(default="localhost", metadata={"description": "Database host"})
       port: int = field(default=5432, metadata={"description": "Database port"})
       name: str = field(default="myapp", metadata={"description": "Database name"})
       user: str = field(default="postgres", metadata={"description": "Database user"})
       pool_size: int = field(default=10, metadata={"description": "Connection pool size"})

   @dataclass(frozen=True)
   class RedisConfig:
       """Redis configuration."""
       host: str = field(default="localhost", metadata={"description": "Redis host"})
       port: int = field(default=6379, metadata={"description": "Redis port"})
       db: int = field(default=0, metadata={"description": "Redis database number"})
       password: Optional[str] = field(default=None, metadata={"description": "Redis password"})

   @dataclass(frozen=True)
   class APIConfig:
       """API server configuration."""
       host: str = field(default="0.0.0.0", metadata={"description": "API server host"})
       port: int = field(default=8000, metadata={"description": "API server port"})
       debug: bool = field(default=False, metadata={"description": "Enable debug mode"})
       cors_origins: list[str] = field(
           default_factory=lambda: ["http://localhost:3000"],
           metadata={"description": "Allowed CORS origins"}
       )

   @dataclass(frozen=True)
   class AppConfig:
       """Main application configuration."""
       # Required fields first (no defaults)
       secret_key: str = field(metadata={"description": "Secret key for encryption"})
       
       # Nested configurations
       database: DatabaseConfig = field(default_factory=DatabaseConfig)
       redis: RedisConfig = field(default_factory=RedisConfig)
       api: APIConfig = field(default_factory=APIConfig)
       
       # Application-level settings (with defaults)
       app_name: str = field(default="MyApp", metadata={"description": "Application name"})
       log_level: str = field(default="INFO", metadata={"description": "Logging level"})
       environment: str = field(default="development", metadata={"description": "Environment name"})

Configuration Setup
-------------------

Create a setup function in ``config/setup.py``:

.. code-block:: python
   :linenos:

   """Configuration setup and initialization."""

   import os
   from pathlib import Path

   from varlord import Config, sources
   from varlord.global_config import set_global_config

   from .models import AppConfig

   def setup_config() -> Config:
       """Initialize and register application configuration.
       
       This function should be called once at application startup.
       
       Returns:
           Config instance (also registered globally)
       """
       # Determine environment
       env = os.getenv("ENVIRONMENT", "development")
       app_dir = Path(__file__).parent.parent
       
       # Build sources list with priority order
       # Priority: CLI > Env > .env > User Config > App Config > Defaults
       config_sources = [
           # System/application defaults (lowest priority)
           sources.YAML(str(app_dir / "config" / "app.yaml")),
           
           # Environment-specific overrides
           sources.YAML(str(app_dir / "config" / f"{env}.yaml")),
           
           # User-specific configuration (if exists)
           sources.YAML(Path.home() / ".config" / "myapp" / "config.yaml"),
           
           # Environment variables (common in containers/CI)
           sources.Env(),
           
           # Local development .env file
           sources.DotEnv(str(app_dir / ".env")),
           
           # Command-line arguments (highest priority, for debugging/overrides)
           sources.CLI(),
       ]
       
       # Create configuration
       cfg = Config(
           model=AppConfig,
           sources=config_sources,
       )
       
       # Handle CLI commands (--help, --check-variables)
       cfg.handle_cli_commands()
       
       # Register globally for easy access throughout the application
       set_global_config(cfg, name="app")
       
       return cfg

   def get_config():
       """Get the application configuration (convenience function).
       
       Returns:
           Loaded configuration object
       """
       from varlord.global_config import get_global_config
       
       config = get_global_config(name="app")
       return config.load()

Application Entry Point
-----------------------

Initialize configuration in your main application file:

.. code-block:: python
   :linenos:

   """Application entry point."""

   import logging
   import sys

   from varlord import set_log_level
   from config.setup import setup_config, get_config

   def main():
       """Main application entry point."""
       # Step 1: Setup logging (optional, but recommended)
       logging.basicConfig(
           level=logging.INFO,
           format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
       )
       set_log_level(logging.DEBUG)  # Enable varlord debug logging
       
       # Step 2: Initialize configuration (once at startup)
       try:
           cfg = setup_config()
           app_config = get_config()
       except Exception as e:
           print(f"❌ Failed to load configuration: {e}")
           print("\n💡 Tips:")
           print("   - Check required fields: python main.py --check-variables")
           print("   - See help: python main.py --help")
           sys.exit(1)
       
       # Step 3: Validate configuration (optional, but recommended)
       if app_config.environment == "production" and app_config.api.debug:
           print("⚠️  Warning: Debug mode is enabled in production!")
           sys.exit(1)
       
       # Step 4: Start your application
       print(f"✅ Starting {app_config.app_name} in {app_config.environment} mode")
       print(f"   API: http://{app_config.api.host}:{app_config.api.port}")
       print(f"   Database: {app_config.database.host}:{app_config.database.port}")
       
       # Your application code here
       start_server(app_config)

   if __name__ == "__main__":
       main()

Using Configuration in Business Code
-------------------------------------

Once configuration is initialized, you can access it anywhere in your application
using the global registry:

**Option 1: Using Global Config (Recommended)**

.. code-block:: python
   :linenos:

   """API routes module."""

   from varlord.global_config import get_global_config

   def get_api_routes():
       """Get API routes configuration."""
       config = get_global_config(name="app")
       app_config = config.load()
       
       return {
           "host": app_config.api.host,
           "port": app_config.api.port,
           "debug": app_config.api.debug,
           "cors_origins": app_config.api.cors_origins,
       }

   def setup_database():
       """Setup database connection."""
       config = get_global_config(name="app")
       app_config = config.load()
       
       db_config = app_config.database
       # Use db_config.host, db_config.port, etc.
       return create_db_connection(db_config)

**Option 2: Using ConfigStore (For Dynamic Updates)**

If you need dynamic configuration updates, use ``ConfigStore``:

.. code-block:: python
   :linenos:

   """Service module with dynamic configuration."""

   from varlord.global_config import get_global_config

   def setup_service_with_watch():
       """Setup service with dynamic configuration updates."""
       config = get_global_config(name="app")
       
       # Load as ConfigStore for dynamic updates
       store = config.load_store()
       
       # Subscribe to configuration changes
       def on_config_change(new_config, diff):
           print(f"Configuration updated: {diff}")
           # Update service behavior based on new config
           if "api.port" in diff.modified:
               print(f"Port changed to {new_config.api.port}")
       
       store.subscribe(on_config_change)
       
       # Get current configuration (thread-safe)
       current_config = store.get()
       return current_config

**Option 3: Dependency Injection (Alternative Pattern)**

If you prefer explicit dependency injection, you can pass configuration as a parameter:

.. code-block:: python
   :linenos:

   """Service module with dependency injection."""

   def process_data(config: AppConfig):
       """Process data using configuration."""
       # Use config.database, config.redis, etc.
       pass

   # In your main code:
   app_config = get_config()
   process_data(app_config)

Complete Example: Web Application
----------------------------------

Here's a complete example showing a web application structure:

**config/__init__.py:**

.. code-block:: python

   """Configuration package."""

   from .models import AppConfig, DatabaseConfig, RedisConfig, APIConfig
   from .setup import setup_config, get_config

   __all__ = [
       "AppConfig",
       "DatabaseConfig",
       "RedisConfig",
       "APIConfig",
       "setup_config",
       "get_config",
   ]

**src/services/database.py:**

.. code-block:: python
   :linenos:

   """Database service."""

   from varlord.global_config import get_global_config

   def get_db_connection():
       """Get database connection using global configuration."""
       config = get_global_config(name="app")
       app_config = config.load()
       
       db = app_config.database
       return create_connection(
           host=db.host,
           port=db.port,
           database=db.name,
           user=db.user,
           password=db.password,
           pool_size=db.pool_size,
       )

**src/api/routes.py:**

.. code-block:: python
   :linenos:

   """API routes."""

   from varlord.global_config import get_global_config

   def create_app():
       """Create Flask/FastAPI application."""
       config = get_global_config(name="app")
       app_config = config.load()
       
       # Create app with configuration
       app = create_web_app(
           host=app_config.api.host,
           port=app_config.api.port,
           debug=app_config.api.debug,
           cors_origins=app_config.api.cors_origins,
       )
       
       return app

**src/main.py:**

.. code-block:: python
   :linenos:

   """Main application entry point."""

   import sys
   from config.setup import setup_config, get_config
   from src.api.routes import create_app
   from src.services.database import get_db_connection

   def main():
       """Main entry point."""
       # Initialize configuration
       try:
           setup_config()
           app_config = get_config()
       except Exception as e:
           print(f"Configuration error: {e}")
           sys.exit(1)
       
       # Initialize services
       db = get_db_connection()
       
       # Create and start application
       app = create_app()
       app.run(
           host=app_config.api.host,
           port=app_config.api.port,
           debug=app_config.api.debug,
       )

   if __name__ == "__main__":
       main()

Configuration Files
-------------------

**config/app.yaml** (Application defaults):

.. code-block:: yaml

   app_name: MyApp
   environment: development
   log_level: INFO
   
   database:
     host: localhost
     port: 5432
     name: myapp
     user: postgres
     pool_size: 10
   
   redis:
     host: localhost
     port: 6379
     db: 0
   
   api:
     host: 0.0.0.0
     port: 8000
     debug: false
     cors_origins:
       - http://localhost:3000

**config/production.yaml** (Production overrides):

.. code-block:: yaml

   environment: production
   log_level: WARNING
   
   api:
     debug: false
     cors_origins:
       - https://myapp.com

**.env.example** (Example environment variables):

.. code-block:: text

   # Required
   SECRET_KEY=your-secret-key-here
   DATABASE__PASSWORD=your-database-password
   
   # Optional
   ENVIRONMENT=development
   API__PORT=8000
   DATABASE__HOST=localhost
   REDIS__HOST=localhost

Best Practices Summary
----------------------

1. **Organize Configuration Models**
   - Group related settings into nested dataclasses
   - Use descriptive field names and metadata
   - Provide sensible defaults

2. **Initialize Once at Startup**
   - Call ``setup_config()`` in your main entry point
   - Register globally using ``set_global_config()``
   - Handle errors gracefully with clear messages

3. **Use Global Registry**
   - Access configuration anywhere with ``get_global_config()``
   - No need to pass config objects around
   - Thread-safe and efficient

4. **Support Multiple Environments**
   - Use different config files for dev/staging/prod
   - Override with environment variables in containers
   - Use CLI arguments for debugging

5. **Validate Configuration**
   - Use ``--check-variables`` to diagnose issues
   - Add validation in ``__post_init__`` for complex rules
   - Fail fast with clear error messages

6. **Document Configuration**
   - Use field metadata for descriptions
   - Provide ``.env.example`` file
   - Document configuration files and their purpose

7. **Test Configuration Loading**
   - Test with different source combinations
   - Test validation and error handling
   - Test in different environments

Common Patterns
---------------

**Pattern 1: Simple Application**

.. code-block:: python

   # config/setup.py
   def setup_config():
       cfg = Config(
           model=AppConfig,
           sources=[sources.Env(), sources.CLI()],
       )
       cfg.handle_cli_commands()
       set_global_config(cfg)
       return cfg

**Pattern 2: Multi-Environment Application**

.. code-block:: python

   # config/setup.py
   def setup_config():
       env = os.getenv("ENVIRONMENT", "development")
       cfg = Config(
           model=AppConfig,
           sources=[
               sources.YAML(f"config/{env}.yaml"),
               sources.Env(),
               sources.CLI(),
           ],
       )
       cfg.handle_cli_commands()
       set_global_config(cfg)
       return cfg

**Pattern 3: Application with Dynamic Updates**

.. code-block:: python

   # config/setup.py
   def setup_config():
       cfg = Config(
           model=AppConfig,
           sources=[
               sources.Env(),
               sources.Etcd(host="etcd.example.com", watch=True),
           ],
       )
       cfg.handle_cli_commands()
       
       # Use ConfigStore for dynamic updates
       store = cfg.load_store()
       set_global_config(store, name="app")
       return store

**Pattern 4: Multiple Named Configurations**

.. code-block:: python

   # config/setup.py
   def setup_config():
       # App configuration
       app_cfg = Config(model=AppConfig, sources=[...])
       set_global_config(app_cfg, name="app")
       
       # Database configuration
       db_cfg = Config(model=DatabaseConfig, sources=[...])
       set_global_config(db_cfg, name="database")
       
       # Use in code:
       # app_config = get_global_config(name="app").load()
       # db_config = get_global_config(name="database").load()

Troubleshooting
---------------

**Problem: Configuration not found**

.. code-block:: python

   from varlord.global_config import get_global_config, has_global_config

   if has_global_config(name="app"):
       config = get_global_config(name="app")
   else:
       raise RuntimeError("Configuration not initialized. Call setup_config() first.")

**Problem: Configuration changes not reflected**

If using ``Config.load()``, configuration is loaded once. For dynamic updates, use ``ConfigStore``:

.. code-block:: python

   # Instead of:
   config = get_global_config(name="app")
   app = config.load()  # Static, loaded once

   # Use:
   store = get_global_config(name="app")
   app = store.get()  # Dynamic, always current

**Problem: Thread safety concerns**

Global configuration uses thread-local storage, so each thread has its own registry.
This is usually what you want, but if you need to share configuration across threads,
pass the config object explicitly or use a shared ConfigStore instance.

Next Steps
----------

- See :doc:`../tutorial/getting_started` for a step-by-step tutorial
- See :doc:`dynamic_updates` for dynamic configuration updates
- See :doc:`validation` for configuration validation
- See :doc:`../api_reference/global_config` for API reference

