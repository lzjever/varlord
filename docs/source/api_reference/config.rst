Config
======

Main Configuration Class
-------------------------

.. autoclass:: varlord.config.Config
   :members:
   :undoc-members:
   :private-members: _model, _sources
   :noindex:

Helper Methods (Internal)
-------------------------

.. note::
   These methods are used internally by the :class:`Config` class. They are documented here
   for advanced users who want to understand the implementation or extend the functionality.

.. automethod:: varlord.config.Config._unwrap_optional_type

.. automethod:: varlord.config.Config._process_dataclass_instances

.. automethod:: varlord.config.Config._process_flat_keys

.. automethod:: varlord.config.Config._collect_nested_keys

.. automethod:: varlord.config.Config._process_nested_keys

.. automethod:: varlord.config.Config._convert_to_dataclasses

.. automethod:: varlord.config.Config._flatten_to_nested

Usage Examples
~~~~~~~~~~~~~~

Basic Usage
^^^^^^^^^^^

.. code-block:: python

   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="localhost")
       port: int = field(default=8000)
       debug: bool = field(default=False)

   # Load configuration from environment variables
   cfg = Config(model=AppConfig, sources=[sources.Env()])
   config = cfg.load()

   print(config.host, config.port, config.debug)

Multiple Sources with Priority
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Load from multiple sources (later sources override earlier ones)
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),        # Priority 1
           sources.DotEnv(),      # Priority 2
           sources.CLI(),         # Priority 3 (highest)
       ],
   )

.. warning::
   **Pitfall**: Source order matters! Later sources override earlier ones.
   If ``PORT`` is set in both environment variables and CLI, the CLI value wins.

With Validation
^^^^^^^^^^^^^^^

.. code-block:: python

   cfg = Config(model=AppConfig, sources=[sources.Env()])
   config = cfg.load(validate=True)

.. note::
   **Best Practice**: Always validate configuration in production to catch errors early.

