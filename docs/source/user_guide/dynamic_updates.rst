Dynamic Updates
===============

Varlord supports dynamic configuration updates via ``ConfigStore`` and source watch mechanisms.

Basic Usage
-----------

.. code-block:: python

   cfg = Config(...)
   store = cfg.load_store()  # Automatically enables watch if sources support it

   # Get current configuration
   current = store.get()

   # Subscribe to changes
   def on_change(new_config, diff):
       print(f"Added: {diff.added}")
       print(f"Modified: {diff.modified}")
       print(f"Deleted: {diff.deleted}")

   store.subscribe(on_change)

Watch Detection
---------------

``load_store()`` automatically detects if any source supports watching and enables it automatically. You only need to enable watch in the source itself:

.. code-block:: python

   # Enable watch in the source
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Etcd(..., watch=True),  # Enable watch here
           # Model defaults applied automatically
       ],
   )
   
   # load_store() automatically detects and enables watch
   store = cfg.load_store()  # No watch parameter needed

Behavior Without Watch Support
-------------------------------

If no sources support watch, ``load_store()`` and ``subscribe()`` still work, but callbacks will only be called when you manually call ``reload()`` and the configuration has changed:

.. code-block:: python

   # No watch support
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Model defaults applied automatically
       ],
   )
   
   store = cfg.load_store()  # ✅ Works, but watching=False
   store.subscribe(on_change)  # ✅ Works, callback is registered
   
   # Callback will only be called on manual reload with changes
   store.reload()  # If config changed, callback is called

.. note::
   For automatic updates, you must use a source that supports watch (e.g., ``Etcd(watch=True)``).
   Without watch support, callbacks are only called on manual ``reload()`` with configuration changes.

Change Events
-------------

The callback receives:

- ``new_config``: The new configuration instance
- ``diff``: A ``ConfigDiff`` object with:
  - ``added``: New keys
  - ``modified``: Changed keys (old_value, new_value)
  - ``deleted``: Removed keys

Thread Safety
-------------

ConfigStore is thread-safe:

.. code-block:: python

   import threading

   def worker():
       config = store.get()  # Thread-safe
       print(config.host)

   # Multiple threads can safely access store.get()
   for _ in range(10):
       threading.Thread(target=worker).start()

Watch Support
-------------

Currently, only Etcd source supports watch:

.. code-block:: python

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Etcd(..., watch=True),  # Enable watch
           # Model defaults applied automatically
       ],
   )

   store = cfg.load_store()  # Watch automatically enabled if Etcd has watch=True

**Example: Single Callback Subscription:**

.. code-block:: python

   from varlord import Config
   from varlord.sources import Etcd
   from dataclasses import dataclass, field

   @dataclass
   class AppConfig:
       host: str = field()
       port: int = field(default=8000)

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

   store = cfg.load_store()

   def on_change(new_config, diff):
       print(f"Config changed: {new_config.host}:{new_config.port}")
       print(f"  Modified keys: {diff.modified}")

   store.subscribe(on_change)

   # Changes in etcd will automatically trigger callbacks

**Example: Multiple Callbacks:**

.. code-block:: python

   store = cfg.load_store()

   def callback1(new_config, diff):
       print(f"Callback 1: {new_config.host}")

   def callback2(new_config, diff):
       print(f"Callback 2: {new_config.port}")

   store.subscribe(callback1)
   store.subscribe(callback2)

   # Both callbacks will be called on configuration changes

**Example: Handling Added, Modified, and Deleted Keys:**

.. code-block:: python

   def on_change(new_config, diff):
       if diff.added:
           print(f"New keys added: {diff.added}")
       if diff.modified:
           print(f"Keys modified: {diff.modified}")
           for key in diff.modified:
               old_val, new_val = diff.modified[key]
               print(f"  {key}: {old_val} -> {new_val}")
       if diff.deleted:
           print(f"Keys deleted: {diff.deleted}")

   store.subscribe(on_change)

**Example: Multiple Sources with Watch:**

.. code-block:: python

   from varlord import Config
   from varlord.sources import Etcd, Env

   # Multiple etcd sources with watch
   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd(host="...", prefix="/app1/", watch=True),  # First source
           Etcd(host="...", prefix="/app2/", watch=True),  # Second source (overrides first)
           Env(),  # Env overrides both etcd sources
       ],
   )

   store = cfg.load_store()  # Watch enabled for both etcd sources

   # Changes in either etcd source will trigger callbacks
   # Priority: /app1/ < /app2/ < Env

**Example: Etcd with Non-Watch Sources:**

.. code-block:: python

   from varlord import Config
   from varlord.sources import Etcd, Env

   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd(host="...", prefix="/app/", watch=True),  # Has watch
           Env(),  # No watch, but can override etcd
       ],
   )

   store = cfg.load_store()  # Watch enabled (because etcd supports it)

   def on_change(new_config, diff):
       print(f"Config updated: {new_config.host}:{new_config.port}")

   store.subscribe(on_change)

   # Changes in etcd will trigger callbacks
   # But env variables still override etcd values

**Example: Load() vs Store.get() Consistency:**

.. code-block:: python

   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd.from_env(prefix="/app/", watch=True),
       ],
   )

   store = cfg.load_store()

   # Both methods return the same values
   config_from_load = cfg.load()
   config_from_store = store.get()

   assert config_from_load.host == config_from_store.host
   assert config_from_load.port == config_from_store.port

   # After etcd changes, both still return consistent values
   # (after watch processes the change)

Fail-Safe Updates
-----------------

If an update fails (validation error, etc.), the old configuration is preserved:

- Old configuration remains active
- Error is logged
- Subscribers are not notified

This ensures your application continues running with a valid configuration.

**Example: Handling Update Failures:**

.. code-block:: python

   @dataclass
   class AppConfig:
       port: int = field(default=8000)

   cfg = Config(
       model=AppConfig,
       sources=[
           Etcd.from_env(prefix="/app/", watch=True),
       ],
   )

   store = cfg.load_store()

   def on_change(new_config, diff):
       print(f"Config updated: {new_config.port}")

   store.subscribe(on_change)

   # If etcd has invalid value (e.g., "invalid"), update fails
   # Old configuration (port=8000) remains active
   # Callback is not called

