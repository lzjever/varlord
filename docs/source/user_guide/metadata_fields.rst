Metadata Fields
===============

Varlord supports several metadata fields in dataclass field definitions to provide
additional information about configuration fields.

Required Metadata Fields
------------------------

These fields **must** be specified (exactly one):

- ``required: bool`` - Set to ``True`` if the field is required and must be provided
- ``optional: bool`` - Set to ``True`` if the field is optional and may have a default

**Example**:

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass
   class AppConfig:
       api_key: str = field(metadata={"required": True})
       host: str = field(default="localhost", metadata={"optional": True})

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
               "required": True,
               "description": "API key for authentication",
               "help": "Required API key for accessing the service"
           }
       )
       host: str = field(
           default="127.0.0.1",
           metadata={
               "optional": True,
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
       # Required field with description
       api_key: str = field(
           metadata={
               "required": True,
               "description": "API key for authentication",
               "help": "Required API key"
           }
       )
       
       # Optional field with description and help
       host: str = field(
           default="127.0.0.1",
           metadata={
               "optional": True,
               "description": "Server host address",
               "help": "Server host (default: 127.0.0.1)"
           }
       )
       
       # Optional field with only description
       port: int = field(
           default=8000,
           metadata={
               "optional": True,
               "description": "Server port number"
           }
       )

