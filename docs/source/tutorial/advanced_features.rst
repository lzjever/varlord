Advanced Features
=================

In this tutorial, you'll learn about advanced features like custom priority
policies, custom sources, and best practices for complex scenarios.

Learning Objectives
-------------------

By the end of this tutorial, you'll be able to:

- Use ``PriorityPolicy`` for per-key priority rules
- Create custom configuration sources
- Understand advanced patterns and best practices

Step 1: Custom Priority with PriorityPolicy
---------------------------------------------

Sometimes you need different priority orders for different keys. Use
``PriorityPolicy``:

.. code-block:: python
   :linenos:

   import os
   from dataclasses import dataclass, field
   from varlord import Config, sources, PriorityPolicy

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)
       api_key: str = field(default="default-key")

   # Set environment variables (no prefix needed)
   os.environ["HOST"] = "env-host"
   os.environ["PORT"] = "9000"
   os.environ["API_KEY"] = "env-key"

   # Define priority policy
   policy = PriorityPolicy(
       rules={
           "host": ["defaults", "env"],  # Env overrides defaults
           "port": ["defaults", "env"],  # Env overrides defaults
           "api_key": ["env", "defaults"],  # Defaults override env (unusual!)
       }
   )

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Defaults applied automatically
       ],
       policy=policy,
   )

   app = cfg.load()
   print(f"Host: {app.host}")      # From env: env-host
   print(f"Port: {app.port}")      # From env: 9000
   print(f"API Key: {app.api_key}")  # From defaults: default-key (env overridden!)

**Expected Output**:

.. code-block:: text

   Host: env-host
   Port: 9000
   API Key: default-key

**Key Points**:

- ``PriorityPolicy`` allows per-key priority rules
- Later sources in the list override earlier ones
- Useful when you need different override behavior for different keys

Step 2: Creating Custom Sources
---------------------------------

You can create custom sources by extending the ``Source`` base class:

.. code-block:: python
   :linenos:

   import json
   from typing import Mapping, Any
   from dataclasses import dataclass
   from varlord import Config
   from varlord.sources.base import Source

   class JSONFileSource(Source):
       """Source that loads configuration from a JSON file."""

       def __init__(self, file_path: str):
           self._file_path = file_path

       @property
       def name(self) -> str:
           return "json_file"

       def load(self) -> Mapping[str, Any]:
           """Load configuration from JSON file."""
           try:
               with open(self._file_path, "r") as f:
                   data = json.load(f)
                   # Normalize keys to lowercase for consistency
                   return {k.lower(): v for k, v in data.items()}
           except FileNotFoundError:
               return {}  # Return empty if file doesn't exist
           except json.JSONDecodeError:
               return {}  # Return empty if JSON is invalid

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)

   # Create JSON file
   import tempfile
   with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
       json.dump({"host": "json-host", "port": 7000}, f)
       json_path = f.name

   # Use custom source
   cfg = Config(
       model=AppConfig,
       sources=[
           JSONFileSource(json_path),  # Defaults applied automatically
       ],
   )

   app = cfg.load()
   print(f"Host: {app.host}")  # From JSON: json-host
   print(f"Port: {app.port}")  # From JSON: 7000

   # Cleanup
   import os
   os.unlink(json_path)

**Expected Output**:

.. code-block:: text

   Host: json-host
   Port: 7000

**Key Points**:

- Extend ``Source`` base class
- Implement ``name`` property and ``load()`` method
- Return a dictionary with normalized keys (lowercase, dot notation)
- Handle errors gracefully (return empty dict on failure)

Step 3: Custom Source with Watch Support
-----------------------------------------

For sources that support watching, implement ``supports_watch()`` and ``watch()``:

.. code-block:: python
   :linenos:

   import time
   from typing import Iterator
   from varlord.sources.base import Source, ChangeEvent

   class PollingFileSource(Source):
       """Source that polls a file for changes."""

       def __init__(self, file_path: str, poll_interval: float = 1.0):
           self._file_path = file_path
           self._poll_interval = poll_interval
           self._last_mtime = 0

       @property
       def name(self) -> str:
           return "polling_file"

       def supports_watch(self) -> bool:
           """Declare that this source supports watching."""
           return True

       def load(self) -> Mapping[str, Any]:
           """Load current configuration from file."""
           # Implementation similar to JSONFileSource
           return {}

       def watch(self) -> Iterator[ChangeEvent]:
           """Watch for file changes by polling."""
           import os
           while True:
               try:
                   current_mtime = os.path.getmtime(self._file_path)
                   if current_mtime > self._last_mtime:
                       self._last_mtime = current_mtime
                       # Load new configuration
                       new_config = self.load()
                       # Yield change events for all keys
                       for key, value in new_config.items():
                           yield ChangeEvent(key=key, value=value, source=self.name)
               except FileNotFoundError:
                   pass  # File doesn't exist yet
               time.sleep(self._poll_interval)

