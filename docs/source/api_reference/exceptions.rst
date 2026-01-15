Exceptions
==========

.. module:: varlord.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

Exception Hierarchy
--------------------

Varlord provides a unified exception hierarchy for error handling. All custom exceptions inherit from :class:`VarlordError`.

Base Exception
~~~~~~~~~~~~~~

.. autoclass:: varlord.exceptions.VarlordError
   :members:
   :undoc-members:

Configuration Exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: varlord.exceptions.ConfigError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: varlord.exceptions.ConfigLoadError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: varlord.exceptions.SourceLoadError
   :members:
   :undoc-members:
   :show-inheritance:

Validation Exceptions
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: varlord.exceptions.ValidationError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: varlord.exceptions.RequiredFieldError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: varlord.exceptions.ModelDefinitionError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: varlord.exceptions.ConversionError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: varlord.exceptions.ResolverError
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
~~~~~~~~~~~~~~

Catching All Varlord Exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from varlord import Config, VarlordError

   cfg = Config(model=MyConfig, sources=[...])
   try:
       config = cfg.load()
   except VarlordError as e:
       print(f"Configuration error {e.code}: {e.message}")

Catching Specific Exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from varlord import Config, ConfigLoadError, ValidationError

   cfg = Config(model=MyConfig, sources=[...])
   try:
       config = cfg.load()
   except ConfigLoadError as e:
       print(f"Failed to load from {e.source_name}: {e.message}")
   except ValidationError as e:
       print(f"Field {e.field_name} failed validation: {e.message}")

Error Codes
~~~~~~~~~~~

All exceptions have an error code for programmatic handling:

- ``CONFIG_LOAD_FAILED`` - Configuration loading failed
- ``SOURCE_LOAD_FAILED`` - Source failed to load
- ``VALIDATION_FAILED`` - Validation failed
- ``MISSING_REQUIRED_FIELD`` - Required field is missing
- ``INVALID_MODEL_DEFINITION`` - Model definition is invalid
- ``TYPE_CONVERSION_FAILED`` - Type conversion failed
- ``RESOLVER_FAILED`` - Source resolution failed

.. note::
   Always catch :class:`VarlordError` instead of generic :class:`Exception` to distinguish configuration errors from other exceptions.

.. seealso::
   :class:`~varlord.Config`
      Main configuration class

   :mod:`varlord.sources`
      Configuration sources
