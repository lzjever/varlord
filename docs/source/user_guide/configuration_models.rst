Configuration Models
====================

Varlord uses Python dataclasses to define configuration structure. This provides 
type safety, default values, and validation support.

Basic Model
-----------

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="127.0.0.1", metadata={"optional": True})
       port: int = field(default=8000, metadata={"optional": True})
       debug: bool = field(default=False, metadata={"optional": True})

**Important**: All fields must explicitly specify ``metadata={"required": True}`` or ``metadata={"optional": True}``.

Required Fields
---------------

Mark fields as required when they must be provided by a source:

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class AppConfig:
       api_key: str = field(metadata={"required": True})  # No default - must be provided
       host: str = field(default="127.0.0.1", metadata={"optional": True})

   # This will raise RequiredFieldError if api_key is not provided
   cfg = Config(model=AppConfig, sources=[])

Optional Fields
---------------

Mark fields as optional when they have defaults or may not be set:

.. code-block:: python

   from dataclasses import dataclass, field
   from typing import Optional

   @dataclass(frozen=True)
   class AppConfig:
       api_key: Optional[str] = field(default=None, metadata={"optional": True})
       timeout: Optional[float] = field(default=None, metadata={"optional": True})

Field Descriptions
------------------

Add descriptions and help text via metadata:

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(
           default="127.0.0.1",
           metadata={
               "optional": True,
               "description": "Server host address",
               "help": "Server host (default: 127.0.0.1)"
           }
       )
       api_key: str = field(
           metadata={
               "required": True,
               "description": "API key for authentication",
               "help": "Required API key"
           }
       )

Default Factories
-----------------

Use ``field(default_factory=...)`` for mutable defaults:

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class AppConfig:
       allowed_hosts: list = field(
           default_factory=list,
           metadata={"optional": True}
       )
       settings: dict = field(
           default_factory=dict,
           metadata={"optional": True}
       )

Best Practices
--------------

1. **Use frozen dataclasses** to prevent accidental modification
2. **Explicitly mark all fields** as required or optional
3. **Provide default values** for optional fields
4. **Use appropriate types** (int, float, bool, str, Optional, etc.)
5. **Add field descriptions** for better documentation
6. **Add validation** in ``__post_init__`` if needed

