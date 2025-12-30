Key Mapping Rules
=================

Each source in Varlord has specific rules for how it maps external variable names
to configuration keys. Understanding these rules helps you use the right naming
conventions for each source.

Overview
--------

All sources return normalized keys using:
- **Dot notation** (e.g., ``"db.host"``) for nested configuration
- **Lowercase** for consistency across all sources

This ensures that keys from different sources can properly override each other.
However, each source has different rules for how it reads and transforms external
names into these normalized keys.

Mapping Rules by Source
------------------------

Defaults
~~~~~~~~

**Source**: ``sources.Defaults``

**Input**: Dataclass field names

**Mapping**: Direct mapping, no transformation

**Example**:

.. code-block:: python

   @dataclass
   class AppConfig:
       host: str = "localhost"
       db_host: str = "127.0.0.1"
       api_timeout: int = 30
   
   # Returns: {"host": "localhost", "db_host": "127.0.0.1", "api_timeout": 30}

**Notes**:
- Field names are used as-is
- No prefix filtering
- No case conversion
- Supports nested dataclasses (fields become ``"parent.child"``)

Env (Environment Variables)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Source**: ``sources.Env``

**Input**: Environment variable names

**Mapping Rules**:

1. **Prefix filtering**: Only variables with the specified prefix are loaded
2. **Prefix removal**: The prefix is stripped from the variable name
3. **Case conversion**: Variable names are converted to lowercase
4. **Separator replacement**: The separator (default: ``"__"``) is replaced with ``"."``

**Example**:

.. code-block:: python

   # Environment variables:
   # APP_HOST=0.0.0.0
   # APP_PORT=9000
   # APP_DB__HOST=localhost
   # APP_DB__PORT=5432
   # OTHER_VAR=ignored
   
   source = Env(prefix="APP_", separator="__")
   # Returns: {"host": "0.0.0.0", "port": "9000", "db.host": "localhost", "db.port": "5432"}

**Mapping Details**:

- ``APP_HOST`` → ``host`` (prefix removed, lowercase)
- ``APP_DB__HOST`` → ``db.host`` (prefix removed, separator ``__`` → ``.``, lowercase)
- ``APP_API_TIMEOUT`` → ``api.timeout`` (if separator is ``_``)
- ``OTHER_VAR`` → ignored (no prefix match)

**Custom Normalization**:

You can provide a custom normalization function:

.. code-block:: python

   def custom_normalize(key: str) -> str:
       # Your custom logic
       return key.lower().replace("_", "-")
   
   source = Env(prefix="APP_", normalize_key=custom_normalize)

CLI (Command-Line Arguments)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Source**: ``sources.CLI``

**Input**: Command-line arguments (e.g., ``--host``, ``--port``)

**Mapping Rules**:

1. **Prefix removal**: The ``--`` prefix is removed
2. **Hyphen to dot**: Hyphens are converted to dots (for consistency with other sources)
3. **Type conversion**: Values are converted based on model field types

**Example**:

.. code-block:: python

   # Command line: python app.py --host 0.0.0.0 --port 9000 --db-host localhost --debug
   
   source = CLI()
   # Returns: {"host": "0.0.0.0", "port": 9000, "db.host": "localhost", "debug": True}

**Mapping Details**:

- ``--host`` → ``host``
- ``--db-host`` → ``db.host`` (hyphen → dot, unified with Env/Etcd)
- ``--api-timeout`` → ``api.timeout``
- ``--debug`` → ``debug`` (boolean flag, becomes ``True``)
- ``--no-debug`` → ``debug: False`` (negation flag)

**Nested Keys**:

CLI uses dot notation for nested keys, consistent with other sources:

- ``--db-host`` → ``db.host`` (automatically maps to nested dataclass)
- ``--api-timeout`` → ``api.timeout``
- This allows CLI to properly override Env/Etcd values for nested configuration

DotEnv (.env Files)
~~~~~~~~~~~~~~~~~~~

**Source**: ``sources.DotEnv``

**Input**: .env file variable names

**Mapping Rules**:

1. **Case conversion**: Keys are converted to lowercase
2. **No separator replacement**: Underscores are preserved (unlike Env source)
3. **No prefix filtering**: All keys from .env file are loaded

**Example**:

.. code-block:: python

   # .env file:
   # HOST=0.0.0.0
   # PORT=9000
   # DB_HOST=localhost
   # DB_PORT=5432
   
   source = DotEnv(".env")
   # Returns: {"host": "0.0.0.0", "port": "9000", "db_host": "localhost", "db_port": "5432"}
   # Note: Only case is converted, underscores are preserved

**Notes**:
- Keys are converted to lowercase for consistency
- Underscores are preserved (not converted to dots)
- No prefix filtering
- For nested keys with dot notation, use ``Env`` source with ``DotEnv``

**Best Practice**:

Use ``DotEnv`` with ``Env`` for automatic normalization with nested keys:

.. code-block:: python

   # .env file uses APP_ prefix and __ separator for nesting
   # APP_HOST=0.0.0.0
   # APP_DB__HOST=localhost
   
   sources = [
       sources.DotEnv(".env"),  # Loads into environment
       sources.Env(prefix="APP_", separator="__"),  # Normalizes keys (db.host)
   ]

Etcd
~~~~

**Source**: ``sources.Etcd``

**Input**: Etcd key paths (e.g., ``/app/host``, ``/app/db/host``)

**Mapping Rules**:

