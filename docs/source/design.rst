System Design
=============

Architecture Overview
---------------------

Varlord follows a clean, pluggable architecture with clear separation of concerns:

**Component Relationships**:

- **Config**: Main entry point, manages sources and creates ConfigStore
- **Resolver**: Merges configurations from multiple sources based on priority
- **Source**: Base abstraction for all configuration sources (Defaults, Env, CLI, DotEnv, Etcd)
- **ConfigStore**: Runtime configuration management with thread-safe access and dynamic updates

**Data Flow**:

1. Config receives model and sources
2. Resolver merges configurations from sources
3. ConfigStore provides runtime access and watch support
4. Sources can optionally support watch for dynamic updates

Core Components
---------------

Config
~~~~~~

The main entry point for configuration management. It:

- Accepts a dataclass model and list of sources
- Automatically injects model to sources that need it (e.g., CLI)
- Provides ``load()`` for static configuration
- Provides ``load_store()`` for dynamic configuration with watch support

Resolver
~~~~~~~~

Handles configuration merging and priority resolution:

- Merges configurations from multiple sources
- Applies priority rules (sources order or PriorityPolicy)
- Performs deep merge for nested configurations

Source
~~~~~~

Base abstraction for all configuration sources. Each source:

- Implements ``load()`` to return configuration snapshot
- Optionally implements ``watch()`` for dynamic updates
- Has a ``name`` property for identification

PriorityPolicy
~~~~~~~~~~~~~~

Defines priority ordering with support for per-key rules:

- ``default``: Default priority order for all keys
- ``overrides``: Per-key/namespace priority rules using glob patterns

ConfigStore
~~~~~~~~~~~

Runtime configuration management:

- Thread-safe atomic snapshots
- Dynamic updates via watch mechanism
- Change subscriptions
- Automatic validation on updates

Design Principles
-----------------

1. **Simplicity First**
   - One way to do things (sources order for priority)
   - Advanced features (PriorityPolicy) only when needed

2. **Type Safety**
   - Dataclass models for structure
   - Automatic type conversion
   - Validation support

3. **Pluggable Architecture**
   - Clean Source abstraction
   - Easy to add new sources

4. **Fail-Safe**
   - Errors don't crash the system
   - Old configuration preserved on update failure

5. **Performance**
   - Lazy loading where possible
   - Efficient merging algorithms

Configuration Flow
------------------

1. **Initialization**
   - User creates ``Config`` with model and sources
   - Model is auto-injected to sources that need it
   - Resolver is created

2. **Loading**
   - Each source's ``load()`` is called
   - Configurations are merged in priority order
   - Values are converted to model field types
   - Model instance is created

3. **Dynamic Updates** (if using ConfigStore)
   - Watch threads monitor sources for changes
   - On change, configuration is reloaded
   - Validation is performed
   - Subscribers are notified

Priority Resolution
-------------------

**Default (Sources Order)**
   - Sources are processed in the order provided
   - Later sources override earlier ones
   - Simple and intuitive

**PriorityPolicy (Per-Key Rules)**
   - Each key can have different priority order
   - Useful for secrets, feature flags, etc.
   - Pattern matching for key groups

Type Conversion
---------------

Varlord automatically converts values based on model field types:

- String → int, float, bool
- Handles Optional and Union types
- JSON parsing for complex types
- Preserves original value if conversion fails

Error Handling
--------------

- **Source Loading**: Failures are logged, empty dict returned
- **Type Conversion**: Failures are logged, original value used
- **Validation**: Failures raise ValidationError
- **Dynamic Updates**: Failures preserve old configuration

Thread Safety
-------------

- ConfigStore uses RLock for thread-safe access
- Atomic configuration snapshots
- Safe concurrent access from multiple threads

