Configuration Sources
=====================

Varlord supports multiple configuration sources, each implementing the ``Source`` interface.

Defaults Source
---------------

Loads default values from your dataclass model:

.. code-block:: python

   from varlord import sources

   source = sources.Defaults(model=AppConfig)
   config = source.load()  # Returns default values

Environment Variables
---------------------

Loads from environment variables with optional prefix:

.. code-block:: python

   source = sources.Env(prefix="APP_")
   # Loads APP_HOST, APP_PORT, etc.
   # Converts APP_DB__HOST to db.host (nested keys)

CLI Arguments
-------------

Loads from command-line arguments:

.. code-block:: python

   source = sources.CLI()  # Model auto-injected from Config
   # Parses --host, --port, --debug, etc.

DotEnv Files
------------

Loads from `.env` files (requires ``varlord[dotenv]``):

.. code-block:: python

   source = sources.DotEnv(".env")

Etcd
----

Loads from etcd with optional watch support (requires ``varlord[etcd]``):

.. code-block:: python

   source = sources.Etcd(
       host="127.0.0.1",
       port=2379,
       prefix="/app/",
       watch=True,  # Enable dynamic updates
   )

Custom Sources
--------------

Create custom sources by implementing the ``Source`` interface:

.. code-block:: python

   from varlord.sources.base import Source, ChangeEvent

   class CustomSource(Source):
       def __init__(self, watch=False):
           self._watch = watch
       
       @property
       def name(self) -> str:
           return "custom"

       def load(self):
           return {"key": "value"}
       
       # To enable watch support, you MUST override supports_watch()
       def supports_watch(self) -> bool:
           """Must override to enable watch support"""
           return self._watch
       
       def watch(self):
           """Implement watch logic"""
           if not self._watch:
               return iter([])  # Return empty iterator when watch is disabled
           
           # Yield ChangeEvent objects when configuration changes
           while True:
               # Monitor for changes...
               yield ChangeEvent(
                   key="key",
                   old_value="old",
                   new_value="new",
                   event_type="modified"
               )

Watch Support Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~

To enable watch support in a custom source, you **must**:

1. Override ``supports_watch()`` to return ``True`` when watch is enabled
2. Implement ``watch()`` to yield ``ChangeEvent`` objects when watch is enabled
3. Return an empty iterator from ``watch()`` when watch is disabled

**Important**: The ``supports_watch()`` method is the only way to indicate watch support. Simply overriding ``watch()`` is not sufficient - you must also override ``supports_watch()``.

