Priority Ordering
=================

Varlord provides two ways to control configuration priority.

Method 1: Sources Order (Recommended)
--------------------------------------

Priority is determined by the order of sources in the list. **Later sources override earlier ones**.

.. code-block:: python

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Defaults(model=AppConfig),  # Lowest priority (first)
           sources.Env(prefix="APP_"),         # Medium priority
           sources.CLI(),                      # Highest priority (last)
       ],
   )
   
   # Result: CLI overrides Env, Env overrides Defaults

This is the simplest and most intuitive way. Just reorder the sources list.

**Key Point**: Later sources in the list have higher priority and override earlier ones.

Method 2: PriorityPolicy (Advanced)
------------------------------------

Use ``PriorityPolicy`` when you need different priority rules for different keys:

.. code-block:: python

   from varlord import PriorityPolicy

   cfg = Config(
       model=AppConfig,
       sources=[...],
       policy=PriorityPolicy(
           default=["defaults", "env", "cli"],  # Default order
           overrides={
               "secrets.*": ["defaults", "etcd"],  # Secrets: skip env
               "db.*": ["defaults", "env"],  # DB: skip CLI
           },
       ),
   )

Pattern Matching
----------------

PriorityPolicy uses glob patterns for key matching:

- ``"secrets.*"`` matches ``secrets.api_key``, ``secrets.db_password``, etc.
- ``"db.*"`` matches ``db.host``, ``db.port``, etc.
- ``"*"`` matches all keys

Use Cases
---------

**Secrets Management**
   - Secrets should only come from secure sources (etcd, not env)

**Feature Flags**
   - Feature flags might have different priority rules

**Environment-Specific**
   - Different rules for different configuration namespaces

