Validation
==========

In this tutorial, you'll learn how to validate configuration values using
Varlord's built-in validators, required field validation, and custom validation logic.

Learning Objectives
-------------------

By the end of this tutorial, you'll be able to:

- Use explicit required/optional field metadata
- Validate required fields are provided
- Use built-in validators to validate configuration values
- Create custom validation logic
- Understand when validation occurs
- Handle validation errors

Step 1: Required/Optional Fields
---------------------------------

Fields are automatically determined as required/optional:

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from typing import Optional
   from varlord import Config

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")  # Optional (has default)
       port: int = field(default=8000)  # Optional (has default)
       api_key: str = field()  # Required (no default, not Optional)
       timeout: Optional[int] = field()  # Optional (Optional type)

   # This will raise RequiredFieldError if api_key is not provided
   from varlord.model_validation import RequiredFieldError

   cfg = Config(
       model=AppConfig,
       sources=[],  # No sources provide api_key
   )

   try:
       app = cfg.load()
   except RequiredFieldError as e:
       print(f"Missing required fields: {e.missing_fields}")

**Key Points**:

- Fields **without defaults** and **not Optional[T]** are **required**
- Fields **with Optional[T]** type annotation are **optional**
- Fields **with defaults** (or ``default_factory``) are **optional**
- Required fields must be provided by at least one source
- Empty strings and empty collections are considered valid (presence is checked, not emptiness)

Step 2: Basic Value Validation
-------------------------------

Let's add validation to ensure configuration values are correct:

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config
   from varlord.validators import validate_port, validate_not_empty

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)

       def __post_init__(self):
           validate_not_empty(self.host)
           validate_port(self.port)

   cfg = Config(
       model=AppConfig,
       sources=[],
   )

   app = cfg.load()
   print(f"Configuration valid: {app.host}:{app.port}")

**Expected Output**:

.. code-block:: text

   Configuration valid: 0.0.0.0:8000

**Key Points**:

- Validation happens in ``__post_init__``
- Validation occurs **after all sources are merged**
- If validation fails, ``cfg.load()`` raises ``ValidationError``

Step 3: Validation with Multiple Sources
------------------------------------------

Validation uses the **final merged values**, not just defaults:

.. code-block:: python
   :linenos:

   import os
   from dataclasses import dataclass, field
   from varlord import Config, sources
   from varlord.validators import validate_port, ValidationError

   @dataclass(frozen=True)
   class AppConfig:
       port: int = field(default=8000)  # Valid default

       def __post_init__(self):
           validate_port(self.port)

   # Set invalid port in environment
   os.environ["PORT"] = "70000"  # Invalid (too large)

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),
       ],
   )

   try:
       app = cfg.load()
   except ValidationError as e:
       print(f"Validation failed: {e.message}")
       print(f"  Key: {e.key}")
       print(f"  Value: {e.value}")

**Expected Output**:

.. code-block:: text

   Validation failed: must be <= 65535
     Key: value
     Value: 70000

**Important**: Even though the default value (8000) is valid, validation fails
because the final merged value (70000 from env) is invalid.

Step 4: Using Multiple Validators
-----------------------------------

You can use multiple validators for a single field:

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config, sources
   from varlord.validators import (
       validate_email,
       validate_url,
       validate_length,
       validate_not_empty,
   )

   @dataclass(frozen=True)
   class AppConfig:
       admin_email: str = field(default="admin@example.com")
       api_url: str = field(default="https://api.example.com")
       api_key: str = field(default="")

       def __post_init__(self):
           validate_email(self.admin_email)
           validate_url(self.api_url)
           validate_not_empty(self.api_key)  # This will fail with empty default!
           validate_length(self.api_key, min_length=32, max_length=64)

   cfg = Config(
       model=AppConfig,
       sources=[],
   )

   try:
       app = cfg.load()
   except ValidationError as e:
       print(f"Validation failed: {e.message}")

**Expected Output**:

.. code-block:: text

   Validation failed: must not be empty

