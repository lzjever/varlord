Validation
==========

Varlord provides comprehensive built-in validators and supports custom validation.
Validation is performed in the dataclass ``__post_init__`` method, which is
automatically called when the configuration is instantiated.

**Important**: Validation happens **after all sources are merged**. This means:

1. Model defaults are automatically applied first
2. All configuration sources are loaded and merged
3. The merged configuration is converted to a model instance
4. Required field validation is performed (if enabled)
5. ``__post_init__`` is called, which performs value validation
6. If validation fails, the entire configuration load fails

This ensures that validation works on the **final merged values**, not just defaults.

**Required Field Validation**:

Fields are automatically determined as required/optional:
- Fields **without defaults** and **not Optional[T]** are **required**
- Fields **with Optional[T]** type annotation are **optional**
- Fields **with defaults** (or ``default_factory``) are **optional**

Required fields are validated before ``__post_init__`` is called.

Example:

.. code-block:: python

   from dataclasses import dataclass, field
   from varlord import Config, sources
   from varlord.validators import validate_length
   from varlord.model_validation import RequiredFieldError

   @dataclass(frozen=True)
   class AppConfig:
       api_key: str = field()  # Required - no default

   # This will FAIL - api_key not provided
   cfg = Config(model=AppConfig, sources=[])
   try:
       app = cfg.load()  # Raises RequiredFieldError
   except RequiredFieldError as e:
       print(f"Missing required fields: {e.missing_fields}")

   # This will SUCCEED (env provides api_key)
   # Set: export API_KEY="a" * 32
   cfg = Config(
       model=AppConfig,
       sources=[
           sources.Env(),
       ],
   )
   app = cfg.load()  # OK - required field provided

Built-in Validators
-------------------

Varlord provides a comprehensive set of validators organized by category:

Basic Validators
~~~~~~~~~~~~~~~~

**validate_range**: Validate that a value is within a range.

.. code-block:: python

   from varlord.validators import validate_range

   validate_range(50, min=0, max=100)  # OK
   validate_range(150, min=0, max=100)  # Raises ValidationError

**validate_regex**: Validate that a string matches a regex pattern.

.. code-block:: python

   from varlord.validators import validate_regex

   validate_regex("abc123", r'^[a-z]+\d+$')  # OK
   validate_regex("ABC123", r'^[a-z]+\d+$')  # Raises ValidationError

**validate_choice**: Validate that a value is in a list of choices.

.. code-block:: python

   from varlord.validators import validate_choice

   validate_choice("red", ["red", "green", "blue"])  # OK
   validate_choice("yellow", ["red", "green", "blue"])  # Raises ValidationError

**validate_not_empty**: Validate that a value is not empty.

.. code-block:: python

   from varlord.validators import validate_not_empty

   validate_not_empty("hello")  # OK
   validate_not_empty(0)  # OK (0 is not considered empty)
   validate_not_empty(False)  # OK (False is not considered empty)
   validate_not_empty("")  # Raises ValidationError
   validate_not_empty([])  # Raises ValidationError

Numeric Validators
~~~~~~~~~~~~~~~~~~

**validate_positive**: Validate that a number is positive (> 0).

.. code-block:: python

   from varlord.validators import validate_positive

   validate_positive(10)  # OK
   validate_positive(-5)  # Raises ValidationError

**validate_non_negative**: Validate that a number is non-negative (>= 0).

.. code-block:: python

   from varlord.validators import validate_non_negative

   validate_non_negative(0)  # OK
   validate_non_negative(10)  # OK
   validate_non_negative(-5)  # Raises ValidationError

**validate_integer**: Validate that a value is an integer.

.. code-block:: python

   from varlord.validators import validate_integer

   validate_integer(42)  # OK
   validate_integer(42.5)  # Raises ValidationError

**validate_float**: Validate that a value is a float or can be converted to float.

.. code-block:: python

   from varlord.validators import validate_float

   validate_float(3.14)  # OK
   validate_float(42)  # OK (int can be float)

**validate_percentage**: Validate that a number is a valid percentage (0-100).

.. code-block:: python

   from varlord.validators import validate_percentage

   validate_percentage(50)  # OK
   validate_percentage(150)  # Raises ValidationError

**validate_port**: Validate that a number is a valid port number (1-65535).

.. code-block:: python

   from varlord.validators import validate_port

   validate_port(8080)  # OK
   validate_port(70000)  # Raises ValidationError

**validate_greater_than**: Validate that a number is greater than a threshold.

.. code-block:: python

   from varlord.validators import validate_greater_than

   validate_greater_than(10, 5)  # OK
   validate_greater_than(3, 5)  # Raises ValidationError

**validate_less_than**: Validate that a number is less than a threshold.

.. code-block:: python

   from varlord.validators import validate_less_than

   validate_less_than(3, 5)  # OK
   validate_less_than(10, 5)  # Raises ValidationError

