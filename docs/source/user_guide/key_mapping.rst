Key Mapping Rules
=================

Each source in Varlord has specific rules for how it maps external variable names
to configuration keys. Understanding these rules helps you use the right naming
conventions for each source.

Overview
--------

All sources in Varlord use a **unified normalization rule** for consistency:

1. **Double underscores (``__``)** → **Dots (``.``)** for nested configuration
2. **Single underscores (``_``)** → **Preserved** (only case is converted)
3. **All keys** → **Lowercase** for consistency

This unified rule ensures that:
- Keys from different sources can properly override each other
- Nested configuration uses dot notation (e.g., ``db.host``)
- Flat keys with underscores are preserved (e.g., ``k8s_pod_name``)
- All sources behave consistently

**Examples**:
- ``APP_DB__HOST`` → ``db.host`` (``__`` becomes ``.``)
- ``K8S_POD_NAME`` → ``k8s_pod_name`` (single ``_`` preserved)
- ``db__host`` → ``db.host`` (``__`` becomes ``.``)

Mapping Rules by Source
------------------------

Defaults
~~~~~~~~

**Source**: ``sources.Defaults``

**Input**: Dataclass field names

**Mapping**: Unified normalization (``__`` → ``.``, ``_`` preserved, lowercase)

**Example**:

.. code-block:: python

   @dataclass
   class AppConfig:
       host: str = "localhost"
       db_host: str = "127.0.0.1"
       db__host: str = "127.0.0.1"
       k8s_pod_name: str = "default-pod"
   
   # Returns: {"host": "localhost", "db_host": "127.0.0.1", "db.host": "127.0.0.1", "k8s_pod_name": "default-pod"}

**Notes**:
- Field names are normalized using unified rules
- ``__`` in field names becomes ``.`` (for nesting)
- Single ``_`` is preserved
- All keys are lowercase
- Supports nested dataclasses (fields become ``"parent.child"``)

Env (Environment Variables)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Source**: ``sources.Env``

**Input**: Environment variable names

**Mapping Rules**:

1. **Prefix filtering**: Only variables with the specified prefix are loaded
2. **Prefix removal**: The prefix is stripped from the variable name
3. **Unified normalization**: ``__`` → ``.``, ``_`` preserved, lowercase

**Example**:

.. code-block:: python

   # Environment variables:
   # APP_HOST=0.0.0.0
   # APP_PORT=9000
   # APP_DB__HOST=localhost
   # APP_DB__PORT=5432
   # APP_K8S_POD_NAME=my-pod
   # OTHER_VAR=ignored
   
   source = Env(prefix="APP_")
   # Returns: {"host": "0.0.0.0", "port": "9000", "db.host": "localhost", "db.port": "5432", "k8s_pod_name": "my-pod"}

**Mapping Details**:

- ``APP_HOST`` → ``host`` (prefix removed, unified normalization)
- ``APP_DB__HOST`` → ``db.host`` (prefix removed, ``__`` → ``.``)
- ``APP_K8S_POD_NAME`` → ``k8s_pod_name`` (prefix removed, single ``_`` preserved)
- ``OTHER_VAR`` → ignored (no prefix match)

**Custom Normalization**:

You can provide a custom normalization function to override the default:

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
2. **Hyphen and underscore equivalence**: Both ``-`` and ``_`` are treated the same
3. **Unified normalization**: ``__`` → ``.``, ``_`` preserved, lowercase
4. **Type conversion**: Values are converted based on model field types

**Example**:

.. code-block:: python

   # Command line: python app.py --host 0.0.0.0 --port 9000 --db-host localhost --k8s-pod-name my-pod --debug
   # Or equivalently: --db_host, --k8s_pod_name (both work)
   
   source = CLI(model=AppConfig)
   # Returns: {"host": "0.0.0.0", "port": 9000, "db.host": "localhost", "k8s_pod_name": "my-pod", "debug": True}

**Mapping Details**:

- ``--host`` → ``host``
- ``--db-host`` or ``--db_host`` → ``db.host`` (both ``-`` and ``_`` work, ``__`` becomes ``.``)
- ``--k8s-pod-name`` or ``--k8s_pod_name`` → ``k8s_pod_name`` (both ``-`` and ``_`` work, single ``_`` preserved)
- ``--debug`` → ``debug`` (boolean flag, becomes ``True``)
- ``--no-debug`` → ``debug: False`` (negation flag)

**Special Behavior**:

CLI treats hyphens and underscores equivalently, allowing flexible command-line syntax:
- ``--db-host`` and ``--db_host`` both work (if field is ``db__host`` or ``db_host``)
- The unified normalization rule applies after converting ``-`` to ``_``

DotEnv (.env Files)
~~~~~~~~~~~~~~~~~~~

