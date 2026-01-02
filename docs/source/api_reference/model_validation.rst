Model Validation
================

This module provides validation functions for model definitions and configuration structure.

.. automodule:: varlord.model_validation
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

**validate_model_definition**
   Validates model definition (currently no validation errors - Optional[T] types are supported).

   Fields are automatically determined as required/optional:
   - Fields **without defaults** and **not Optional[T]** are **required**
   - Fields **with Optional[T]** type annotation are **optional**
   - Fields **with defaults** (or ``default_factory``) are **optional**

   Example:

   .. code-block:: python

      from varlord.model_validation import validate_model_definition
      from dataclasses import dataclass, field
      from typing import Optional

      @dataclass
      class Config:
          api_key: str = field()  # Required (no default, not Optional)
          timeout: Optional[int] = field()  # Optional (Optional type)
          host: str = field(default="localhost")  # Optional (has default)

      validate_model_definition(Config)  # OK

**validate_config**
   Validates that all required fields exist in a configuration dictionary.

   Example:

   .. code-block:: python

      from varlord.model_validation import validate_config, RequiredFieldError
      from dataclasses import dataclass, field

      @dataclass
      class Config:
          api_key: str = field()

      config_dict = {}  # Missing api_key
      try:
          validate_config(Config, config_dict, [])
      except RequiredFieldError as e:
          print(e)  # Shows missing fields and source help

Exceptions
----------

**VarlordError**
   Base exception for all varlord errors.

**ModelDefinitionError**
   Raised when model definition is invalid (currently not used - Optional[T] types are supported).

**RequiredFieldError**
   Raised when required fields are missing from the configuration dictionary.
   Includes comprehensive error messages with source mapping help.