String Validators
~~~~~~~~~~~~~~~~~

**validate_length**: Validate that a string has a length within a range.

.. code-block:: python

   from varlord.validators import validate_length

   validate_length("hello", min_length=3, max_length=10)  # OK
   validate_length("hi", min_length=3)  # Raises ValidationError

**validate_email**: Validate that a string is a valid email address.

.. code-block:: python

   from varlord.validators import validate_email

   validate_email("user@example.com")  # OK
   validate_email("invalid-email")  # Raises ValidationError

**validate_url**: Validate that a string is a valid URL.

.. code-block:: python

   from varlord.validators import validate_url

   validate_url("https://example.com")  # OK
   validate_url("example.com", require_scheme=False)  # OK
   validate_url("not-a-url")  # Raises ValidationError

**validate_ipv4**: Validate that a string is a valid IPv4 address.

.. code-block:: python

   from varlord.validators import validate_ipv4

   validate_ipv4("192.168.1.1")  # OK
   validate_ipv4("256.1.1.1")  # Raises ValidationError

**validate_ipv6**: Validate that a string is a valid IPv6 address.

.. code-block:: python

   from varlord.validators import validate_ipv6

   validate_ipv6("2001:0db8::1")  # OK
   validate_ipv6("192.168.1.1")  # Raises ValidationError

**validate_ip**: Validate that a string is a valid IPv4 or IPv6 address.

.. code-block:: python

   from varlord.validators import validate_ip

   validate_ip("192.168.1.1")  # OK (IPv4)
   validate_ip("2001:db8::1")  # OK (IPv6)

**validate_domain**: Validate that a string is a valid domain name.

.. code-block:: python

   from varlord.validators import validate_domain

   validate_domain("example.com")  # OK
   validate_domain("sub.example.com")  # OK
   validate_domain("invalid..domain")  # Raises ValidationError

**validate_phone**: Validate that a string is a valid phone number.

.. code-block:: python

   from varlord.validators import validate_phone

   validate_phone("+1234567890")  # OK (generic)
   validate_phone("13800138000", country="CN")  # OK (Chinese mobile)
   validate_phone("5552345678", country="US")  # OK (US phone)

**validate_uuid**: Validate that a string is a valid UUID.

.. code-block:: python

   from varlord.validators import validate_uuid

   validate_uuid("550e8400-e29b-41d4-a716-446655440000")  # OK
   validate_uuid("invalid-uuid")  # Raises ValidationError

**validate_base64**: Validate that a string is valid Base64 encoded data.

.. code-block:: python

   from varlord.validators import validate_base64

   validate_base64("SGVsbG8gV29ybGQ=")  # OK
   validate_base64("invalid!")  # Raises ValidationError

**validate_json_string**: Validate that a string is valid JSON.

.. code-block:: python

   from varlord.validators import validate_json_string

   validate_json_string('{"key": "value"}')  # OK
   validate_json_string("invalid json")  # Raises ValidationError

**validate_date_format**: Validate that a string matches a date format.

.. code-block:: python

   from varlord.validators import validate_date_format

   validate_date_format("2024-01-15", "%Y-%m-%d")  # OK
   validate_date_format("01/15/2024", "%m/%d/%Y")  # OK

**validate_time_format**: Validate that a string matches a time format.

.. code-block:: python

   from varlord.validators import validate_time_format

   validate_time_format("14:30:00", "%H:%M:%S")  # OK
   validate_time_format("2:30 PM", "%I:%M %p")  # OK

**validate_datetime_format**: Validate that a string matches a datetime format.

.. code-block:: python

   from varlord.validators import validate_datetime_format

   validate_datetime_format("2024-01-15 14:30:00")  # OK (default format)
   validate_datetime_format("2024-01-15 14:30:00", "%Y-%m-%d %H:%M:%S")  # OK

Collection Validators
~~~~~~~~~~~~~~~~~~~~~

**validate_list_length**: Validate that a list has a length within a range.

.. code-block:: python

   from varlord.validators import validate_list_length

   validate_list_length([1, 2, 3], min_length=2, max_length=5)  # OK
   validate_list_length([1], min_length=2)  # Raises ValidationError

**validate_dict_keys**: Validate that a dictionary has required keys and/or only allowed keys.

.. code-block:: python

   from varlord.validators import validate_dict_keys

   validate_dict_keys({"a": 1, "b": 2}, required_keys=["a"])  # OK
   validate_dict_keys({"a": 1}, required_keys=["a", "b"])  # Raises ValidationError
   validate_dict_keys({"a": 1, "c": 3}, allowed_keys=["a", "b"])  # Raises ValidationError

File/Path Validators
~~~~~~~~~~~~~~~~~~~~

**validate_file_path**: Validate that a string is a valid file path.