**Key Points**:

- Implement ``supports_watch()`` returning ``True``
- Implement ``watch()`` method that yields ``ChangeEvent`` objects
- Watch is automatically enabled when using ``load_store()``

Step 4: Best Practices for Complex Configurations
---------------------------------------------------

Here are some best practices for complex scenarios:

**1. Organize Configuration by Domain**

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class DatabaseConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)

   @dataclass(frozen=True)
   class CacheConfig:
       host: str = field(default="localhost")
       port: int = field(default=6379)

   @dataclass(frozen=True)
   class AppConfig:
       db: DatabaseConfig = field(default_factory=lambda: DatabaseConfig())
       cache: CacheConfig = field(default_factory=lambda: CacheConfig())

**2. Use Environment-Specific Defaults**

.. code-block:: python
   :linenos:

   import os

   @dataclass(frozen=True)
   class AppConfig:
       debug: bool = field(default=os.getenv("ENV") != "production")
       log_level: str = field(default="DEBUG" if os.getenv("ENV") != "production" else "INFO")

**3. Validate Critical Fields**

.. code-block:: python
   :linenos:

   from dataclasses import field
   from varlord.validators import validate_not_empty, validate_port

   @dataclass(frozen=True)
   class AppConfig:
       api_key: str = field(default="")

       def __post_init__(self):
           validate_not_empty(self.api_key)  # Fail fast if missing

Step 5: Complete Advanced Example
----------------------------------

Here's a complete example combining multiple advanced features:

.. code-block:: python
   :name: advanced_features_complete
   :linenos:

   import os
   from dataclasses import dataclass, field
   from varlord import Config, sources, PriorityPolicy
   from varlord.validators import validate_port, validate_not_empty

   @dataclass(frozen=True)
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)

       def __post_init__(self):
           validate_not_empty(self.host)
           validate_port(self.port)

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)
       db: DBConfig = field(default_factory=lambda: DBConfig())

       def __post_init__(self):
           validate_port(self.port)

   def main():
       # Set environment variables (no prefix needed)
       os.environ["HOST"] = "0.0.0.0"
       os.environ["PORT"] = "9000"
       os.environ["DB__HOST"] = "db.example.com"
       os.environ["DB__PORT"] = "3306"

       # Use PriorityPolicy for fine-grained control
       policy = PriorityPolicy(
           rules={
               "port": ["defaults", "env"],  # Env overrides defaults
               "db.port": ["env", "defaults"],  # Defaults override env (example)
           }
       )

       cfg = Config(
           model=AppConfig,
           sources=[
               sources.Env(),  # Model defaults applied automatically
           ],
           policy=policy,
       )

       app = cfg.load()

       print("Advanced configuration loaded:")
       print(f"  App: {app.host}:{app.port}")
       print(f"  DB: {app.db.host}:{app.db.port}")

   if __name__ == "__main__":
       main()

**Expected Output**:

.. code-block:: text

   Advanced configuration loaded:
     App: 0.0.0.0:9000
     DB: db.example.com:3306

Common Pitfalls
---------------

**Pitfall 1: Overusing PriorityPolicy**

.. code-block:: python
   :emphasize-lines: 3-7

   # Don't do this for simple cases
   policy = PriorityPolicy(
       rules={
           "host": ["defaults", "env"],
           "port": ["defaults", "env"],
           # ... same rule for every key
       }
   )

**Solution**: Only use ``PriorityPolicy`` when you need different priority
rules for different keys. For uniform priority, just order your sources
correctly.

**Pitfall 2: Not normalizing keys in custom sources**

.. code-block:: python
   :emphasize-lines: 3

   def load(self) -> Mapping[str, Any]:
       data = json.load(f)
       return data  # Keys might be uppercase or inconsistent!

**Solution**: Always normalize keys to lowercase and use dot notation for
consistency with other sources.

**Pitfall 3: Not handling errors in custom sources**

.. code-block:: python
   :emphasize-lines: 3

   def load(self) -> Mapping[str, Any]:
       with open(self._file_path) as f:
           return json.load(f)  # Raises exception if file doesn't exist!

**Solution**: Always handle errors gracefully and return empty dict on failure.

Best Practices
--------------

1. **Keep it simple**: Only use advanced features when necessary
2. **Normalize keys**: Always use lowercase and dot notation
3. **Handle errors**: Custom sources should be fail-safe
4. **Document custom sources**: Explain what they do and how to use them
5. **Test thoroughly**: Advanced features need more testing

Summary
-------

You've now learned:

- How to use ``PriorityPolicy`` for per-key priority rules
- How to create custom configuration sources
- How to implement watch support in custom sources
- Best practices for complex configurations

You're now ready to use Varlord in production! For more details, see the
:doc:`../user_guide/index` and :doc:`../api_reference/index`.

