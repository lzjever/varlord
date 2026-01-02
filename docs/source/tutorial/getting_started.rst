Getting Started
===============

In this first tutorial, you'll learn the basics of Varlord by creating a simple
configuration and loading it from defaults.

Learning Objectives
-------------------

By the end of this tutorial, you'll be able to:

- Define a configuration model using dataclasses
- Load configuration from default values
- Understand the basic structure of a Varlord application

Step 1: Define Your Configuration Model
---------------------------------------

First, let's create a simple configuration model for a web application:

.. code-block:: python
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="127.0.0.1")
       port: int = field(default=8000)
       debug: bool = field(default=False)
       app_name: str = field(default="MyApp")

   # Create configuration
   # Model defaults are automatically applied - no need for sources.Defaults
   cfg = Config(
       model=AppConfig,
       sources=[],  # No sources needed - defaults are automatic
   )

   # Load configuration
   app = cfg.load()

   # Use configuration
   print(f"Starting {app.app_name} on {app.host}:{app.port}")
   print(f"Debug mode: {app.debug}")

**Expected Output**:

.. code-block:: text

   Starting MyApp on 127.0.0.1:8000
   Debug mode: False

**Key Points**:

- Use ``@dataclass(frozen=True)`` to create immutable configuration objects
- Fields are automatically determined as required/optional:
  - Fields **without defaults** and **not Optional[T]** are **required**
  - Fields **with Optional[T]** type annotation are **optional**
  - Fields **with defaults** (or ``default_factory``) are **optional**
- Model defaults are automatically applied - no need for ``sources.Defaults``
- ``cfg.load()`` returns an instance of your configuration model

Step 2: Access Configuration Values
------------------------------------

Configuration values can be accessed as attributes:

.. code-block:: python
   :linenos:

   app = cfg.load()

   # Access as attributes
   print(f"Host: {app.host}")
   print(f"Port: {app.port}")

   # Configuration is immutable (frozen=True)
   # app.host = "0.0.0.0"  # This would raise FrozenInstanceError

**Expected Output**:

.. code-block:: text

   Host: 127.0.0.1
   Port: 8000

**Important**: Since we used ``frozen=True``, configuration objects are
immutable. This prevents accidental modification and ensures consistency.

Step 3: Complete Example
-------------------------

Here's a complete working example:

.. code-block:: python
   :name: getting_started_complete
   :linenos:

   from dataclasses import dataclass, field
   from varlord import Config

   @dataclass(frozen=True)
   class AppConfig:
       host: str = field(default="127.0.0.1")
       port: int = field(default=8000)
       debug: bool = field(default=False)
       app_name: str = field(default="MyApp")

   def main():
       cfg = Config(
           model=AppConfig,
           sources=[],  # Defaults are automatically applied
       )

       app = cfg.load()
       print(f"Configuration loaded:")
       print(f"  App: {app.app_name}")
       print(f"  Host: {app.host}")
       print(f"  Port: {app.port}")
       print(f"  Debug: {app.debug}")

   if __name__ == "__main__":
       main()

**Expected Output**:

.. code-block:: text

   Configuration loaded:
     App: MyApp
     Host: 127.0.0.1
     Port: 8000
     Debug: False

Common Pitfalls
---------------

**Pitfall 1: Forgetting to provide defaults**

.. code-block:: python
   :emphasize-lines: 4

   @dataclass(frozen=True)
   class AppConfig:
       host: str  # Missing default value!
       port: int = 8000

   # This will fail if no other source provides 'host'
   app = cfg.load()  # May raise TypeError

**Solution**: Always provide default values for optional fields, or use ``Optional[T]``
type annotation for fields that may not be set.

**Pitfall 4: Not using frozen dataclasses**

.. code-block:: python
   :emphasize-lines: 1

   @dataclass  # Missing frozen=True
   class AppConfig:
       host: str = field(default="127.0.0.1")

   app = cfg.load()
   app.host = "0.0.0.0"  # This works, but breaks immutability!

**Solution**: Always use ``@dataclass(frozen=True)`` to ensure configuration
immutability.

Best Practices
--------------

1. **Use descriptive field names**: Choose clear, self-documenting names
2. **Fields are automatically determined**: Use ``Optional[T]`` type annotation or default values for optional fields
3. **Provide sensible defaults**: Defaults should work for development
4. **Use appropriate types**: Use ``int``, ``str``, ``bool``, ``Optional[T]``, etc. correctly
5. **Add field descriptions**: Use ``metadata={"description": "..."}`` for better documentation
6. **Keep it simple**: Start with defaults, add complexity as needed

Next Steps
----------

Now that you understand the basics, let's move on to :doc:`multiple_sources`
to learn how to load configuration from environment variables and command-line
arguments.