**Source**: ``sources.DotEnv``

**Input**: .env file variable names

**Mapping Rules**:

1. **Unified normalization**: ``__`` → ``.``, ``_`` preserved, lowercase
2. **No prefix filtering**: All keys from .env file are loaded

**Example**:

.. code-block:: python

   # .env file:
   # HOST=0.0.0.0
   # PORT=9000
   # DB_HOST=localhost
   # DB__HOST=localhost
   # K8S_POD_NAME=my-pod
   
   source = DotEnv(".env")
   # Returns: {"host": "0.0.0.0", "port": "9000", "db_host": "localhost", "db.host": "localhost", "k8s_pod_name": "my-pod"}

**Notes**:
- Keys are normalized using unified rules
- ``__`` becomes ``.`` (for nesting)
- Single ``_`` is preserved
- All keys are lowercase
- No prefix filtering

**Best Practice**:

Use ``DotEnv`` with ``Env`` for prefix filtering:

.. code-block:: python

   # .env file uses APP_ prefix
   # APP_HOST=0.0.0.0
   # APP_DB__HOST=localhost
   
   sources = [
       sources.DotEnv(".env"),  # Loads into environment
       sources.Env(prefix="APP_"),  # Filters and normalizes keys
   ]

Etcd
~~~~

**Source**: ``sources.Etcd``

**Input**: Etcd key paths (e.g., ``/app/host``, ``/app/db/host``)

**Mapping Rules**:

1. **Prefix removal**: The specified prefix is removed from the key path
2. **Path separator conversion**: Path separators (``/``) are converted to ``__``
3. **Unified normalization**: ``__`` → ``.``, ``_`` preserved, lowercase

**Example**:

.. code-block:: python

   # Etcd keys:
   # /app/Host = "0.0.0.0"
   # /app/Port = "9000"
   # /app/DB/Host = "localhost"
   # /app/DB/Port = "5432"
   # /app/k8s_pod_name = "my-pod"
   
   source = Etcd(host="127.0.0.1", prefix="/app/")
   # Returns: {"host": "0.0.0.0", "port": "9000", "db.host": "localhost", "db.port": "5432", "k8s_pod_name": "my-pod"}

**Mapping Details**:

- ``/app/Host`` → ``host`` (prefix removed, unified normalization)
- ``/app/DB/Host`` → ``db.host`` (prefix removed, ``/`` → ``__`` → ``.``)
- ``/app/k8s_pod_name`` → ``k8s_pod_name`` (prefix removed, single ``_`` preserved)
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
   
   # Note: Path separator "/" becomes "__" then "." via unified normalization

Comparison Table
----------------

+------------------+------------------+------------------+------------------+------------------+
| Feature          | Defaults         | Env              | CLI              | DotEnv           |
+==================+==================+==================+==================+==================+
| Input            | Field names      | Env var names    | CLI args         | .env file        |
+------------------+------------------+------------------+------------------+------------------+
| Prefix filter    | No               | Yes (optional)   | No               | No               |
+------------------+------------------+------------------+------------------+------------------+
| Normalization    | Unified rule     | Unified rule     | Unified rule     | Unified rule     |
+------------------+------------------+------------------+------------------+------------------+
| ``__`` handling  | ``__`` → ``.``   | ``__`` → ``.``   | ``__`` → ``.``   | ``__`` → ``.``   |
+------------------+------------------+------------------+------------------+------------------+
| ``_`` handling   | Preserved        | Preserved        | Preserved        | Preserved        |
+------------------+------------------+------------------+------------------+------------------+
| CLI special      | N/A              | N/A              | ``-`` = ``_``    | N/A              |
+------------------+------------------+------------------+------------------+------------------+
| Nested keys      | ``parent__child``| ``PARENT__CHILD``|``--parent-child``| ``PARENT__CHILD``|
+------------------+------------------+------------------+------------------+------------------+
| Type conversion  | Native types     | Strings          | Based on model   | Strings          |
+------------------+------------------+------------------+------------------+------------------+
| Example input    | ``host``         | ``APP_HOST``     | ``--host``       | ``HOST``         |
+------------------+------------------+------------------+------------------+------------------+
| Example output   | ``host``         | ``host``         | ``host``         | ``host``         |
+------------------+------------------+------------------+------------------+------------------+
| Nested example   | ``db__host``     | ``APP_DB__HOST`` | ``--db-host``    | ``DB__HOST``     |
+------------------+------------------+------------------+------------------+------------------+
| Nested output    | ``db.host``      | ``db.host``      | ``db.host``      | ``db.host``      |
+------------------+------------------+------------------+------------------+------------------+
| Underscore ex.   | ``k8s_pod_name`` |``APP_K8S_POD``   |``--k8s-pod-name``|``K8S_POD_NAME``  |
+------------------+------------------+------------------+------------------+------------------+
| Underscore out   | ``k8s_pod_name`` | ``k8s_pod``      | ``k8s_pod_name`` | ``k8s_pod_name`` |
+------------------+------------------+------------------+------------------+------------------+