**Solution**: Provide a valid default or ensure another source provides the value:

.. code-block:: python
   :linenos:

   import os

   # Provide valid api_key from environment
   os.environ["API_KEY"] = "a" * 32  # 32 characters

   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),
       ],
   )

   app = cfg.load()
   print(f"API Key length: {len(app.api_key)}")  # 32

**Expected Output**:

.. code-block:: text

   API Key length: 32

Step 5: Validating Nested Configuration
----------------------------------------

Each nested dataclass can have its own validation:

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config
   from varlord.validators import validate_port, validate_not_empty

   @dataclass(frozen=True)
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)

       def __post_init__(self):
           validate_not_empty(self.host)
           validate_port(self.port)

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)
       db: DBConfig = field(default_factory=lambda: DBConfig())

       def __post_init__(self):
           validate_port(self.port)
           # DBConfig's __post_init__ is automatically called
           # No need to manually validate self.db

   cfg = Config(
       model=AppConfig,
       sources=[],
   )

   app = cfg.load()
   print(f"App port: {app.port}")
   print(f"DB port: {app.db.port}")

**Expected Output**:

.. code-block:: text

   App port: 8000
   DB port: 5432

**Key Points**:

- Nested objects are validated automatically when created
- Parent's ``__post_init__`` is called after nested objects are validated
- You can add cross-field validation in the parent's ``__post_init__``

Step 6: Cross-Field Validation
-------------------------------

You can validate relationships between fields:

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config
   from varlord.validators import validate_port, ValidationError

   @dataclass(frozen=True)
   class AppConfig:
       app_port: int = field(default=8000)
       db_port: int = field(default=8000)  # Same as app_port - will conflict!

       def __post_init__(self):
           validate_port(self.app_port)
           validate_port(self.db_port)

           # Cross-field validation
           if self.app_port == self.db_port:
               raise ValidationError(
                   "app_port",
                   self.app_port,
                   f"App port conflicts with DB port {self.db_port}"
               )

   # This will fail - ports conflict
   cfg = Config(
       model=AppConfig,
       sources=[],
   )

   try:
       app = cfg.load()
   except ValidationError as e:
       print(f"Validation failed: {e.message}")

**Expected Output**:

.. code-block:: text

   Validation failed: App port conflicts with DB port 8000

Step 7: Custom Validators
--------------------------

You can create custom validation functions:

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config
   from varlord.validators import ValidationError

   def validate_api_key_format(value: str) -> None:
       """Custom validator for API key format."""
       if not value.startswith("sk-"):
           raise ValidationError(
               "api_key",
               value,
               "API key must start with 'sk-'"
           )
       if len(value) < 32:
           raise ValidationError(
               "api_key",
               value,
               "API key must be at least 32 characters"
           )

   @dataclass(frozen=True)
   class AppConfig:
       api_key: str = field(default="")

       def __post_init__(self):
           validate_api_key_format(self.api_key)

   # This will fail with empty default
   cfg = Config(
       model=AppConfig,
       sources=[],
   )

   try:
       app = cfg.load()
   except ValidationError as e:
       print(f"Validation failed: {e.message}")

**Expected Output**:

.. code-block:: text

   Validation failed: API key must start with 'sk-'

Step 8: Complete Example
------------------------

Here's a complete example with comprehensive validation:

