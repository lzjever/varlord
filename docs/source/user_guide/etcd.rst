Etcd Source
===========

The Etcd source allows loading configuration from etcd key-value store with support for TLS authentication, user authentication, and dynamic updates via watch.

Installation
------------

Install the etcd extra:

.. code-block:: bash

   pip install varlord[etcd]

Basic Usage
-----------

Direct Creation
~~~~~~~~~~~~~~~

Create an Etcd source directly:

.. code-block:: python

   from varlord import Config
   from varlord.sources import Etcd
   from dataclasses import dataclass, field

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=8000)
       debug: bool = field(default=False)

   # Create etcd source
   etcd_source = Etcd(
       host="192.168.0.220",
       port=2379,
       prefix="/app/",
       ca_cert="./cert/AgentsmithLocal.cert.pem",
       cert_key="./cert/etcd-client-lzj-local/key.pem",
       cert_cert="./cert/etcd-client-lzj-local/cert.pem",
   )

   # Use Config
   cfg = Config(
       model=AppConfig,
       sources=[etcd_source],
   )

   app = cfg.load()

From Environment Variables (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The recommended approach is to read environment variables yourself and pass them to ``Etcd()``. This aligns with the principle that the library should not implicitly read environment variables for its own configuration.

.. code-block:: python

   from varlord import Config
   from varlord.sources import Etcd
   from dataclasses import dataclass, field
   import os

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=8000)
       debug: bool = field(default=False)

   # Read environment variables and pass to Etcd
   etcd_source = Etcd(
       host=os.environ.get("ETCD_HOST", "127.0.0.1"),
       port=int(os.environ.get("ETCD_PORT", "2379")),
       prefix=os.environ.get("ETCD_PREFIX", "/app/"),
       ca_cert=os.environ.get("ETCD_CA_CERT"),
       cert_key=os.environ.get("ETCD_CERT_KEY"),
       cert_cert=os.environ.get("ETCD_CERT_CERT"),
       user=os.environ.get("ETCD_USER"),
       password=os.environ.get("ETCD_PASSWORD"),
       watch=os.environ.get("ETCD_WATCH", "").lower() in ("true", "1", "yes", "on"),
   )

   cfg = Config(
       model=AppConfig,
       sources=[etcd_source],
   )

   app = cfg.load()

**Note**: The ``Etcd.from_env()`` method has been removed. All parameters must be passed explicitly via ``__init__``.

Environment Variables
---------------------

Configure etcd connection via environment variables:

**Required:**
- ``ETCD_HOST``: Etcd host (default: "127.0.0.1")
- ``ETCD_PORT``: Etcd port (default: 2379)

**Optional - TLS Certificates:**
- ``ETCD_CA_CERT``: Path to CA certificate file
- ``ETCD_CERT_KEY``: Path to client key file
- ``ETCD_CERT_CERT``: Path to client certificate file

**Optional - Authentication:**
- ``ETCD_USER``: Username for authentication
- ``ETCD_PASSWORD``: Password for authentication

**Optional - Other Settings:**
- ``ETCD_PREFIX``: Key prefix to load (default: "/")
- ``ETCD_WATCH``: Enable watch support ("true", "1", "yes", "on")
- ``ETCD_TIMEOUT``: Connection timeout in seconds

Example:

.. code-block:: bash

   export ETCD_HOST=192.168.0.220
   export ETCD_PORT=2379
   export ETCD_CA_CERT=./cert/AgentsmithLocal.cert.pem
   export ETCD_CERT_KEY=./cert/etcd-client-lzj-local/key.pem
   export ETCD_CERT_CERT=./cert/etcd-client-lzj-local/cert.pem
   export ETCD_PREFIX=/app/
   export ETCD_WATCH=true

Using .env Files
----------------

You can also configure etcd in a ``.env`` file:

.. code-block:: bash

   # .env
   ETCD_HOST=192.168.0.220
   ETCD_PORT=2379
   ETCD_CA_CERT=./cert/AgentsmithLocal.cert.pem
   ETCD_CERT_KEY=./cert/etcd-client-lzj-local/key.pem
   ETCD_CERT_CERT=./cert/etcd-client-lzj-local/cert.pem
   ETCD_PREFIX=/app/
   ETCD_WATCH=true

Then load it with python-dotenv:

.. code-block:: python

   from dotenv import load_dotenv
   from varlord import Config
   from varlord.sources import Etcd

   load_dotenv()  # Load .env file

   import os
   
   etcd_source = Etcd(
       host=os.environ.get("ETCD_HOST", "127.0.0.1"),
       port=int(os.environ.get("ETCD_PORT", "2379")),
       prefix=os.environ.get("ETCD_PREFIX", "/app/"),
       ca_cert=os.environ.get("ETCD_CA_CERT"),
       cert_key=os.environ.get("ETCD_CERT_KEY"),
       cert_cert=os.environ.get("ETCD_CERT_CERT"),
   )
   
   cfg = Config(
       model=AppConfig,
       sources=[etcd_source],
   )

TLS Configuration
-----------------

