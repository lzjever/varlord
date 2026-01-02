Custom Sources
==============

You can create custom configuration sources by implementing the ``Source`` interface.
This allows you to load configuration from any source you need (databases, APIs, files, etc.).

Basic Implementation
--------------------

A minimal custom source must implement:

1. ``name`` property: Returns a unique name for the source
2. ``load()`` method: Returns a mapping of configuration key-value pairs

Example:

.. code-block:: python

   from varlord.sources.base import Source
   from typing import Mapping, Any
   
   class DatabaseSource(Source):
       """Load configuration from a database."""
       
       def __init__(self, connection_string: str):
           self.connection_string = connection_string
       
       @property
       def name(self) -> str:
           return "database"
       
       def load(self) -> Mapping[str, Any]:
           # Your implementation here
           # Return a dict with normalized keys (e.g., "db.host" for nested configs)
           return {
               "host": "localhost",
               "port": 5432,
               "db.name": "myapp",
           }

Key Normalization
-----------------

Configuration keys should be normalized to use dot notation for nested values:

- Flat keys: ``"host"``, ``"port"``
- Nested keys: ``"db.host"``, ``"db.port"``, ``"api.timeout"``

This allows the configuration model to use nested dataclasses:

.. code-block:: python

   @dataclass
   class DatabaseConfig:
       host: str
       port: int
   
   @dataclass
   class AppConfig:
       db: DatabaseConfig
       api_timeout: int

The source should return ``{"db.host": "...", "db.port": 123, "api_timeout": 30}``,
and Varlord will automatically map it to the nested structure.

Watch Support (Optional)
------------------------

To enable dynamic updates, implement watch support:

1. Override ``supports_watch()`` to return ``True`` when watch is enabled
2. Implement ``watch()`` to yield ``ChangeEvent`` objects

Example:

.. code-block:: python

   from varlord.sources.base import Source, ChangeEvent
   from typing import Iterator
   import time
   
   class FileSource(Source):
       """Load configuration from a file with watch support."""
       
       def __init__(self, file_path: str, watch: bool = False):
           self.file_path = file_path
           self._watch = watch
       
       @property
       def name(self) -> str:
           return "file"
       
       def supports_watch(self) -> bool:
           """Enable watch support when requested."""
           return self._watch
       
       def load(self) -> Mapping[str, Any]:
           # Load from file
           with open(self.file_path) as f:
               # Parse file and return config dict
               return {"key": "value"}
       
       def watch(self) -> Iterator[ChangeEvent]:
           """Watch for file changes."""
           if not self._watch:
               return iter([])
           
           from watchdog.observers import Observer
           from watchdog.events import FileSystemEventHandler
           
           # Implement file watching logic
           # Yield ChangeEvent objects when file changes
           while True:
               # Monitor file...
               yield ChangeEvent(
                   key="some_key",
                   old_value="old",
                   new_value="new",
                   event_type="modified"
               )

Watch Implementation Requirements
-----------------------------------

When implementing ``watch()``:

1. **Return empty iterator when disabled**: If ``supports_watch()`` returns ``False``,
   ``watch()`` should return ``iter([])``.

2. **Yield ChangeEvent objects**: Each change should be represented as a ``ChangeEvent``:

   .. code-block:: python

      ChangeEvent(
          key="config_key",      # The configuration key that changed
          old_value="old_value",  # Previous value (None if key was added)
          new_value="new_value",  # New value (None if key was removed)
          event_type="modified"   # One of: "added", "modified", "deleted"
      )

3. **Handle errors gracefully**: Watch loops should handle connection errors, timeouts,
   and other exceptions. Consider implementing exponential backoff for reconnection.

4. **Thread safety**: The watch method will be called in a separate thread. Ensure
   your implementation is thread-safe.

Complete Example
----------------

Here's a complete example of a custom source that loads from a JSON file:

.. code-block:: python

   from varlord.sources.base import Source, ChangeEvent
   from typing import Mapping, Any, Iterator
   import json
   import os
   from pathlib import Path
   
   class JSONFileSource(Source):
       """Load configuration from a JSON file."""
       
       def __init__(self, file_path: str, watch: bool = False):
           self.file_path = Path(file_path)
           self._watch = watch
           self._last_modified = None
       
       @property
       def name(self) -> str:
           return "json_file"
       
       def supports_watch(self) -> bool:
           return self._watch
       
       def load(self) -> Mapping[str, Any]:
           """Load configuration from JSON file."""
           if not self.file_path.exists():
               return {}
           
           with open(self.file_path) as f:
               data = json.load(f)
           
           # Normalize nested dicts to dot notation
           def normalize(data, prefix=""):
               result = {}
               for key, value in data.items():
                   full_key = f"{prefix}.{key}" if prefix else key
                   if isinstance(value, dict):
                       result.update(normalize(value, full_key))
                   else:
                       result[full_key] = value
               return result
           
           return normalize(data)
       
       def watch(self) -> Iterator[ChangeEvent]:
           """Watch for file changes."""
           if not self._watch:
               return iter([])
           
           import time
           
           while True:
               try:
                   if self.file_path.exists():
                       current_modified = self.file_path.stat().st_mtime
                       
                       if self._last_modified is not None and current_modified != self._last_modified:
                           # File changed, reload and yield events
                           old_data = self._last_data if hasattr(self, '_last_data') else {}
                           new_data = self.load()
                           
                           # Compare and yield changes
                           all_keys = set(old_data.keys()) | set(new_data.keys())
                           for key in all_keys:
                               old_val = old_data.get(key)
                               new_val = new_data.get(key)
                               
                               if old_val != new_val:
                                   if old_val is None:
                                       event_type = "added"
                                   elif new_val is None:
                                       event_type = "deleted"
                                   else:
                                       event_type = "modified"
                                   
                                   yield ChangeEvent(
                                       key=key,
                                       old_value=old_val,
                                       new_value=new_val,
                                       event_type=event_type
                                   )
                       
                       self._last_modified = current_modified
                       self._last_data = new_data
                   
                   time.sleep(1)  # Check every second
               except Exception as e:
                   # Log error and continue
                   print(f"Error watching file: {e}")
                   time.sleep(5)  # Wait longer on error

Using Custom Sources
--------------------

Once you've created a custom source, use it like any built-in source:

.. code-block:: python

   from varlord import Config
   from my_sources import JSONFileSource
   
   cfg = Config(
       model=AppConfig,
       sources=[
           JSONFileSource("config.json", watch=True),
           sources.Env(),  # Model auto-injected, defaults applied automatically
       ],
   )
   
   store = cfg.load_store()
   config = store.get()

Best Practices
--------------

1. **Normalize keys consistently**: Use dot notation for nested values (e.g., ``"db.host"``)

2. **Handle missing sources gracefully**: If your source might not be available (e.g., file doesn't exist),
   return an empty dict ``{}`` rather than raising an exception.

3. **Type conversion**: Sources return string values by default. Varlord will automatically convert
   them to the appropriate types based on your model. However, you can return typed values if
   your source has type information.

4. **Error handling**: Implement robust error handling in ``load()`` and ``watch()`` methods.
   Failures should be logged but not crash the application.

5. **Thread safety**: If your source uses shared state, ensure it's thread-safe, especially
   if you implement watch support.

6. **Documentation**: Document your source's behavior, especially:
   - How keys are normalized
   - What happens when the source is unavailable
   - Watch behavior and limitations