.. code-block:: python

   from varlord.validators import validate_file_path

   validate_file_path("/path/to/file.txt")  # OK
   validate_file_path("/nonexistent.txt", must_exist=True)  # Raises ValidationError if file doesn't exist

**validate_directory_path**: Validate that a string is a valid directory path.

.. code-block:: python

   from varlord.validators import validate_directory_path

   validate_directory_path("/path/to/dir")  # OK
   validate_directory_path("/nonexistent", must_exist=True)  # Raises ValidationError if directory doesn't exist

Complete Example
~~~~~~~~~~~~~~~~

Here's a complete example using multiple validators:

.. code-block:: python

   from dataclasses import dataclass
   from varlord.validators import (
       validate_range,
       validate_email,
       validate_url,
       validate_port,
       validate_length,
       validate_not_empty,
   )

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)
       admin_email: str = field(default="admin@example.com")
       api_url: str = field(default="https://api.example.com")
       api_key: str = field(default="")

       def __post_init__(self):
           validate_not_empty(self.host)
           validate_port(self.port)
           validate_email(self.admin_email)
           validate_url(self.api_url)
           validate_length(self.api_key, min_length=32, max_length=64)

Custom Validators
-----------------

Create custom validators:

.. code-block:: python

   from varlord.validators import validate_custom, ValidationError

   def validate_port(value):
       if not (1024 <= value <= 65535):
           raise ValidationError("port", value, "must be between 1024 and 65535")

   @dataclass(frozen=True)
   class AppConfig:
       port: int = 8000

       def __post_init__(self):
           validate_custom(self.port, validate_port)

**Or raise ValidationError directly**:

.. code-block:: python

   from varlord.validators import ValidationError

   @dataclass(frozen=True)
   class AppConfig:
       port: int = 8000

       def __post_init__(self):
           if not (1024 <= self.port <= 65535):
               raise ValidationError(
                   "port",
                   self.port,
                   "must be between 1024 and 65535"
               )

Nested Configuration Validation
--------------------------------

For nested configurations, each nested dataclass should have its own ``__post_init__``
method. Validation is performed automatically when nested objects are created.

.. code-block:: python

   from dataclasses import dataclass
   from varlord.validators import validate_range, validate_not_empty, validate_email, ValidationError

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class DBConfig:
       host: str = field(default="localhost")
       port: int = field(default=5432)
       max_connections: int = field(default=10)

       def __post_init__(self):
           """Validate database configuration."""
           validate_not_empty(self.host)
           validate_port(self.port)
           validate_range(self.max_connections, min=1, max=100)

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="0.0.0.0")
       port: int = field(default=8000)
       db: DBConfig = field(default_factory=lambda: DBConfig())

       def __post_init__(self):
           """Validate application configuration."""
           # Validate flat fields
           validate_range(self.port, min=1, max=65535)
           
           # Nested dataclasses are automatically validated
           # DBConfig's __post_init__ is called when DBConfig is instantiated
           # No need to manually validate self.db here - it's already validated!
           
           # Optional: Cross-field validation
           if self.db is not None:
               # Example: Validate that port doesn't conflict with DB port
               if self.port == self.db.port:
                   raise ValidationError(
                       "port",
                       self.port,
                       f"App port conflicts with DB port {self.db.port}"
                   )

**Key Points**:

1. **Automatic nested validation**: When a nested dataclass is created, its
   ``__post_init__`` is automatically called. You don't need to manually validate
   nested objects in the parent's ``__post_init__``.

2. **Cross-field validation**: You can validate relationships between fields
   (including nested fields) in the parent's ``__post_init__``.

3. **Validation order**: Nested objects are validated first (when created), then
   the parent object is validated.

Validation Errors
-----------------

Varlord provides several exception types for different validation scenarios:

**Value Validation Errors** (from ``varlord.validators``):

Value validation errors raise ``ValidationError`` with detailed information:

.. code-block:: python

   from varlord.validators import ValidationError

   try:
       app = cfg.load()
   except ValidationError as e:
       print(f"Key: {e.key}")
       print(f"Value: {e.value}")
       print(f"Error: {e.message}")

**Error Information**:

- ``e.key``: The configuration key that failed validation (e.g., ``"port"``, ``"db.host"``)
- ``e.value``: The invalid value
- ``e.message``: Human-readable error message

**Model and Structure Validation Errors** (from ``varlord.model_validation``):

- ``ModelDefinitionError``: Raised when a field is missing required/optional metadata
- ``RequiredFieldError``: Raised when required fields are missing from configuration
  - ``e.missing_fields``: List of missing field keys
  - ``e.model_name``: Name of the model class
  - Includes comprehensive source mapping help in error message

For more details, see :doc:`API Reference <../api_reference/model_validation>`.

Validator Reference
-------------------

For a complete list of all available validators, see the :doc:`API Reference <../api_reference/validators>`.
