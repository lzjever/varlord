Configuration Sources
=====================

Varlord supports multiple configuration sources, each implementing the ``Source`` interface.

Defaults Source
---------------

Model defaults are automatically applied as the base layer. You no longer need to explicitly include ``sources.Defaults`` in your sources list.

**Note**: The ``Defaults`` source is now internal. Model defaults are automatically extracted and applied first, before any user-provided sources.

Environment Variables
---------------------

Loads from environment variables, filtered by model fields:

.. code-block:: python

   source = sources.Env(model=AppConfig)  # Model required
   # Only loads environment variables that match model fields
   # HOST -> host, PORT -> port, etc.
   # Converts DB__HOST to db.host (nested keys)

**Important**: The ``prefix`` parameter has been removed. All environment variables are filtered by model fields. Only variables that map to model fields are loaded.

CLI Arguments
-------------

Loads from command-line arguments, filtered by model fields:

.. code-block:: python

   source = sources.CLI(model=AppConfig)  # Model required (auto-injected by Config)
   # Only parses arguments for model fields
   # Parses --host, --port, --debug, etc.
   # Uses field metadata for help text and required flags

DotEnv Files
------------

Loads from `.env` files, filtered by model fields (requires ``varlord[dotenv]``):

.. code-block:: python

   source = sources.DotEnv(".env", model=AppConfig)  # Model required
   # Only loads variables that match model fields

Etcd
----

Loads from etcd with optional watch support, filtered by model fields (requires ``varlord[etcd]``):

.. code-block:: python

   source = sources.Etcd(
       host="127.0.0.1",
       port=2379,
       prefix="/app/",
       watch=True,  # Enable dynamic updates
       model=AppConfig,  # Model required (auto-injected by Config)
   )
   # Only loads keys that match model fields

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