1. **Prefix removal**: The specified prefix is removed from the key path
2. **Path to dot notation**: Path separators (``/``) are converted to dots (``.``)
3. **Case conversion**: Keys are converted to lowercase for consistency
4. **Leading/trailing cleanup**: Leading and trailing slashes are removed

**Example**:

.. code-block:: python

   # Etcd keys:
   # /app/Host = "0.0.0.0"
   # /app/Port = "9000"
   # /app/DB/Host = "localhost"
   # /app/DB/Port = "5432"
   
   source = Etcd(host="127.0.0.1", prefix="/app/")
   # Returns: {"host": "0.0.0.0", "port": "9000", "db.host": "localhost", "db.port": "5432"}

**Mapping Details**:

- ``/app/Host`` → ``host`` (prefix removed, lowercase)
- ``/app/DB/Host`` → ``db.host`` (prefix removed, ``/`` → ``.``, lowercase)
- ``/app/API/Timeout`` → ``api.timeout``
- ``/other/key`` → ignored (no prefix match)

**Nested Structure**:

Etcd's hierarchical structure naturally maps to nested configuration:

.. code-block:: python

   # Etcd structure:
   # /app/DB/Host = "localhost"
   # /app/DB/Port = "5432"
   # /app/API/Timeout = "30"
   
   # Maps to:
   # {"db.host": "localhost", "db.port": "5432", "api.timeout": "30"}

Comparison Table
----------------

+------------------+------------------+------------------+------------------+------------------+
| Feature          | Defaults         | Env              | CLI              | DotEnv           |
+==================+==================+==================+==================+==================+
| Input            | Field names      | Env var names    | CLI args         | .env file        |
+------------------+------------------+------------------+------------------+------------------+
| Prefix filter    | No               | Yes (optional)   | No               | No               |
+------------------+------------------+------------------+------------------+------------------+
| Case conversion  | No               | Yes (lowercase)  | Yes (lowercase)  | Yes (lowercase)  |
+------------------+------------------+------------------+------------------+------------------+
| Separator        | N/A              | ``__`` → ``.``   | ``-`` → ``.``    | No conversion    |
+------------------+------------------+------------------+------------------+------------------+
| Nested keys      | ``parent.child`` | ``PARENT__CHILD``|``--parent-child``| ``PARENT_CHILD`` |
+------------------+------------------+------------------+------------------+------------------+
| Type conversion  | Native types     | Strings          | Based on model   | Strings          |
+------------------+------------------+------------------+------------------+------------------+
| Example input    | ``host``         | ``APP_HOST``     | ``--host``       | ``HOST``         |
+------------------+------------------+------------------+------------------+------------------+
| Example output   | ``host``         | ``host``         | ``host``         | ``host``         |
+------------------+------------------+------------------+------------------+------------------+
| Nested example   | ``db.host``      | ``APP_DB__HOST`` | ``--db-host``    | ``DB_HOST``      |
+------------------+------------------+------------------+------------------+------------------+
| Nested output    | ``db.host``      | ``db.host``      | ``db.host``      | ``db.host``      |
+------------------+------------------+------------------+------------------+------------------+

+------------------+------------------+
| Feature          | Etcd             |
+==================+==================+
| Input            | Key paths        |
+------------------+------------------+
| Prefix filter    | Yes (required)   |
+------------------+------------------+
| Case conversion  | Yes (lowercase)  |
+------------------+------------------+
| Separator        | ``/`` → ``.``    |
+------------------+------------------+
| Nested keys      | ``/parent/child``|
+------------------+------------------+
| Type conversion  | Strings          |
+------------------+------------------+
| Example input    | ``/app/Host``    |
+------------------+------------------+
| Example output   | ``host``         |
+------------------+------------------+

Common Patterns
---------------

Nested Configuration
~~~~~~~~~~~~~~~~~~~~

To use nested configuration, use dot notation in your source keys:

**Env**:

.. code-block:: python

   # Environment: APP_DB__HOST=localhost APP_DB__PORT=5432
   source = Env(prefix="APP_", separator="__")
   # Returns: {"db.host": "localhost", "db.port": "5432"}

**CLI**:

.. code-block:: python

   # Command line: --db-host localhost --db-port 5432
   source = CLI()
   # Returns: {"db.host": "localhost", "db.port": "5432"}
   # Automatically maps to nested dataclass structure

**Etcd**:

.. code-block:: python

   # Etcd: /app/db/host = localhost, /app/db/port = 5432
   source = Etcd(prefix="/app/")
   # Returns: {"db.host": "localhost", "db.port": "5432"}

Prefix Isolation
~~~~~~~~~~~~~~~~

Use prefixes to isolate configuration from different applications:

**Env**:

.. code-block:: python

   # Only load APP_* variables
   source = Env(prefix="APP_")

**Etcd**:

.. code-block:: python

   # Only load /app/* keys
   source = Etcd(prefix="/app/")

Best Practices
--------------

1. **Unified format**: All sources now use unified lowercase dot notation, ensuring
   consistent key mapping across all sources

2. **Prefix usage**: Use prefixes to avoid conflicts (e.g., ``APP_`` for environment variables)

3. **Case insensitivity**: All sources normalize keys to lowercase, so you don't need to
   worry about case mismatches between sources

4. **Nested structures**: Use dot notation for nested configuration to leverage
   Varlord's automatic mapping to nested dataclasses

5. **Type safety**: Use CLI or model-based sources when you need automatic type conversion

6. **Override behavior**: With unified key format (lowercase + dot notation), later sources
   in the list will correctly override earlier ones, regardless of the source type

