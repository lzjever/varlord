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

Defaults (Model Defaults)
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Source**: Automatically created from model defaults (no need to explicitly add ``sources.Defaults``)

**Input**: Dataclass field names with default values

**Mapping**: Unified normalization (``__`` → ``.``, ``_`` preserved, lowercase)

**Example**:

.. code-block:: python

   @dataclass
   class AppConfig:
       host: str = field(default="localhost")
       db_host: str = field(default="127.0.0.1")
       db__host: str = field(default="127.0.0.1")
       k8s_pod_name: str = field(default="default-pod")
   
   # Config automatically creates defaults source from model
   # Returns: {"host": "localhost", "db_host": "127.0.0.1", "db.host": "127.0.0.1", "k8s_pod_name": "default-pod"}

**Notes**:
- Defaults are automatically extracted from model fields
- No need to explicitly add ``sources.Defaults`` to your sources list
- Field names are normalized using unified rules
- ``__`` in field names becomes ``.`` (for nesting)
- Single ``_`` is preserved
- All keys are lowercase
- Supports nested dataclasses (fields become ``"parent.child"``)
- Defaults have the lowest priority (can be overridden by other sources)

Env (Environment Variables)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Source**: ``sources.Env``

**Input**: Environment variable names

**Mapping Rules**:

1. **Model-based filtering**: Only environment variables that map to fields defined in the model are loaded
2. **Unified normalization**: ``__`` → ``.``, ``_`` preserved, lowercase

**Example**:

.. code-block:: python

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=9000)
       db__host: str = field(default="127.0.0.1")
       k8s_pod_name: str = field(default="default-pod")
   
   # Environment variables:
   # HOST=0.0.0.0
   # PORT=9000
   # DB__HOST=localhost
   # K8S_POD_NAME=my-pod
   # OTHER_VAR=ignored  # This will be ignored (not in model)
   
   source = Env(model=AppConfig)
   # Returns: {"host": "0.0.0.0", "port": "9000", "db.host": "localhost", "k8s_pod_name": "my-pod"}

**Mapping Details**:

- ``HOST`` → ``host`` (unified normalization)
- ``DB__HOST`` → ``db.host`` (``__`` → ``.``)
- ``K8S_POD_NAME`` → ``k8s_pod_name`` (single ``_`` preserved)
- ``OTHER_VAR`` → ignored (not in model fields)

**Notes**:

- Model is required and will be auto-injected by ``Config`` if not provided
- All environment variables are checked against model fields
- Only variables that map to model fields are loaded
- No prefix filtering - use model fields to control which variables are loaded
- If you want to use a prefix in environment variable names, ensure your model field names match after normalization

CLI (Command-Line Arguments)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Source**: ``sources.CLI``

**Input**: Command-line arguments (e.g., ``--host``, ``--port``)

**Mapping Rules**:

1. **Model-based filtering**: Only arguments for fields defined in the model are parsed
2. **Prefix removal**: The ``--`` prefix is removed
3. **Hyphen and underscore equivalence**: Both ``-`` and ``_`` are treated the same
4. **Unified normalization**: ``__`` → ``.``, ``_`` preserved, lowercase
5. **Type conversion**: Values are converted based on model field types

**Example**:

.. code-block:: python

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=9000)
       db__host: str = field(default="127.0.0.1")
       k8s_pod_name: str = field(default="default-pod")
       debug: bool = field(default=False)
   
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

**Notes**:

- Model is required and will be auto-injected by ``Config`` if not provided
- Only arguments for model fields are parsed
- CLI treats hyphens and underscores equivalently, allowing flexible command-line syntax:
  - ``--db-host`` and ``--db_host`` both work (if field is ``db__host`` or ``db_host``)
  - The unified normalization rule applies after converting ``-`` to ``_``
- Help text and descriptions are automatically extracted from field metadata

DotEnv (.env Files)
~~~~~~~~~~~~~~~~~~~

**Source**: ``sources.DotEnv``

**Input**: .env file variable names

**Mapping Rules**:

1. **Model-based filtering**: Only variables that map to fields defined in the model are loaded
2. **Unified normalization**: ``__`` → ``.``, ``_`` preserved, lowercase

**Example**:

.. code-block:: python

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=9000)
       db__host: str = field(default="127.0.0.1")
       k8s_pod_name: str = field(default="default-pod")
   
   # .env file:
   # HOST=0.0.0.0
   # PORT=9000
   # DB__HOST=localhost
   # K8S_POD_NAME=my-pod
   # OTHER_VAR=ignored  # This will be ignored (not in model)
   
   source = DotEnv(".env", model=AppConfig)
   # Returns: {"host": "0.0.0.0", "port": "9000", "db.host": "localhost", "k8s_pod_name": "my-pod"}

