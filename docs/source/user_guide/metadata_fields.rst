Metadata Fields
===============

Varlord supports several metadata fields in dataclass field definitions to provide
additional information about configuration fields.

Field Required/Optional Status
------------------------------

Fields are automatically determined by their default values:

- **Fields without defaults** → **Required**
- **Fields with defaults** (or ``default_factory``) → **Optional**

No ``metadata={"optional": True}`` needed - defaults determine optional status.

**Example**:

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass
   class AppConfig:
       api_key: str = field()  # Required (no default)
       host: str = field(default="localhost")  # Optional (has default)

Optional Metadata Fields
------------------------

These fields are optional but recommended for better user experience:

- ``description: str`` - General field description used for documentation and CLI help
- ``help: str`` - CLI-specific help text (overrides description for CLI help if provided)

**Example**:

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass
   class AppConfig:
       api_key: str = field(
           metadata={
               "description": "API key for authentication",
               "help": "Required API key for accessing the service"
           }
       )  # Required by default
       host: str = field(
           default="127.0.0.1",
           metadata={
               
               "description": "Server host address",
               "help": "Server host (default: 127.0.0.1)"
           }
       )

Metadata Field Priority
------------------------

When both ``description`` and ``help`` are provided:
- ``help`` takes precedence for CLI help text
- ``description`` is used for general documentation and error messages

If only ``description`` is provided, it will be used for both CLI help and documentation.

Complete Example
----------------

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class AppConfig:
       # Required field with description (no default)
       api_key: str = field(
           metadata={
               "description": "API key for authentication",
               "help": "Required API key"
           }
       )
       
       # Optional field with description and help (has default)
       host: str = field(
           default="127.0.0.1",
           metadata={
               "description": "Server host address",
               "help": "Server host (default: 127.0.0.1)"
           }
       )
       
       # Optional field with only description (has default)
       port: int = field(
           default=8000,
           metadata={
               "description": "Server port number"
           }
       )

