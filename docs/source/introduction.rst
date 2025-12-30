Introduction
============

What is Varlord?
----------------

Varlord is a powerful Python configuration management library designed to simplify 
configuration loading from multiple sources while maintaining flexibility and type safety.

Key Features
------------

- **Multiple Sources**: Support for defaults, CLI arguments, environment variables, 
  `.env` files, and optional etcd integration
- **Simple Priority**: Priority determined by sources order (later overrides earlier)
- **Advanced Priority**: Per-key priority rules via PriorityPolicy
- **Type Safety**: Built-in support for dataclass models with automatic type conversion
- **Dynamic Updates**: Real-time configuration updates via etcd watch (optional)
- **Logging**: Configurable logging to track configuration loading
- **Validation**: Built-in validators for configuration validation
- **Pluggable**: Clean source abstraction for easy extension

Core Concepts
-------------

Configuration Model
~~~~~~~~~~~~~~~~~~~

Varlord uses dataclass models to define your configuration structure:

.. code-block:: python

   from dataclasses import dataclass
   from varlord import Config, sources

   @dataclass(frozen=True)
   class AppConfig:
       host: str = "127.0.0.1"
       port: int = 8000
       debug: bool = False

Configuration Sources
~~~~~~~~~~~~~~~~~~~~~

Each source implements a unified interface:

- ``load() -> Mapping[str, Any]``: Load configuration snapshot
- ``watch() -> Iterator[ChangeEvent]`` (optional): Stream of changes for dynamic updates
- ``name``: Source name for debugging

Priority Ordering
~~~~~~~~~~~~~~~~~

Priority is determined by sources order: **later sources override earlier ones**.

For advanced use cases, use ``PriorityPolicy`` for per-key priority rules.

**Key Point**: Later sources in the list have higher priority and override earlier ones.

Type Conversion
~~~~~~~~~~~~~~~

Varlord automatically converts string values (from env vars, CLI, etc.) to the 
appropriate types based on your model field types.

Validation
~~~~~~~~~~

Use validators in your model's ``__post_init__`` method to validate configuration values.

