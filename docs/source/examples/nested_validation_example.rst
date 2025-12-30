Nested Validation Example
==========================

This example demonstrates validation with nested configuration structures.

Source Code
-----------

.. literalinclude:: ../../../examples/nested_validation_example.py
   :language: python
   :linenos:

Key Points
----------

1. **Nested Validation**: Each nested dataclass (``DBConfig``, ``APIConfig``) has its
   own ``__post_init__`` method for validation.

2. **Automatic Validation**: When nested objects are created, their ``__post_init__``
   methods are automatically called. You don't need to manually validate nested objects
   in the parent's ``__post_init__``.

3. **Cross-Field Validation**: The parent ``AppConfig.__post_init__`` can validate
   relationships between fields, including nested fields.

4. **Error Handling**: Validation errors provide detailed information about which key
   failed and why.

Running the Example
-------------------

.. code-block:: bash

   python examples/nested_validation_example.py

Expected Output
---------------

.. code-block:: text

   Config loaded successfully:
     Host: 0.0.0.0:8000
     DB: localhost:5432 (max_conn=10)
     API: https://api.example.com (timeout=30s, retries=3)

