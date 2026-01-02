Validators
==========

This module provides comprehensive validation functions for configuration values.

.. automodule:: varlord.validators
   :members:
   :undoc-members:
   :show-inheritance:

Validator Categories
--------------------

The validators are organized into the following categories:

**Basic Validators**
   - :func:`validate_range` - Validate value is within a range
   - :func:`validate_regex` - Validate string matches regex pattern
   - :func:`validate_choice` - Validate value is in a list of choices
   - :func:`validate_not_empty` - Validate value is not empty

**Numeric Validators**
   - :func:`validate_positive` - Validate number is positive
   - :func:`validate_non_negative` - Validate number is non-negative
   - :func:`validate_integer` - Validate value is an integer
   - :func:`validate_float` - Validate value is a float
   - :func:`validate_percentage` - Validate number is 0-100
   - :func:`validate_port` - Validate port number (1-65535)
   - :func:`validate_greater_than` - Validate number is greater than threshold
   - :func:`validate_less_than` - Validate number is less than threshold

**String Validators**
   - :func:`validate_length` - Validate string length
   - :func:`validate_email` - Validate email address
   - :func:`validate_url` - Validate URL
   - :func:`validate_ipv4` - Validate IPv4 address
   - :func:`validate_ipv6` - Validate IPv6 address
   - :func:`validate_ip` - Validate IPv4 or IPv6 address
   - :func:`validate_domain` - Validate domain name
   - :func:`validate_phone` - Validate phone number
   - :func:`validate_uuid` - Validate UUID
   - :func:`validate_base64` - Validate Base64 encoded data
   - :func:`validate_json_string` - Validate JSON string
   - :func:`validate_date_format` - Validate date format
   - :func:`validate_time_format` - Validate time format
   - :func:`validate_datetime_format` - Validate datetime format

**Collection Validators**
   - :func:`validate_list_length` - Validate list length
   - :func:`validate_dict_keys` - Validate dictionary keys

**File/Path Validators**
   - :func:`validate_file_path` - Validate file path
   - :func:`validate_directory_path` - Validate directory path

**Custom Validators**
   - :func:`validate_custom` - Validate using custom function
   - :func:`apply_validators` - Apply validators to configuration object