.. code-block:: python
   :name: validation_complete
   :linenos:

   import os
   from dataclasses import dataclass, field
   from varlord import Config, sources
   from varlord.validators import (
       validate_port,
       validate_email,
       validate_url,
       validate_length,
       validate_not_empty,
       ValidationError,
   )

   @dataclass(frozen=True)
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)

       def __post_init__(self):
           validate_not_empty(self.host)
           validate_port(self.port)

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)
       admin_email: str = field(default="admin@example.com")
       api_url: str = field(default="https://api.example.com")
       api_key: str = field(default="")
       db: DBConfig = field(default_factory=lambda: DBConfig())

       def __post_init__(self):
           validate_not_empty(self.host)
           validate_port(self.port)
           validate_email(self.admin_email)
           validate_url(self.api_url)
           validate_length(self.api_key, min_length=32, max_length=64)

           # Cross-field validation
           if self.port == self.db.port:
               raise ValidationError(
                   "port",
                   self.port,
                   f"App port conflicts with DB port {self.db.port}"
               )

   def main():
       # Provide required values from environment
       os.environ["API_KEY"] = "a" * 32

       cfg = Config(
           model=AppConfig,
           sources=[
               sources.Env(),
           ],
       )

       try:
           app = cfg.load()
           print("Configuration validated successfully:")
           print(f"  App: {app.host}:{app.port}")
           print(f"  Admin: {app.admin_email}")
           print(f"  API: {app.api_url}")
           print(f"  API Key: {'*' * len(app.api_key)}")
           print(f"  DB: {app.db.host}:{app.db.port}")
       except ValidationError as e:
           print(f"Validation failed: {e.message}")
           print(f"  Key: {e.key}")
           print(f"  Value: {e.value}")

   if __name__ == "__main__":
       main()

**Expected Output**:

.. code-block:: text

   Configuration validated successfully:
     App: 0.0.0.0:8000
     Admin: admin@example.com
     API: https://api.example.com
     API Key: ********************************
     DB: localhost:5432

Common Pitfalls
---------------

**Pitfall 1: Validating before sources are merged**

.. code-block:: python
   :emphasize-lines: 6-7

   @dataclass(frozen=True)
   class AppConfig:
       api_key: str = ""

       def __post_init__(self):
           # This validates the FINAL merged value, not just the default
           validate_length(self.api_key, min_length=32)
           # If no source provides api_key, this will fail even if
           # you intended to provide it via environment

**Solution**: Remember that validation happens after all sources are merged.
Ensure at least one source provides valid values, or use ``Optional`` for
fields that may not always be set.

**Pitfall 3: Not handling RequiredFieldError**

.. code-block:: python
   :emphasize-lines: 1

   @dataclass(frozen=True)
   class AppConfig:
       api_key: str = field()

   app = cfg.load()  # May raise RequiredFieldError if api_key not provided
   print(app.api_key)  # This line won't execute if validation fails

**Solution**: Either provide the required field via a source, or use ``cfg.load(validate=False)`` to skip validation, or wrap in try-except to handle ``RequiredFieldError``.

**Pitfall 4: Not handling ValidationError**

.. code-block:: python
   :emphasize-lines: 1

   app = cfg.load()  # May raise ValidationError
   print(app.port)  # This line won't execute if validation fails

**Solution**: Always wrap ``cfg.load()`` in try-except to handle validation
errors gracefully.

**Pitfall 5: Validating nested objects manually**

.. code-block:: python
   :emphasize-lines: 7-8

   @dataclass(frozen=True)
   class AppConfig:
       db: DBConfig = field(default_factory=lambda: DBConfig())

       def __post_init__(self):
           # Unnecessary - DBConfig.__post_init__ is already called
           if self.db:
               validate_port(self.db.port)  # Redundant!

**Solution**: Nested objects are automatically validated. Only add validation
in the parent if you need cross-field validation.

Best Practices
--------------

1. **Fields are automatically determined**: Use ``Optional[T]`` type annotation or default values for optional fields
2. **Validate required fields**: Use ``Config.validate()`` or ``cfg.load(validate=True)`` to ensure required fields are provided
3. **Validate field values**: Use validators in ``__post_init__`` to ensure data integrity
4. **Provide helpful error messages**: Custom validators should explain what's wrong
5. **Validate after merge**: Remember validation uses final merged values
6. **Use built-in validators when possible**: They're tested and well-documented
7. **Add field descriptions**: Use ``metadata={"description": "..."}`` for better documentation

Next Steps
----------

Now that you understand validation, let's learn about :doc:`dynamic_updates` to
handle configuration changes at runtime.

