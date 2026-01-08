Quick Start
===========

Installation
------------

.. code-block:: bash

   pip install varlord

   # With optional dependencies
   pip install varlord[etcd]

Basic Usage
-----------

**Step 1: Define your configuration model**

.. code-block:: python

   from dataclasses import dataclass, field
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="127.0.0.1")
       port: int = field(default=8000)
       debug: bool = field(default=False)

**Step 2: Create and load configuration**

.. code-block:: python

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Model auto-injected, defaults applied automatically
           sources.CLI(),  # Model auto-injected
       ],
   )

   app = cfg.load()
   print(app.host)  # Can be overridden by env var or CLI arg

**Or use the convenience method:**

.. code-block:: python

   cfg = Config.from_model(
       AppConfig,
       cli=True,  # env_prefix removed - all env vars filtered by model
   )

   app = cfg.load()

Priority Ordering
-----------------

Priority is determined by sources order (later sources override earlier ones):

.. code-block:: python

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Model defaults applied first, then env
           sources.CLI(),  # Highest priority (last)
       ],
   )

For per-key priority rules, use PriorityPolicy:

.. code-block:: python

   from varlord import PriorityPolicy

   cfg = Config(
       model=AppConfig,
       sources=[...],
       policy=PriorityPolicy(
           default=["defaults", "env", "cli"],
           overrides={
               "secrets.*": ["defaults", "etcd"],  # Secrets: skip env
           },
       ),
   )

Validation
----------

Add validation in your model's ``__post_init__``:

.. code-block:: python

   from varlord.validators import validate_range, validate_regex

   @dataclass(frozen=True)
   class AppConfig:
       port: int = 8000
       host: str = "127.0.0.1"

       def __post_init__(self):
           validate_range(self.port, min=1, max=65535)
           validate_regex(self.host, r'^\d+\.\d+\.\d+\.\d+$')

Logging
-------

Enable debug logging to track configuration loading:

.. code-block:: python

   import logging
   from varlord import set_log_level

   set_log_level(logging.DEBUG)
   cfg = Config(...)
   app = cfg.load()  # Will log source loads, merges, conversions

Dynamic Updates
---------------

Use ConfigStore for dynamic configuration updates:

.. code-block:: python

   def on_change(new_config, diff):
       print("Config updated:", diff)

   # Enable watch in the source
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Etcd(..., watch=True),  # Enable watch here
       ],
   )
   
   # load_store() automatically detects and enables watch
   store = cfg.load_store()  # No watch parameter needed
   store.subscribe(on_change)
   current = store.get()  # Thread-safe access

.. note::
   ``load_store()`` automatically detects if any source supports watching.
   You only need to enable watch in the source itself (e.g., ``Etcd(watch=True)``).

