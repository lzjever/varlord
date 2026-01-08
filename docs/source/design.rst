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
   - Focus on core functionality: configuration loading and merging
   - Avoid feature bloat that complicates the API

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

6. **Separation of Concerns**
   - Varlord focuses on configuration management, not application routing
   - CLI source handles flat arguments only (no subcommands)
   - Application layer handles command routing and subcommands
   - This keeps varlord simple and flexible

Why No Built-in Subcommand Support?
------------------------------------

Varlord intentionally does not include built-in support for command-line subcommands (e.g., ``myapp console login``).
This is a deliberate design decision based on the following principles:

**1. Single Responsibility**
   - Varlord's CLI source is designed to handle flat configuration arguments
   - Adding subcommand support would mix configuration management with application routing
   - Keeping these concerns separate makes both systems simpler and more maintainable

**2. Flexibility**
   - Different applications have different subcommand structures
   - Some use simple two-level hierarchies (``command subcommand``)
   - Others use complex nested structures (``command subcommand action``)
   - By handling subcommands at the application layer, you have full control over the structure

**3. Standard Library Integration**
   - Python's ``argparse`` module provides excellent subcommand support
   - There's no need to reinvent this functionality
   - Using standard libraries makes code more familiar and maintainable

**4. Configuration Model Independence**
   - Each subcommand may need a different configuration model
   - Application-level routing allows you to select the appropriate model for each subcommand
   - This is more flexible than trying to support multiple models in a single CLI source

**5. Keep It Simple**
   - Adding subcommand support would significantly complicate the CLI source
   - Most applications don't need subcommands
   - For those that do, the application-layer approach is straightforward and well-understood

**Recommended Approach**

For applications that need subcommands, we recommend:

1. Use ``argparse`` at the application layer to handle subcommand routing
2. Create separate configuration models for each subcommand (if needed)
3. Use varlord's ``Config`` class to load configuration for each subcommand
4. This approach is simple, flexible, and follows Python best practices

See :doc:`../user_guide/subcommands` for detailed guidance and examples.

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

