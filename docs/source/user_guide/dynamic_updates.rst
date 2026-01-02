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

Fail-Safe Updates
-----------------

If an update fails (validation error, etc.), the old configuration is preserved:

- Old configuration remains active
- Error is logged
- Subscribers are not notified

This ensures your application continues running with a valid configuration.