+------------------+------------------+
| Feature          | Etcd             |
+==================+==================+
| Input            | Key paths        |
+------------------+------------------+
| Prefix filter    | Yes (required)   |
+------------------+------------------+
| Normalization    | Unified rule     |
+------------------+------------------+
| Path separator   | ``/`` → ``__``   |
+------------------+------------------+
| ``__`` handling  | ``__`` → ``.``   |
+------------------+------------------+
| ``_`` handling   | Preserved        |
+------------------+------------------+
| Nested keys      | ``/parent/child``|
+------------------+------------------+
| Type conversion  | Strings          |
+------------------+------------------+
| Example input    | ``/app/Host``    |
+------------------+------------------+
| Example output   | ``host``         |
+------------------+------------------+
| Nested example   | ``/app/DB/Host`` |
+------------------+------------------+
| Nested output    | ``db.host``      |
+------------------+------------------+

Common Patterns
---------------

Nested Configuration
~~~~~~~~~~~~~~~~~~~~

To use nested configuration, use dot notation in your source keys:

**Env**:

.. code-block:: python

   # Environment: APP_DB__HOST=localhost APP_DB__PORT=5432
   source = Env(prefix="APP_")
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

Fields with Underscores (e.g., ``k8s_pod_name``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When your dataclass field names contain single underscores (not intended for nesting),
all sources preserve the underscores using the unified normalization rule. Here's how
each source handles overriding such fields:

**Defaults**:

.. code-block:: python

   @dataclass
   class AppConfig:
       k8s_pod_name: str = "default-pod"
   
   # Returns: {"k8s_pod_name": "default-pod"}
   # Note: Single underscores are preserved by unified normalization

**CLI**:

.. code-block:: python

   # Command line: --k8s-pod-name my-pod
   # Or: --k8s_pod_name my-pod (both work)
   source = CLI(model=AppConfig)
   # Returns: {"k8s_pod_name": "my-pod"}
   # Note: Both hyphens and underscores work, unified normalization preserves single _

**DotEnv**:

.. code-block:: python

   # .env file: K8S_POD_NAME=my-pod
   source = DotEnv(".env")
   # Returns: {"k8s_pod_name": "my-pod"}
   # Note: Unified normalization preserves single underscores

**Env**:

.. code-block:: python

   # Environment: APP_K8S_POD_NAME=my-pod
   source = Env(prefix="APP_")
   # Returns: {"k8s_pod_name": "my-pod"}
   # Note: Unified normalization preserves single underscores automatically

**Etcd**:

.. code-block:: python

   # Etcd: /app/k8s_pod_name = my-pod
   source = Etcd(prefix="/app/")
   # Returns: {"k8s_pod_name": "my-pod"}
   # Note: Unified normalization preserves single underscores

**Summary**:

All sources use the unified normalization rule:
- **Single underscores (``_``)**: Preserved in output
- **Double underscores (``__``)**: Converted to dots (``.``) for nesting
- **All keys**: Converted to lowercase

This ensures consistent behavior across all sources, making it easy to override
configuration values regardless of the source type.

Best Practices
--------------

1. **Unified normalization**: All sources use the same normalization rules:
   - ``__`` → ``.`` for nesting
   - Single ``_`` preserved
   - All keys lowercase
   This ensures consistent behavior across all sources.

2. **Nested configuration**: Use double underscores (``__``) in your source keys to create
   nested configuration:
   - Environment: ``APP_DB__HOST=localhost`` → ``db.host``
   - CLI: ``--db-host`` or ``--db_host`` → ``db.host``
   - Etcd: ``/app/DB/Host`` → ``db.host``

3. **Flat keys with underscores**: Use single underscores (``_``) for flat keys:
   - Environment: ``APP_K8S_POD_NAME=my-pod`` → ``k8s_pod_name``
   - CLI: ``--k8s-pod-name`` or ``--k8s_pod_name`` → ``k8s_pod_name``
   - DotEnv: ``K8S_POD_NAME=my-pod`` → ``k8s_pod_name``

4. **Prefix usage**: Use prefixes to avoid conflicts (e.g., ``APP_`` for environment variables)

5. **CLI flexibility**: CLI treats hyphens and underscores equivalently, so you can use
   either ``--db-host`` or ``--db_host`` (both work)

6. **Type safety**: Use CLI or model-based sources when you need automatic type conversion

7. **Override behavior**: With unified normalization, later sources in the list will correctly
   override earlier ones, regardless of the source type

