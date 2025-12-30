Configuration Models
====================

Varlord uses Python dataclasses to define configuration structure. This provides 
type safety, default values, and validation support.

Basic Model
-----------

.. code-block:: python

   from dataclasses import dataclass

   @dataclass(frozen=True)
   class AppConfig:
       host: str = "127.0.0.1"
       port: int = 8000
       debug: bool = False

Best Practices
--------------

1. **Use frozen dataclasses** to prevent accidental modification
2. **Provide default values** for all fields
3. **Use appropriate types** (int, float, bool, str, Optional, etc.)
4. **Add validation** in ``__post_init__`` if needed

Optional Fields
---------------

Use ``Optional`` for fields that may not be set:

.. code-block:: python

   from typing import Optional

   @dataclass(frozen=True)
   class AppConfig:
       api_key: Optional[str] = None
       timeout: Optional[float] = None

Default Factories
-----------------

Use ``field(default_factory=...)`` for mutable defaults:

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class AppConfig:
       allowed_hosts: list = field(default_factory=list)
       settings: dict = field(default_factory=dict)