Etcd source supports TLS/SSL connections with client certificates:

.. code-block:: python

   source = Etcd(
       host="192.168.0.220",
       port=2379,
       prefix="/app/",
       ca_cert="./cert/AgentsmithLocal.cert.pem",      # CA certificate
       cert_key="./cert/etcd-client-lzj-local/key.pem",  # Client key
       cert_cert="./cert/etcd-client-lzj-local/cert.pem", # Client certificate
   )

Or via environment variables:

.. code-block:: bash

   export ETCD_CA_CERT=./cert/AgentsmithLocal.cert.pem
   export ETCD_CERT_KEY=./cert/etcd-client-lzj-local/key.pem
   export ETCD_CERT_CERT=./cert/etcd-client-lzj-local/cert.pem

User Authentication
-------------------

If your etcd instance requires authentication:

.. code-block:: python

   source = Etcd(
       host="192.168.0.220",
       port=2379,
       prefix="/app/",
       user="myuser",
       password="mypassword",
   )

Or via environment variables:

.. code-block:: bash

   export ETCD_USER=myuser
   export ETCD_PASSWORD=mypassword

Key Naming Conventions
----------------------

Etcd source supports multiple key naming formats:

**Flat Keys:**
- ``host``, ``port``, ``api_key``

**Nested Keys (Double Underscore):**
- ``db__host``, ``db__port`` → normalized to ``db.host``, ``db.port``

**Nested Keys (Slash Separator):**
- ``db/host``, ``db/port`` → converted to ``db__host``, ``db__port`` → normalized to ``db.host``, ``db.port``

Example:

.. code-block:: python

   @dataclass
   class DBConfig:
       host: str = field()
       port: int = field(default=5432)

   @dataclass
   class AppConfig:
       api_key: str = field()
       db: DBConfig = field()

   # In etcd:
   # /app/api_key = "secret123"
   # /app/db__host = "db.example.com"  # Double underscore for nesting
   # /app/db__port = "5432"
   # OR
   # /app/db/host = "db.example.com"  # Slash separator also works
   # /app/db/port = "5432"

Value Types
-----------

Etcd source automatically handles different value types:

**Strings:**
- Returned as-is

**JSON:**
- Automatically parsed if valid JSON
- ``"9000"`` → ``9000`` (integer)
- ``"true"`` → ``True`` (boolean)
- ``'{"key": "value"}'`` → ``{"key": "value"}`` (dict)

Watch Support (Dynamic Updates)
--------------------------------

Enable watch support for dynamic configuration updates. Etcd source can watch for changes and automatically notify subscribers.

**Basic Watch Example:**

.. code-block:: python

   from varlord import Config
   from varlord.sources import Etcd
   import threading

   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd(
               host=os.environ.get("ETCD_HOST", "127.0.0.1"),
               port=int(os.environ.get("ETCD_PORT", "2379")),
               prefix="/app/",
               watch=True,
               ca_cert=os.environ.get("ETCD_CA_CERT"),
               cert_key=os.environ.get("ETCD_CERT_KEY"),
               cert_cert=os.environ.get("ETCD_CERT_CERT"),
           ),
       ],
   )

   # Load initial configuration
   app = cfg.load()

   # Start watch in background thread
   def watch_changes():
       etcd_source = cfg._sources[0]
       for event in etcd_source.watch():
           print(f"Config changed: {event.key} = {event.new_value} (type: {event.event_type})")
           # Reload configuration
           app = cfg.load()

   watch_thread = threading.Thread(target=watch_changes, daemon=True)
   watch_thread.start()

**Watch Events:**

Watch events include:
- ``added``: New key was added
- ``modified``: Existing key was modified
- ``deleted``: Key was deleted

**Example: Watching Multiple Keys:**

.. code-block:: python

   from varlord import Config
   from varlord.sources import Etcd
   from varlord.sources.base import ChangeEvent
   import threading

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=8000)
       debug: bool = field(default=False)

   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd(
               host="192.168.0.220",
               port=2379,
               prefix="/app/",
               watch=True,
               ca_cert="./cert/ca.cert.pem",
               cert_key="./cert/key.pem",
               cert_cert="./cert/cert.pem",
           ),
       ],
   )

   events_received = []

   def watch_thread():
       etcd_source = cfg._sources[0]
       for event in etcd_source.watch():
           events_received.append(event)
           print(f"Event: {event.key} = {event.new_value} ({event.event_type})")
           if len(events_received) >= 3:
               break

   watch_thread_obj = threading.Thread(target=watch_thread, daemon=True)
   watch_thread_obj.start()

   # In etcd, update keys:
   # /app/host = "example.com"
   # /app/port = "9000"
   # /app/debug = "true"

**Example: Watching for DELETE Events:**