**Notes**:
- Model is required and will be auto-injected by ``Config`` if not provided
- Only variables that map to model fields are loaded
- Keys are normalized using unified rules
- ``__`` becomes ``.`` (for nesting)
- Single ``_`` is preserved
- All keys are lowercase
- No prefix filtering - use model fields to control which variables are loaded

YAML Files
~~~~~~~~~~

**Source**: ``sources.YAML``

**Input**: YAML file structure (nested dictionaries)

**Mapping Rules**:

1. **Recursive flattening**: Nested dictionaries are automatically flattened to dot notation
2. **Model-based filtering**: Only keys that map to fields defined in the model are loaded
3. **Unified normalization**: ``__`` → ``.``, ``_`` preserved, lowercase

**Example**:

.. code-block:: python

   @dataclass
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)

   @dataclass
   class AppConfig:
       host: str = field(default="127.0.0.1")
       port: int = field(default=8000)
       db: DBConfig = field(default_factory=DBConfig)
       k8s_pod_name: str = field(default="default-pod")
   
   # config.yaml:
   # host: 0.0.0.0
   # port: 8080
   # db:
   #   host: db.example.com
   #   port: 3306
   # k8s_pod_name: my-pod
   
   source = YAML("config.yaml", model=AppConfig)
   # Returns: {"host": "0.0.0.0", "port": 8080, "db.host": "db.example.com", "db.port": 3306, "k8s_pod_name": "my-pod"}

**Mapping Details**:

- Nested structure ``db.host`` → ``db.host`` (flattened automatically)
- Top-level keys are normalized using unified rules
- ``k8s_pod_name`` → ``k8s_pod_name`` (single ``_`` preserved)
- Missing files return empty dict (if ``required=False``) or raise ``FileNotFoundError`` (if ``required=True``)

**Notes**:
- Model is required and will be auto-injected by ``Config`` if not provided
- Nested dictionaries are automatically flattened to dot notation
- Keys are normalized using unified rules
- ``__`` becomes ``.`` (for nesting)
- Single ``_`` is preserved
- All keys are lowercase
- Supports ``required=False`` for graceful handling of missing files
- Missing files show "Not Available" status in ``--check-variables``

JSON Files
~~~~~~~~~~~

**Source**: ``sources.JSON``

**Input**: JSON file structure (nested objects)

**Mapping Rules**:

1. **Recursive flattening**: Nested objects are automatically flattened to dot notation
2. **Model-based filtering**: Only keys that map to fields defined in the model are loaded
3. **Unified normalization**: ``__`` → ``.``, ``_`` preserved, lowercase

**Example**:

.. code-block:: python

   @dataclass
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)

   @dataclass
   class AppConfig:
       host: str = field(default="127.0.0.1")
       port: int = field(default=8000)
       db: DBConfig = field(default_factory=DBConfig)
       k8s_pod_name: str = field(default="default-pod")
   
   # config.json:
   # {
   #   "host": "0.0.0.0",
   #   "port": 8080,
   #   "db": {
   #     "host": "db.example.com",
   #     "port": 3306
   #   },
   #   "k8s_pod_name": "my-pod"
   # }
   
   source = JSON("config.json", model=AppConfig)
   # Returns: {"host": "0.0.0.0", "port": 8080, "db.host": "db.example.com", "db.port": 3306, "k8s_pod_name": "my-pod"}

**Mapping Details**:

- Nested structure ``db.host`` → ``db.host`` (flattened automatically)
- Top-level keys are normalized using unified rules
- ``k8s_pod_name`` → ``k8s_pod_name`` (single ``_`` preserved)
- Missing files return empty dict (if ``required=False``) or raise ``FileNotFoundError`` (if ``required=True``)

**Notes**:
- Model is required and will be auto-injected by ``Config`` if not provided
- Nested objects are automatically flattened to dot notation
- Keys are normalized using unified rules
- ``__`` becomes ``.`` (for nesting)
- Single ``_`` is preserved
- All keys are lowercase
- Supports ``required=False`` for graceful handling of missing files
- Missing files show "Not Available" status in ``--check-variables``

TOML Files
~~~~~~~~~~

**Source**: ``sources.TOML``

**Input**: TOML file structure (nested tables)

**Mapping Rules**:

1. **Recursive flattening**: Nested tables are automatically flattened to dot notation
2. **Model-based filtering**: Only keys that map to fields defined in the model are loaded
3. **Unified normalization**: ``__`` → ``.``, ``_`` preserved, lowercase

