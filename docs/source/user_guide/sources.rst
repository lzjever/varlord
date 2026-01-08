Configuration Sources
=====================

Varlord supports multiple configuration sources, each implementing the ``Source`` interface.

Defaults Source
---------------

Model defaults are automatically applied as the base layer. You no longer need to explicitly include ``sources.Defaults`` in your sources list.

**Note**: The ``Defaults`` source is now internal. Model defaults are automatically extracted and applied first, before any user-provided sources.

Environment Variables
---------------------

Loads from environment variables, filtered by model fields:

.. code-block:: python

   # Recommended: Model is auto-injected by Config
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Model auto-injected, no need to pass model parameter
       ],
   )

   # With prefix filtering (useful for containerized deployments)
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(prefix="APP__"),  # Only loads variables starting with APP__
       ],
   )

   # Advanced: Explicit model (when using source independently)
   source = sources.Env()  # Only needed if using source outside Config
   # Only loads environment variables that match model fields
   # HOST -> host, PORT -> port, etc.
   # Converts DB__HOST to db.host (nested keys)

**Parameters**:
- ``model`` (optional): Model class for filtering. Auto-injected by ``Config`` if not provided.
- ``prefix`` (optional): Prefix for filtering environment variables. Only variables starting with this prefix are loaded.

  - Case-insensitive matching (e.g., ``titan__`` matches ``TITAN__``)
  - Prefix is automatically removed before key normalization
  - Useful for isolating application-specific environment variables in containerized deployments
  - Example: ``sources.Env(prefix="TITAN__")`` will only load ``TITAN__AI__COMPLETION__MODEL``, not ``AI__COMPLETION__MODEL``

- ``source_id`` (optional): Custom source identifier for priority policies

**Important**: 
- When used in ``Config``, model is automatically injected - no need to pass ``model`` parameter.
- Only pass ``model`` explicitly if using the source independently.
- If ``prefix`` is not provided, all environment variables matching model fields are loaded.
- Prefix matching is case-insensitive for better compatibility.

**Example with prefix**:

.. code-block:: python

   # Environment variables:
   # TITAN__AI__COMPLETION__MODEL=deepseek-chat
   # TITAN__AI__COMPLETION__API_BASE=https://api.deepseek.com
   # AI__COMPLETION__MODEL=other-model  # This will be ignored

   cfg = Config(
       model=TitanConfig,
       sources=[
           sources.Env(prefix="TITAN__"),  # Only loads TITAN__ prefixed variables
       ],
   )
   
   config = cfg.load()
   # config.ai.completion.model == "deepseek-chat"
   # AI__COMPLETION__MODEL is ignored due to prefix filtering

CLI Arguments
-------------

Loads from command-line arguments, filtered by model fields:

.. code-block:: python

   # Recommended: Model is auto-injected by Config
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.CLI(),  # Model auto-injected, no need to pass model parameter
       ],
   )

   # Advanced: Explicit model (when using source independently)
   source = sources.CLI()  # Only needed if using source outside Config
   # Only parses arguments for model fields
   # Parses --host, --port, --debug, etc.
   # Uses field metadata for help text and optional flags

DotEnv Files
------------

Loads from `.env` files, filtered by model fields:

.. code-block:: python

   # Recommended: Model is auto-injected by Config
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.DotEnv(".env"),  # Model auto-injected, no need to pass model parameter
       ],
   )

   # Advanced: Explicit model (when using source independently)
   source = sources.DotEnv(".env")  # Only needed if using source outside Config
   # Only loads variables that match model fields

YAML Files
----------

Loads from YAML files with automatic nested structure flattening:

.. code-block:: python

   # Recommended: Model is auto-injected by Config
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.YAML("config.yaml"),  # Model auto-injected, no need to pass model parameter
       ],
   )

   # Advanced: Explicit model and options
   source = sources.YAML(
       "config.yaml",
       model=AppConfig,  # Only needed if using source outside Config
       required=False,   # Return empty dict if file not found (default: True)
       encoding="utf-8", # File encoding (default: None, uses system default)
       source_id="custom-yaml",  # Custom source ID for priority policy
   )
   # Nested dictionaries are automatically flattened to dot notation
   # Example: {"db": {"host": "localhost"}} → {"db.host": "localhost"}

**Example YAML file**:

.. code-block:: yaml

   host: 0.0.0.0
   port: 8080
   debug: true
   db:
     host: db.example.com
     port: 3306

**Notes**:
- Model is required and will be auto-injected by ``Config`` if not provided
- Nested dictionaries are automatically flattened to dot notation
- Missing files return empty dict if ``required=False``, or raise ``FileNotFoundError`` if ``required=True``
- Missing files show "Not Available" status in ``--check-variables``
- Supports custom source IDs for multiple YAML sources with different priorities

JSON Files
----------

Loads from JSON files with automatic nested structure flattening:

