Configuration Export
====================

Varlord provides functionality to export the current configuration to various file formats,
making it easy to save, share, or version control your configuration.

Basic Usage
-----------

After loading your configuration, you can export it to different formats:

.. code-block:: python
   :linenos:

   from varlord import Config, sources
   from dataclasses import dataclass, field

   @dataclass
   class AppConfig:
       api_key: str = field()
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)

   # Create and load config
   cfg = Config(
       model=AppConfig,
       sources=[sources.Env(), sources.CLI()],
   )
   cfg.handle_cli_commands()
   config = cfg.load()

   # Export to different formats
   cfg.dump_json("config.json")
   cfg.dump_yaml("config.yaml")
   cfg.dump_toml("config.toml")
   cfg.dump_env(".env", prefix="APP_")

Export Methods
--------------

Get Configuration as Dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``to_dict()`` to get the current configuration as a dictionary without writing to a file:

.. code-block:: python

   config_dict = cfg.to_dict()
   print(config_dict["host"])
   print(config_dict["port"])

This is useful when you need to programmatically access configuration values or pass them to other functions.

JSON Export
~~~~~~~~~~~

Export configuration to JSON format:

.. code-block:: python

   cfg.dump_json("config.json", indent=4)

**Parameters:**
- ``file_path``: Path to output JSON file (str or Path)
- ``validate``: Whether to validate required fields before export (default: True)
- ``indent``: JSON indentation level (default: 2)

**Example output:**

.. code-block:: json

   {
     "api_key": "sk-...",
     "host": "0.0.0.0",
     "port": 8000
   }

YAML Export
~~~~~~~~~~~

Export configuration to YAML format:

.. code-block:: python

   cfg.dump_yaml("config.yaml", default_flow_style=False)

**Parameters:**
- ``file_path``: Path to output YAML file (str or Path)
- ``validate``: Whether to validate required fields before export (default: True)
- ``default_flow_style``: Use flow style (default: False, uses block style)

**Dependencies:** Requires ``pyyaml`` package. Install with: ``pip install pyyaml``

**Example output:**

.. code-block:: yaml

   api_key: sk-...
   host: 0.0.0.0
   port: 8000

TOML Export
~~~~~~~~~~~

Export configuration to TOML format:

.. code-block:: python

   cfg.dump_toml("config.toml")

**Parameters:**
- ``file_path``: Path to output TOML file (str or Path)
- ``validate``: Whether to validate required fields before export (default: True)

**Dependencies:** Requires ``tomli-w`` package. Install with: ``pip install tomli-w``

**Example output:**

.. code-block:: toml

   api_key = "sk-..."
   host = "0.0.0.0"
   port = 8000

.env Export
~~~~~~~~~~~

Export configuration to .env file format (for environment variables):

.. code-block:: python

   cfg.dump_env(
       ".env",
       prefix="APP_",
       uppercase=True,
       nested_separator="__"
   )

**Parameters:**
- ``file_path``: Path to output .env file (str or Path)
- ``validate``: Whether to validate required fields before export (default: True)
- ``prefix``: Optional prefix for all environment variable names (e.g., ``APP_``)
- ``uppercase``: Convert keys to uppercase (default: True)
- ``nested_separator``: Separator for nested keys (default: "__")

**Example output:**

.. code-block:: text

   APP_API_KEY=sk-...
   APP_HOST=0.0.0.0
   APP_PORT=8000

Nested Configuration
--------------------

All export methods correctly handle nested dataclass structures:

.. code-block:: python
   :linenos:

   @dataclass
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)

   @dataclass
   class AppConfig:
       api_key: str = field()
       db: DBConfig = field(default_factory=lambda: DBConfig())

   cfg = Config(model=AppConfig, sources=[...])
   cfg.dump_json("config.json")

**JSON output:**

.. code-block:: json

   {
     "api_key": "sk-...",
     "db": {
       "host": "localhost",
       "port": 5432
     }
   }

**YAML output:**

.. code-block:: yaml

   api_key: sk-...
   db:
     host: localhost
     port: 5432

**TOML output:**

.. code-block:: toml

   api_key = "sk-..."
   [db]
   host = "localhost"
   port = 5432

**.env output (with nested separator):**

.. code-block:: text

   API_KEY=sk-...
   DB__HOST=localhost
   DB__PORT=5432

Use Cases
---------

Configuration Backup
~~~~~~~~~~~~~~~~~~~~~

Export your current configuration to save a snapshot:

.. code-block:: python

   # Save current config as backup
   cfg.dump_yaml(f"config_backup_{datetime.now().isoformat()}.yaml")

Configuration Templates
~~~~~~~~~~~~~~~~~~~~~~~~

Generate configuration templates for users:

.. code-block:: python

   # Create template with defaults
   template_cfg = Config(model=AppConfig, sources=[])
   template_cfg.dump_json("config.template.json")

Environment Setup
~~~~~~~~~~~~~~~~~

Generate .env files for different environments:

.. code-block:: python

   # Development environment
   cfg.dump_env(".env.development", prefix="APP_DEV_")

   # Production environment
   cfg.dump_env(".env.production", prefix="APP_PROD_")

Configuration Sharing
~~~~~~~~~~~~~~~~~~~~~

Export configuration to share with team members or for documentation:

.. code-block:: python

   # Export to YAML for documentation
   cfg.dump_yaml("docs/example_config.yaml")

Dependencies
------------

- **JSON**: Built-in (no extra dependencies required)
- **YAML**: Requires ``pyyaml`` (``pip install pyyaml``)
- **TOML**: Requires ``tomli-w`` (``pip install tomli-w``)
- **.env**: Built-in (no extra dependencies required)

If a required dependency is missing, the export method will raise an ``ImportError`` with a clear message indicating which package needs to be installed.

Best Practices
--------------

1. **Validate before export**: By default, all export methods validate required fields. Set ``validate=False`` only if you're intentionally exporting incomplete configurations.

2. **Use appropriate formats**: 
   - Use JSON for machine-readable configs and APIs
   - Use YAML for human-readable configs and documentation
   - Use TOML for Python projects (pyproject.toml style)
   - Use .env for environment variable exports

3. **Handle nested structures**: All export methods automatically handle nested dataclasses, so you don't need to manually flatten structures.

4. **Use prefixes for .env**: When exporting to .env format, use prefixes to avoid conflicts with other environment variables.

5. **Version control**: Consider adding exported config files to ``.gitignore`` if they contain sensitive information like API keys.