**Example**:

.. code-block:: python

   @dataclass
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)

   @dataclass
   class AppConfig:
       host: str = field(default="127.0.0.1")
       port: int = field(default=8000)
       db: DBConfig = field(default_factory=DBConfig)
       k8s_pod_name: str = field(default="default-pod")
   
   # config.toml:
   # host = "0.0.0.0"
   # port = 8080
   # k8s_pod_name = "my-pod"
   #
   # [db]
   # host = "db.example.com"
   # port = 3306
   
   source = TOML("config.toml", model=AppConfig)
   # Returns: {"host": "0.0.0.0", "port": 8080, "db.host": "db.example.com", "db.port": 3306, "k8s_pod_name": "my-pod"}

**Mapping Details**:

- Nested tables ``[db]`` → ``db.host``, ``db.port`` (flattened automatically)
- Top-level keys are normalized using unified rules
- ``k8s_pod_name`` → ``k8s_pod_name`` (single ``_`` preserved)
- Missing files return empty dict (if ``required=False``) or raise ``FileNotFoundError`` (if ``required=True``)

**Notes**:
- Model is required and will be auto-injected by ``Config`` if not provided
- Nested tables are automatically flattened to dot notation
- Keys are normalized using unified rules
- ``__`` becomes ``.`` (for nesting)
- Single ``_`` is preserved
- All keys are lowercase
- Supports ``required=False`` for graceful handling of missing files
- Missing files show "Not Available" status in ``--check-variables``
- Requires ``tomli`` package on Python < 3.11 (Python 3.11+ has built-in ``tomllib``)

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

+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Feature          | Defaults         | Env              | CLI              | DotEnv           | YAML             | JSON             | TOML             |
+==================+==================+==================+==================+==================+==================+==================+==================+
| Input            | Field names      | Env var names    | CLI args         | .env file        | YAML file        | JSON file        | TOML file        |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Model filter     | N/A (from model) | Yes (required)   | Yes (required)   | Yes (required)   | Yes (required)   | Yes (required)   | Yes (required)   |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Prefix filter    | No               | No               | No               | No               | No               | No               | No               |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Normalization    | Unified rule     | Unified rule     | Unified rule     | Unified rule     | Unified rule     | Unified rule     | Unified rule     |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Flattening       | N/A              | N/A              | N/A              | N/A              | Recursive        | Recursive        | Recursive        |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| ``__`` handling  | ``__`` → ``.``   | ``__`` → ``.``   | ``__`` → ``.``   | ``__`` → ``.``   | ``__`` → ``.``   | ``__`` → ``.``   | ``__`` → ``.``   |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| ``_`` handling   | Preserved        | Preserved        | Preserved        | Preserved        | Preserved        | Preserved        | Preserved        |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| CLI special      | N/A              | N/A              | ``-`` = ``_``    | N/A              | N/A              | N/A              | N/A              |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Nested keys      | ``parent__child``| ``PARENT__CHILD``|``--parent-child``| ``PARENT__CHILD``| ``parent: child:``| ``{"parent": {}}``| ``[parent]``   |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Type conversion  | Native types     | Strings          | Based on model   | Strings          | Native types     | Native types     | Native types     |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Missing file     | N/A              | N/A              | N/A              | Empty dict       | Empty dict*      | Empty dict*      | Empty dict*      |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Example input    | ``host``         | ``HOST``         | ``--host``       | ``HOST``         | ``host: ...``     | ``"host": ...``   | ``host = ...`` |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Example output   | ``host``         | ``host``         | ``host``         | ``host``         | ``host``         | ``host``         | ``host``         |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Nested example   | ``db__host``     | ``DB__HOST``     | ``--db-host``    | ``DB__HOST``     | ``db: host:``    |``"db": {"host"}``| ``[db] host``    |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Nested output    | ``db.host``      | ``db.host``      | ``db.host``      | ``db.host``      | ``db.host``      | ``db.host``      | ``db.host``      |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Underscore ex.   | ``k8s_pod_name`` |``K8S_POD_NAME``  |``--k8s-pod-name``|``K8S_POD_NAME``  | ``k8s_pod_name:``|``"k8s_pod_name"``| ``k8s_pod_name`` |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+
| Underscore out   | ``k8s_pod_name`` | ``k8s_pod_name`` | ``k8s_pod_name`` | ``k8s_pod_name`` | ``k8s_pod_name`` | ``k8s_pod_name`` | ``k8s_pod_name`` |
+------------------+------------------+------------------+------------------+------------------+------------------+------------------+------------------+

\* If ``required=False``, otherwise raises ``FileNotFoundError``

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