.. code-block:: python

   # Recommended: Model is auto-injected by Config
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.JSON("config.json"),  # Model auto-injected, no need to pass model parameter
       ],
   )

   # Advanced: Explicit model and options
   source = sources.JSON(
       "config.json",
       model=AppConfig,  # Only needed if using source outside Config
       required=False,   # Return empty dict if file not found (default: True)
       encoding="utf-8", # File encoding (default: None, uses system default)
       source_id="custom-json",  # Custom source ID for priority policy
   )
   # Nested objects are automatically flattened to dot notation
   # Example: {"db": {"host": "localhost"}} → {"db.host": "localhost"}

**Example JSON file**:

.. code-block:: json

   {
     "host": "0.0.0.0",
     "port": 8080,
     "debug": true,
     "db": {
       "host": "db.example.com",
       "port": 3306
     }
   }

**Notes**:
- Model is required and will be auto-injected by ``Config`` if not provided
- Nested objects are automatically flattened to dot notation
- Missing files return empty dict if ``required=False``, or raise ``FileNotFoundError`` if ``required=True``
- Missing files show "Not Available" status in ``--check-variables``
- Supports custom source IDs for multiple JSON sources with different priorities

TOML Files
----------

Loads from TOML files with automatic nested table flattening:

.. code-block:: python

   # Recommended: Model is auto-injected by Config
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.TOML("config.toml"),  # Model auto-injected, no need to pass model parameter
       ],
   )

   # Advanced: Explicit model and options
   source = sources.TOML(
       "config.toml",
       model=AppConfig,  # Only needed if using source outside Config
       required=False,   # Return empty dict if file not found (default: True)
       encoding="utf-8", # File encoding (default: None, uses system default)
       source_id="custom-toml",  # Custom source ID for priority policy
   )
   # Nested tables are automatically flattened to dot notation
   # Example: [db] host = "localhost" → {"db.host": "localhost"}

**Example TOML file**:

.. code-block:: toml

   host = "0.0.0.0"
   port = 8080
   debug = true

   [db]
   host = "db.example.com"
   port = 3306

**Notes**:
- Model is required and will be auto-injected by ``Config`` if not provided
- Nested tables are automatically flattened to dot notation
- Missing files return empty dict if ``required=False``, or raise ``FileNotFoundError`` if ``required=True``
- Missing files show "Not Available" status in ``--check-variables``
- Supports custom source IDs for multiple TOML sources with different priorities
- Requires ``tomli`` package on Python < 3.11 (Python 3.11+ has built-in ``tomllib``)

Etcd
----

Loads from etcd with optional watch support, filtered by model fields (requires ``varlord[etcd]``).

**Features:**
- TLS/SSL certificate support
- User authentication
- Dynamic updates via watch
- Configuration from environment variables
- Automatic JSON parsing

**Basic Usage:**

.. code-block:: python

   # Recommended: Model is auto-injected by Config
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Etcd(
               host="127.0.0.1",
               port=2379,
               prefix="/app/",
               watch=True,  # Enable dynamic updates
               # Model auto-injected, no need to pass model parameter
           ),
       ],
   )

   # Advanced: Explicit model (when using source independently)
   source = sources.Etcd(
       host="127.0.0.1",
       port=2379,
       prefix="/app/",
       watch=True,
       model=AppConfig,  # Only needed if using source outside Config
   )
   # Only loads keys that match model fields

**With TLS:**

.. code-block:: python

   source = sources.Etcd(
       host="192.168.0.220",
       port=2379,
       prefix="/app/",
       ca_cert="./cert/ca.cert.pem",
       cert_key="./cert/key.pem",
       cert_cert="./cert/cert.pem",
   )

**From Environment Variables (Recommended):**

.. code-block:: python

   # Set environment variables:
   # export ETCD_HOST=192.168.0.220
   # export ETCD_PORT=2379
   # export ETCD_CA_CERT=./cert/ca.cert.pem
   # export ETCD_CERT_KEY=./cert/key.pem
   # export ETCD_CERT_CERT=./cert/cert.pem

   source = sources.Etcd.from_env(prefix="/app/")

See :doc:`etcd` for complete documentation.

Custom Sources
--------------

Create custom sources by implementing the ``Source`` interface:

.. code-block:: python

   from varlord.sources.base import Source, ChangeEvent

   class CustomSource(Source):
       def __init__(self, watch=False):
           self._watch = watch
       
       @property
       def name(self) -> str:
           return "custom"

       def load(self):
           return {"key": "value"}
       
       # To enable watch support, you MUST override supports_watch()
       def supports_watch(self) -> bool:
           """Must override to enable watch support"""
           return self._watch
       
       def watch(self):
           """Implement watch logic"""
           if not self._watch:
               return iter([])  # Return empty iterator when watch is disabled
           
           # Yield ChangeEvent objects when configuration changes
           while True:
               # Monitor for changes...
               yield ChangeEvent(
                   key="key",
                   old_value="old",
                   new_value="new",
                   event_type="modified"
               )

Watch Support Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~

To enable watch support in a custom source, you **must**:

1. Override ``supports_watch()`` to return ``True`` when watch is enabled
2. Implement ``watch()`` to yield ``ChangeEvent`` objects when watch is enabled
3. Return an empty iterator from ``watch()`` when watch is disabled

**Important**: The ``supports_watch()`` method is the only way to indicate watch support. Simply overriding ``watch()`` is not sufficient - you must also override ``supports_watch()``.

