Dynamic Updates
===============

In this tutorial, you'll learn how to use ``ConfigStore`` for dynamic
configuration updates, including watching for changes in etcd.

Learning Objectives
-------------------

By the end of this tutorial, you'll be able to:

- Use ``ConfigStore`` for runtime configuration access
- Subscribe to configuration changes
- Enable automatic updates from watchable sources (e.g., etcd)

Step 1: Basic ConfigStore Usage
---------------------------------

``ConfigStore`` provides thread-safe access to configuration:

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0", metadata={"optional": True})
       port: int = field(default=8000, metadata={"optional": True})

   cfg = Config(
       model=AppConfig,
       sources=[],  # Defaults are automatically applied
   )

   # Load as store (supports dynamic updates)
   store = cfg.load_store()

   # Access configuration
   app = store.get()
   print(f"Host: {app.host}, Port: {app.port}")

   # Access via store.get() (store.host is not supported)
   print(f"Host: {store.get().host}, Port: {store.get().port}")

**Expected Output**:

.. code-block:: text

   Host: 0.0.0.0, Port: 8000
   Host: 0.0.0.0, Port: 8000

**Key Points**:

- ``load_store()`` returns a ``ConfigStore`` instance
- ``store.get()`` returns the current configuration model instance
- Access fields via ``store.get().host``, not ``store.host``

Step 2: Manual Reload
----------------------

You can manually reload configuration:

.. code-block:: python
   :linenos:

   import os
   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       port: int = field(default=8000, metadata={"optional": True})

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Defaults applied automatically
       ],
   )

   store = cfg.load_store()

   # Initial value
   print(f"Initial port: {store.get().port}")

   # Change environment variable (no prefix needed)
   os.environ["PORT"] = "9000"

   # Manually reload
   store.reload()

   # New value
   print(f"Updated port: {store.get().port}")

**Expected Output**:

.. code-block:: text

   Initial port: 8000
   Updated port: 9000

**Important**: Manual reload is useful when sources don't support automatic
watching (like environment variables or CLI arguments).

Step 3: Subscribing to Changes
-------------------------------

You can subscribe to configuration changes:

.. code-block:: python
   :linenos:

   import os
   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       port: int = field(default=8000, metadata={"optional": True})

   def on_config_change(new_config, diff):
       print(f"Configuration changed!")
       print(f"  Added: {diff.added}")
       print(f"  Modified: {diff.modified}")
       print(f"  Deleted: {diff.deleted}")
       print(f"  New port: {new_config.port}")

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Defaults applied automatically
       ],
   )

   store = cfg.load_store()
   store.subscribe(on_config_change)

   # Change configuration (no prefix needed)
   os.environ["PORT"] = "9000"
   store.reload()  # Triggers callback

**Expected Output**:

.. code-block:: text

   Configuration changed!
     Added: set()
     Modified: {'port'}
     Deleted: set()
     New port: 9000

**Key Points**:

- Subscribers are called when configuration changes
- ``diff`` object shows what changed
- Callbacks receive the new configuration and diff

Step 4: Automatic Updates with Etcd (Optional)
-----------------------------------------------

If you have etcd installed, you can enable automatic watching:

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       port: int = field(default=8000, metadata={"optional": True})
       timeout: int = field(default=30, metadata={"optional": True})

   def on_config_change(new_config, diff):
       print(f"Configuration updated from etcd!")
       print(f"  Changes: {diff.modified}")

   # Configure etcd source with watch enabled
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Etcd(
               host="127.0.0.1",
               port=2379,
               prefix="/app/",
               watch=True,  # Enable automatic watching
           ),  # Defaults applied automatically
       ],
   )

   store = cfg.load_store()
   store.subscribe(on_config_change)

   print("Watching etcd for changes...")
   print("Update /app/port or /app/timeout in etcd to see changes")
   # In production, your application would continue running here

**Note**: This requires etcd to be running and the ``etcd3`` package installed.
Changes in etcd will automatically trigger configuration reloads and callbacks.

**Key Points**:

- ``watch=True`` enables automatic watching
- Changes in etcd automatically update configuration
- Subscribers are notified of changes
- Watch is only enabled if the source supports it (via ``supports_watch()``)

Step 5: Thread-Safe Access
---------------------------

``ConfigStore`` is thread-safe:

.. code-block:: python
   :linenos:

   import threading
   import time
   from dataclasses import dataclass, field
   from varlord import Config

   @dataclass(frozen=True)
   class AppConfig:
       counter: int = field(default=0, metadata={"optional": True})

   cfg = Config(
       model=AppConfig,
       sources=[],  # Defaults applied automatically
   )

   store = cfg.load_store()

   def reader_thread():
       for _ in range(10):
           config = store.get()
           print(f"Reader: counter = {config.counter}")
           time.sleep(0.1)

   # Start reader thread
   thread = threading.Thread(target=reader_thread)
   thread.start()

   # Main thread can also access safely
   for i in range(5):
       print(f"Main: counter = {store.get().counter}")
       time.sleep(0.2)

   thread.join()

**Expected Output** (example):

.. code-block:: text

   Main: counter = 0
   Reader: counter = 0
   Reader: counter = 0
   Main: counter = 0
   Reader: counter = 0
   ...

**Key Points**:

- Multiple threads can safely access ``ConfigStore``
- Configuration snapshots are atomic
- No locking required for reading

Step 6: Complete Example
------------------------

Here's a complete example with subscriptions and manual reload:

.. code-block:: python
   :name: dynamic_updates_complete
   :linenos:

   import os
   import time
   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0", metadata={"optional": True})
       port: int = field(default=8000, metadata={"optional": True})
       debug: bool = field(default=False, metadata={"optional": True})

   def on_config_change(new_config, diff):
       print(f"\n[Callback] Configuration changed:")
       if diff.modified:
           for key in diff.modified:
               print(f"  {key} was modified")
       if diff.added:
           for key in diff.added:
               print(f"  {key} was added")
       print(f"  Current config: {new_config.host}:{new_config.port}")

   def main():
       cfg = Config(
           model=AppConfig,
           sources=[
               sources.Env(),  # Defaults applied automatically
           ],
       )

       store = cfg.load_store()
       store.subscribe(on_config_change)

       print("Initial configuration:")
       config = store.get()
       print(f"  {config.host}:{config.port} (debug={config.debug})")

       # Simulate configuration changes
       print("\n--- Changing port ---")
       os.environ["PORT"] = "9000"
       store.reload()

       time.sleep(0.5)

       print("\n--- Changing host ---")
       os.environ["HOST"] = "192.168.1.1"
       store.reload()

       time.sleep(0.5)

       print("\n--- Final configuration ---")
       config = store.get()
       print(f"  {config.host}:{config.port} (debug={config.debug})")

   if __name__ == "__main__":
       main()

**Expected Output**:

.. code-block:: text

   Initial configuration:
     0.0.0.0:8000 (debug=False)

   --- Changing port ---

   [Callback] Configuration changed:
     port was modified
     Current config: 0.0.0.0:9000

   --- Changing host ---

   [Callback] Configuration changed:
     host was modified
     Current config: 192.168.1.1:9000

   --- Final configuration ---
     192.168.1.1:9000 (debug=False)

Common Pitfalls
---------------

**Pitfall 1: Expecting automatic updates from non-watchable sources**

.. code-block:: python
   :emphasize-lines: 3-4

   store = cfg.load_store()
   # Change environment variable
   os.environ["PORT"] = "9000"
   # Configuration won't update automatically!
   print(store.get().port)  # Still 8000

**Solution**: Environment variables and CLI arguments don't support automatic
watching. Use ``store.reload()`` to manually refresh, or use etcd for
automatic updates.

**Pitfall 2: Modifying configuration objects**

.. code-block:: python
   :emphasize-lines: 2

   config = store.get()
   config.port = 9000  # This will fail - config is frozen!

**Solution**: Configuration objects are immutable (frozen). To change
configuration, update the source (e.g., etcd, environment) and reload.

**Pitfall 3: Not handling exceptions in callbacks**

.. code-block:: python
   :emphasize-lines: 2-3

   def on_config_change(new_config, diff):
       raise Exception("Error in callback")  # This won't break the update
       # But it will be silently ignored

**Solution**: Always handle exceptions in callbacks. The store will continue
working even if a callback fails.

Best Practices
--------------

1. **Use ConfigStore for long-running applications**: Enables dynamic updates
2. **Subscribe to changes**: React to configuration updates
3. **Use etcd for automatic updates**: When you need real-time configuration
4. **Handle reload errors gracefully**: Updates are fail-safe

Next Steps
----------

Now that you understand dynamic updates, let's explore :doc:`advanced_features`
like custom priority policies and custom sources.

