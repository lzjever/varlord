Logging
=======

Varlord provides configurable logging to track configuration loading and merging.

Enable Logging
--------------

.. code-block:: python

   import logging
   from varlord import set_log_level

   # Enable debug logging
   set_log_level(logging.DEBUG)

   cfg = Config(...)
   app = cfg.load()

Log Levels
----------

- **WARNING** (default): Only warnings and errors
- **INFO**: Configuration loading summary
- **DEBUG**: Detailed information about sources, merges, and conversions

What Gets Logged
----------------

**DEBUG Level:**
   - Source loading (number of items from each source)
   - Configuration merging (each key-value merge)
   - Type conversions (original → converted)
   - Validation errors

**INFO Level:**
   - Successful configuration loads
   - Model name and number of keys

**WARNING Level:**
   - Validation failures
   - Type conversion failures

**ERROR Level:**
   - Critical errors (source failures, etc.)

Example Output
--------------

.. code-block::

   varlord - DEBUG - Loaded 3 items from source 'defaults'
   varlord - DEBUG - Merged 'host' = '127.0.0.1' from source 'defaults'
   varlord - DEBUG - Merged 'port' = 8000 from source 'defaults'
   varlord - DEBUG - Loaded 2 items from source 'env'
   varlord - DEBUG - Merged 'host' = '0.0.0.0' from source 'env'
   varlord - DEBUG - Converted 'port': '9000' (str) -> 9000 (int)
   varlord - INFO - Loaded configuration 'AppConfig' with 3 keys

