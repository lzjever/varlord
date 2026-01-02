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
       host: str = field(default="127.0.0.1")
       port: int = field(default=8000)
       debug: bool = field(default=False)

**Important**: 
- Fields **without defaults** and **not Optional[T]** are **required by default**
- Fields **with defaults** (or ``default_factory``) are **automatically optional**
- Fields with **Optional[T]** type annotation are **automatically optional**
- No ``metadata={"optional": True}`` needed - type annotation and defaults determine optional status

Required Fields
---------------

Fields are required by default (no metadata needed):

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class AppConfig:
       api_key: str = field()  # Required by default - no metadata needed
       host: str = field(default="127.0.0.1")

   # This will raise RequiredFieldError if api_key is not provided
   cfg = Config(model=AppConfig, sources=[])

Optional Fields
---------------

Mark fields as optional when they have defaults or may not be set:

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class AppConfig:
       # Use explicit type with default
       api_key: str = field(default="")
       timeout: float = field(default=30.0)

**Important**: Use ``Optional[T]`` type annotation or default values to mark fields as optional.
Fields with ``Optional[T]`` or defaults are automatically optional.

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
               
               "description": "Server host address",
               "help": "Server host (default: 127.0.0.1)"
           }
       )
       api_key: str = field(
           metadata={
               "description": "API key for authentication",
               "help": "Required API key"
           }
       )  # Required by default

**Supported Metadata Keys**:

- ``description: str`` - **Optional**: General field description (used for documentation and CLI help)
- ``help: str`` - **Optional**: CLI-specific help text (overrides description for CLI help if provided)

**Note**: Fields with defaults are automatically optional. No ``metadata={"optional": True}`` needed. 
The ``description`` and ``help`` fields are optional but recommended for better user experience.

Default Factories
-----------------

Use ``field(default_factory=...)`` for mutable defaults:

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class AppConfig:
       allowed_hosts: list = field(
           default_factory=list
       )  # Optional (has default_factory)
       settings: dict = field(
           default_factory=dict
       )  # Optional (has default_factory)

Best Practices
--------------

1. **Use frozen dataclasses** to prevent accidental modification
2. **Fields without defaults and not Optional[T] are required** - fields with Optional[T] or defaults are automatically optional
3. **Use Optional[T] type annotation or default values** for optional fields (no ``metadata={"optional": True}`` needed)
4. **Use appropriate types** (int, float, bool, str, Optional[T], etc.)
5. **Add field descriptions** for better documentation
6. **Add validation** in ``__post_init__`` if needed

