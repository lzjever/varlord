Etcd Source Example
===================

This example demonstrates how to use the Etcd source with TLS authentication and dynamic updates.

Prerequisites
-------------

1. Install etcd support:

   .. code-block:: bash

      pip install varlord[etcd]

2. Have a running etcd instance with TLS authentication

3. Set up environment variables or provide certificates

Example: Basic Etcd Configuration
----------------------------------

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config
   from varlord.sources import Etcd

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=8000)
       debug: bool = field(default=False)

   # Create etcd source with TLS
   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd(
               host="192.168.0.220",
               port=2379,
               prefix="/app/",
               ca_cert="./cert/AgentsmithLocal.cert.pem",
               cert_key="./cert/etcd-client-lzj-local/key.pem",
               cert_cert="./cert/etcd-client-lzj-local/cert.pem",
           ),
       ],
   )

   app = cfg.load()
   print(f"Host: {app.host}")
   print(f"Port: {app.port}")
   print(f"Debug: {app.debug}")

Example: Using from_env()
--------------------------

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config
   from varlord.sources import Etcd

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=8000)
       debug: bool = field(default=False)

   # Set environment variables:
   # export ETCD_HOST=192.168.0.220
   # export ETCD_PORT=2379
   # export ETCD_CA_CERT=./cert/AgentsmithLocal.cert.pem
   # export ETCD_CERT_KEY=./cert/etcd-client-lzj-local/key.pem
   # export ETCD_CERT_CERT=./cert/etcd-client-lzj-local/cert.pem

   # Create etcd source from environment variables
   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd.from_env(prefix="/app/"),
       ],
   )

   app = cfg.load()
   print(f"Host: {app.host}")
   print(f"Port: {app.port}")

Example: Nested Configuration
------------------------------

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config
   from varlord.sources import Etcd

   @dataclass
   class DBConfig:
       host: str = field()
       port: int = field(default=5432)

   @dataclass
   class AppConfig:
       api_key: str = field()
       db: DBConfig = field()

   # In etcd, use double underscore for nesting:
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
   print(f"API Key: {app.api_key}")
   print(f"DB Host: {app.db.host}")
   print(f"DB Port: {app.db.port}")

Example: Dynamic Updates with Watch
------------------------------------

**Using ConfigStore (Recommended):**

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config
   from varlord.sources import Etcd

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=8000)

   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd.from_env(prefix="/app/", watch=True),
       ],
   )

   # Load store (automatically enables watch)
   store = cfg.load_store()

   # Initial configuration
   config = store.get()
   print(f"Initial config: {config.host}:{config.port}")

   # Subscribe to changes
   def on_change(new_config, diff):
       print(f"Config changed!")
       print(f"  Modified: {diff.modified}")
       print(f"  New config: {new_config.host}:{new_config.port}")

   store.subscribe(on_change)

   # Watch runs automatically in background
   # Changes in etcd will trigger callbacks
   # Your application continues running here

**Using Source Watch Directly:**

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config
   from varlord.sources import Etcd
   import threading
   import time

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=8000)

   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd.from_env(prefix="/app/", watch=True),
       ],
   )

   # Load initial configuration
   app = cfg.load()
   print(f"Initial config: {app.host}:{app.port}")

   # Start watching for changes
   def watch_changes():
       etcd_source = cfg._sources[0]
       for event in etcd_source.watch():
           print(f"Config changed: {event.key} = {event.new_value} (type: {event.event_type})")
           # Reload configuration
           app = cfg.load()
           print(f"Updated config: {app.host}:{app.port}")

   watch_thread = threading.Thread(target=watch_changes, daemon=True)
   watch_thread.start()

   # Keep main thread alive
   time.sleep(60)

**Example: Multiple Callbacks:**

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config
   from varlord.sources import Etcd

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=8000)

   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd.from_env(prefix="/app/", watch=True),
       ],
   )

   store = cfg.load_store()

   def callback1(new_config, diff):
       print(f"Callback 1: host changed to {new_config.host}")

   def callback2(new_config, diff):
       print(f"Callback 2: port changed to {new_config.port}")

   store.subscribe(callback1)
   store.subscribe(callback2)

   # Both callbacks will be called on configuration changes

Example: Multiple Sources with Priority
---------------------------------------

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config
   from varlord.sources import Etcd, Env, CLI

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=8000)

   # Priority: Defaults < Etcd < Env < CLI
   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd.from_env(prefix="/app/"),  # Load from etcd
           Env(),                           # Env can override etcd
           CLI(),                           # CLI can override all
       ],
   )

   app = cfg.load()
   # CLI arguments > Environment variables > Etcd > Defaults