.. code-block:: python

   from varlord import Config
   from varlord.sources import Etcd
   import threading

   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd(
               host=os.environ.get("ETCD_HOST", "127.0.0.1"),
               port=int(os.environ.get("ETCD_PORT", "2379")),
               prefix="/app/",
               watch=True,
               ca_cert=os.environ.get("ETCD_CA_CERT"),
               cert_key=os.environ.get("ETCD_CERT_KEY"),
               cert_cert=os.environ.get("ETCD_CERT_CERT"),
           ),
       ],
   )

   def watch_changes():
       etcd_source = cfg._sources[0]
       for event in etcd_source.watch():
           if event.event_type == "deleted":
               print(f"Key deleted: {event.key}")
               # Key was deleted, will fall back to default value
           elif event.event_type == "added":
               print(f"Key added: {event.key} = {event.new_value}")
           elif event.event_type == "modified":
               print(f"Key modified: {event.key} = {event.new_value}")

   watch_thread = threading.Thread(target=watch_changes, daemon=True)
   watch_thread.start()

**Using ConfigStore (Recommended):**

For automatic updates, use ``ConfigStore`` which handles watch automatically:

.. code-block:: python

   from varlord import Config
   from varlord.sources import Etcd

   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd(
               host=os.environ.get("ETCD_HOST", "127.0.0.1"),
               port=int(os.environ.get("ETCD_PORT", "2379")),
               prefix="/app/",
               watch=True,
               ca_cert=os.environ.get("ETCD_CA_CERT"),
               cert_key=os.environ.get("ETCD_CERT_KEY"),
               cert_cert=os.environ.get("ETCD_CERT_CERT"),
           ),
       ],
   )

   store = cfg.load_store()  # Automatically enables watch

   def on_change(new_config, diff):
       print(f"Config changed!")
       print(f"  Added: {diff.added}")
       print(f"  Modified: {diff.modified}")
       print(f"  Deleted: {diff.deleted}")

   store.subscribe(on_change)

   # Watch runs automatically in background
   # Changes in etcd will trigger callbacks

Priority with Other Sources
----------------------------

Etcd source can be combined with other sources. Later sources override earlier ones:

.. code-block:: python

   from varlord import Config
   from varlord.sources import Etcd, Env, CLI

   # Priority: Defaults < Etcd < Env < CLI
   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd(
               host=os.environ.get("ETCD_HOST", "127.0.0.1"),
               port=int(os.environ.get("ETCD_PORT", "2379")),
               prefix="/app/",
               ca_cert=os.environ.get("ETCD_CA_CERT"),
               cert_key=os.environ.get("ETCD_CERT_KEY"),
               cert_cert=os.environ.get("ETCD_CERT_CERT"),
           ),  # Load from etcd
           Env(),                           # Env can override etcd
           CLI(),                           # CLI can override all
       ],
   )

Complete Examples
-----------------

Basic Configuration Loading
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from varlord import Config
   from varlord.sources import Etcd
   from dataclasses import dataclass, field

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=8000)
       debug: bool = field(default=False)

   # Assume etcd has:
   # /app/host = "0.0.0.0"
   # /app/port = "9000"
   # /app/debug = "true"

   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd.from_env(prefix="/app/"),
       ],
   )

   app = cfg.load()
   print(app.host)   # "0.0.0.0"
   print(app.port)   # 9000
   print(app.debug)  # True

Nested Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @dataclass
   class DBConfig:
       host: str = field()
       port: int = field(default=5432)

   @dataclass
   class AppConfig:
       api_key: str = field()
       db: DBConfig = field()

   # In etcd:
   # /app/api_key = "secret123"
   # /app/db__host = "db.example.com"
   # /app/db__port = "5432"

   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd.from_env(prefix="/app/"),
       ],
   )

   app = cfg.load()
   print(app.api_key)      # "secret123"
   print(app.db.host)      # "db.example.com"
   print(app.db.port)      # 5432

Best Practices
--------------

1. **Use Environment Variables**: Read environment variables yourself and pass them to ``Etcd()`` instead of hardcoding connection parameters
2. **Use .env Files**: Manage configuration in development with ``.env`` files
3. **Enable Watch**: Enable ``watch=True`` for configurations that need dynamic updates
4. **Use Prefixes**: Use different etcd prefixes for different applications to avoid key conflicts
5. **TLS Security**: Always use TLS certificates in production environments
6. **Model Filtering**: Only keys that match model fields are loaded, ensuring type safety

Troubleshooting
---------------

Connection Failures
~~~~~~~~~~~~~~~~~~~

If you get connection errors:

- Verify etcd is running
- Check host and port are correct
- Verify TLS certificate paths are correct
- Ensure certificates are valid and match the etcd server configuration

Configuration Not Loading
~~~~~~~~~~~~~~~~~~~~~~~~~~

If configuration is not loaded:

- Check key prefix is correct
- Verify key names match model fields (after normalization)
- Ensure model fields are correctly defined
- Check that keys exist in etcd

Watch Not Working
~~~~~~~~~~~~~~~~~~

If watch is not working:

- Verify ``watch=True`` is set
- Ensure watch is running in a separate thread
- Check etcd connection is working
- Verify etcd server supports watch operations

See Also
--------

- :doc:`sources` - Overview of all configuration sources
- :doc:`dynamic_updates` - Dynamic configuration updates
- :doc:`key_mapping` - Key normalization and mapping rules