To use nested configuration, use double underscores (``__``) in your source keys, which will be normalized to dots (``.``):

**Env**:

.. code-block:: python

   @dataclass
   class AppConfig:
       db__host: str = field(default="")
       db__port: int = field(default=5432)
   
   # Environment: DB__HOST=localhost DB__PORT=5432
   source = Env(model=AppConfig)
   # Returns: {"db.host": "localhost", "db.port": "5432"}

**CLI**:

.. code-block:: python

   @dataclass
   class AppConfig:
       db__host: str = field(default="")
       db__port: int = field(default=5432)
   
   # Command line: --db-host localhost --db-port 5432
   source = CLI(model=AppConfig)
   # Returns: {"db.host": "localhost", "db.port": "5432"}
   # Automatically maps to nested dataclass structure

**DotEnv**:

.. code-block:: python

   @dataclass
   class AppConfig:
       db__host: str = field(default="")
       db__port: int = field(default=5432)
   
   # .env file: DB__HOST=localhost DB__PORT=5432
   source = DotEnv(".env", model=AppConfig)
   # Returns: {"db.host": "localhost", "db.port": "5432"}

**Etcd**:

.. code-block:: python

   # Etcd: /app/db/host = localhost, /app/db/port = 5432
   source = Etcd(host="127.0.0.1", prefix="/app/", model=AppConfig)
   # Returns: {"db.host": "localhost", "db.port": "5432"}

Model-Based Filtering
~~~~~~~~~~~~~~~~~~~~~

All sources (except Defaults) now use model-based filtering to control which variables are loaded:

**Env**:

.. code-block:: python

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=9000)
   
   # Environment: HOST=0.0.0.0 PORT=9000 OTHER_VAR=ignored
   source = Env(model=AppConfig)
   # Returns: {"host": "0.0.0.0", "port": "9000"}
   # OTHER_VAR is ignored because it's not in the model

**CLI**:

.. code-block:: python

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=9000)
   
   # Command line: --host 0.0.0.0 --port 9000 --other-var ignored
   source = CLI(model=AppConfig)
   # Returns: {"host": "0.0.0.0", "port": "9000"}
   # --other-var is ignored because it's not in the model

**DotEnv**:

.. code-block:: python

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=9000)
   
   # .env file: HOST=0.0.0.0 PORT=9000 OTHER_VAR=ignored
   source = DotEnv(".env", model=AppConfig)
   # Returns: {"host": "0.0.0.0", "port": "9000"}
   # OTHER_VAR is ignored because it's not in the model

Fields with Underscores (e.g., ``k8s_pod_name``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When your dataclass field names contain single underscores (not intended for nesting),
all sources preserve the underscores using the unified normalization rule. Here's how
each source handles overriding such fields:

**Defaults**:

.. code-block:: python

   @dataclass
   class AppConfig:
       k8s_pod_name: str = field(default="default-pod")
   
   # Config automatically creates defaults from model
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

   @dataclass
   class AppConfig:
       k8s_pod_name: str = field(default="")
   
   # .env file: K8S_POD_NAME=my-pod
   source = DotEnv(".env", model=AppConfig)
   # Returns: {"k8s_pod_name": "my-pod"}
   # Note: Unified normalization preserves single underscores

**Env**:

.. code-block:: python

   @dataclass
   class AppConfig:
       k8s_pod_name: str = field(default="")
   
   # Environment: K8S_POD_NAME=my-pod
   source = Env(model=AppConfig)
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
   - Environment: ``DB__HOST=localhost`` → ``db.host``
   - CLI: ``--db-host`` or ``--db_host`` → ``db.host``
   - DotEnv: ``DB__HOST=localhost`` → ``db.host``
   - Etcd: ``/app/DB/Host`` → ``db.host``

3. **Flat keys with underscores**: Use single underscores (``_``) for flat keys:
   - Environment: ``K8S_POD_NAME=my-pod`` → ``k8s_pod_name``
   - CLI: ``--k8s-pod-name`` or ``--k8s_pod_name`` → ``k8s_pod_name``
   - DotEnv: ``K8S_POD_NAME=my-pod`` → ``k8s_pod_name``

4. **Model-based filtering**: All sources (except Defaults) use model fields to filter which
   variables are loaded. Define your model fields to match the normalized keys you want to use.

5. **CLI flexibility**: CLI treats hyphens and underscores equivalently, so you can use
   either ``--db-host`` or ``--db_host`` (both work)

6. **Type safety**: Use CLI or model-based sources when you need automatic type conversion

7. **Override behavior**: With unified normalization, later sources in the list will correctly
   override earlier ones, regardless of the source type

