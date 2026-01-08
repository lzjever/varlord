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
           sources.Env(),  # Model auto-injected, defaults applied first (lowest priority)
           sources.CLI(),  # Model auto-injected, highest priority (last)
       ],
   )
   
   # Result: CLI overrides Env, Env overrides Model Defaults

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
           default=["defaults", "env", "cli"],  # Default order (can use source names or IDs)
           overrides={
               "secrets.*": ["defaults", "etcd"],  # Secrets: skip env
               "db.*": ["defaults", "env"],  # DB: skip CLI
           },
       ),
   )

**Source Names vs Source IDs**:

PriorityPolicy supports both source names and source IDs:

- **Source names** (e.g., ``"yaml"``, ``"env"``): Match all sources of that type
- **Source IDs** (e.g., ``"yaml:/etc/app/config.yaml"``, ``"system-config"``): Match specific source instances

.. code-block:: python

   # Multiple YAML sources with different priorities
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.YAML("/etc/app/config.yaml", source_id="system-config"),
           sources.YAML("~/.config/app.yaml", source_id="user-config"),
           sources.Env(),
       ],
       policy=PriorityPolicy(
           default=["defaults", "system-config", "user-config", "env"],
           # system-config has lower priority than user-config
       ),
   )

**Note**: When using source names in PriorityPolicy, all sources of that type are matched in their original order. When using source IDs, only the specific source instance is matched.

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

