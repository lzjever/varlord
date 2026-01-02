Frequently Asked Questions
===========================

This section addresses common questions and potential points of confusion.

Why doesn't ``load_store()`` need a ``watch`` parameter?
----------------------------------------------------------

**Question**: If I set ``watch=True`` in the source (e.g., ``Etcd(watch=True)``), why doesn't ``load_store()`` also need a ``watch`` parameter?

**Answer**: ``load_store()`` automatically detects if any source supports watching and enables it automatically. You only need to enable watch in the source itself.

**Example**:

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

**Why this design?**
- Simplicity: Only one place to configure watch
- Automatic: If source supports watch, it's automatically enabled
- Less error-prone: No risk of mismatched watch settings

What happens if I call ``subscribe()`` but no sources support watch?
----------------------------------------------------------------------

**Question**: If all sources don't support watch, but I call ``load_store()`` and ``subscribe()``, what happens?

**Answer**: ``load_store()`` and ``subscribe()`` work normally, but callbacks will only be called when you manually call ``reload()`` and the configuration has changed.

**Behavior**:

1. ``load_store()`` creates successfully (``watching=False``)
2. ``subscribe()`` adds the callback successfully
3. Callbacks are called only when:
   - You manually call ``reload()`` and configuration has changed
   - Initial load does NOT trigger callbacks (it's initialization, not a change)

**Example**:

.. code-block:: python

   # No watch support
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Model auto-injected, defaults applied automatically
       ],
   )
   
   store = cfg.load_store()  # ✅ Works, but watching=False
   
   def on_change(new_config, diff):
       print("Config changed!")
   
   store.subscribe(on_change)  # ✅ Works, callback is registered
   
   # Callback will only be called on manual reload with changes
   store.reload()  # If config changed, callback is called

**For automatic updates**, you must use a source that supports watch:

.. code-block:: python

   sources.Etcd(..., watch=True)  # Must enable watch for automatic updates

How do I implement watch support in a custom source?
-----------------------------------------------------

**Question**: How do I make my custom source support watch?

**Answer**: You must override the ``supports_watch()`` method to return ``True`` when watch is enabled, and implement the ``watch()`` method.

**Required Implementation**:

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
       
       def supports_watch(self) -> bool:
           """Must override to enable watch support"""
           return self._watch
       
       def watch(self):
           """Implement watch logic"""
           if not self._watch:
               return iter([])
           # ... implement watch logic
           while True:
               yield ChangeEvent(...)

**Key Points**:
- ``supports_watch()`` must return ``True`` when watch is enabled
- ``watch()`` should return an empty iterator when watch is disabled
- ``watch()`` should yield ``ChangeEvent`` objects when watch is enabled

How does priority ordering work?
---------------------------------

**Question**: How do I control which source overrides which?

**Answer**: Priority is determined by the order of sources in the list. **Later sources override earlier ones**.

**Simple Priority (Recommended)**:

.. code-block:: python

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),  # Model auto-injected, defaults applied first (lowest priority)
           sources.CLI(),  # Model auto-injected, highest priority (last)
       ],
   )
   
   # Result: CLI overrides Env, Env overrides Model Defaults

**Advanced Priority (Per-Key Rules)**:

Use ``PriorityPolicy`` when you need different priority rules for different keys:

.. code-block:: python

   from varlord import PriorityPolicy
   
   cfg = Config(
       model=AppConfig,
       sources=[...],
       policy=PriorityPolicy(
           default=["defaults", "env", "cli"],  # Default order
           overrides={
               "secrets.*": ["defaults", "etcd"],  # Secrets: skip env and CLI
           },
       ),
   )

**Key Point**: Later sources in the list have higher priority and override earlier ones.

Why is there only one way to set priority?
-------------------------------------------

**Question**: Why can't I use a ``priority`` parameter like ``priority=["defaults", "env", "cli"]``?

**Answer**: To reduce confusion and learning cost. We provide two clear options:

1. **Reorder sources** (recommended): Simply change the order in the sources list
2. **PriorityPolicy** (advanced): Use when you need per-key priority rules

Having a separate ``priority`` parameter would be redundant with reordering sources and would add unnecessary complexity.

What's the difference between ``load()`` and ``load_store()``?
--------------------------------------------------------------

**Question**: When should I use ``load()`` vs ``load_store()``?

**Answer**:

- **``load()``**: One-time load, returns a static configuration object
  - Use when: You only need to load configuration once
  - Configuration does not change during runtime
  - Simpler, lighter weight

- **``load_store()``**: Returns a ``ConfigStore`` with dynamic update support
  - Use when: You need thread-safe access
  - You want to subscribe to configuration changes
  - You need manual reload capability
  - You want automatic updates (requires watch support)

**Example**:

.. code-block:: python

   # One-time load
   app = cfg.load()
   print(app.host)  # Static, won't update
   
   # Dynamic store
   store = cfg.load_store()
   store.subscribe(on_change)  # Subscribe to changes
   config = store.get()  # Thread-safe, can update automatically

