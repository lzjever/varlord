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
   Validates that all fields in a dataclass model have explicit required/optional metadata.

   Example:

   .. code-block:: python

      from varlord.model_validation import validate_model_definition
      from dataclasses import dataclass, field

      @dataclass
      class Config:
          api_key: str = field(metadata={"required": True})  # OK
          host: str = field()  # Missing metadata - will raise ModelDefinitionError

      validate_model_definition(Config)  # Raises ModelDefinitionError

**validate_config**
   Validates that all required fields exist in a configuration dictionary.

   Example:

   .. code-block:: python

      from varlord.model_validation import validate_config, RequiredFieldError
      from dataclasses import dataclass, field

      @dataclass
      class Config:
          api_key: str = field(metadata={"required": True})

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
   Raised when a field is missing required/optional metadata in the model definition.

**RequiredFieldError**
   Raised when required fields are missing from the configuration dictionary.
   Includes comprehensive error messages with source mapping help.

