"""
Varlord exception hierarchy.

All Varlord exceptions inherit from :class:`VarlordError` for consistent error handling.
Each exception has an error code for programmatic handling.
"""

from typing import Optional


class VarlordError(Exception):
    """Base exception for all Varlord errors.

    All exceptions raised by Varlord inherit from this class, allowing users to:
    - Catch all Varlord errors with ``except VarlordError``
    - Identify error types programmatically using the ``code`` attribute

    Attributes:
        message: Human-readable error message
        code: Machine-readable error code (e.g., "CONFIG_LOAD_FAILED")

    Example:
        >>> try:
        ...     cfg.load()
        ... except VarlordError as e:
        ...     print(f"Error {e.code}: {e.message}")
    """

    def __init__(self, message: str, code: Optional[str] = None):
        """Initialize VarlordError.

        Args:
            message: Human-readable error message
            code: Machine-readable error code (defaults to class name)
        """
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"

    def __str__(self) -> str:
        """Return user-friendly string representation."""
        return self.message


class ConfigError(VarlordError):
    """Base exception for configuration-related errors."""

    pass


class ConfigLoadError(ConfigError):
    """Raised when configuration loading fails.

    This can occur when:
    - A source fails to load (e.g., file not found, permission denied)
    - Type conversion fails (e.g., invalid int value)
    - Validation fails (e.g., missing required field)

    Attributes:
        source_name: Name of the source that failed (if applicable)
    """

    def __init__(
        self,
        message: str,
        source_name: Optional[str] = None,
        code: str = "CONFIG_LOAD_FAILED",
    ):
        """Initialize ConfigLoadError.

        Args:
            message: Human-readable error message
            source_name: Name of the source that failed (e.g., "yaml", "env")
            code: Machine-readable error code
        """
        self.source_name = source_name
        if source_name:
            message = f"[{source_name}] {message}"
        super().__init__(message, code=code)


class SourceLoadError(ConfigLoadError):
    """Raised when a configuration source fails to load.

    This is a subclass of :class:`ConfigLoadError` for backward compatibility.
    """

    pass


class ValidationError(ConfigError):
    """Raised when configuration validation fails.

    This can occur when:
    - Required fields are missing
    - Field values fail custom validation
    - Model definition is invalid
    """

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        code: str = "VALIDATION_FAILED",
    ):
        """Initialize ValidationError.

        Args:
            message: Human-readable error message
            field_name: Name of the field that failed validation (if applicable)
            code: Machine-readable error code
        """
        self.field_name = field_name
        if field_name:
            message = f"Field '{field_name}': {message}"
        super().__init__(message, code=code)


class RequiredFieldError(ValidationError):
    """Raised when a required field is missing.

    Attributes:
        field_name: Name of the missing required field
    """

    def __init__(self, message: str, field_name: Optional[str] = None):
        """Initialize RequiredFieldError.

        Args:
            message: Human-readable error message
            field_name: Name of the missing required field
        """
        if field_name is None:
            # Extract field name from message if possible
            if "field" in message.lower():
                # Try to extract field name from message
                import re

                match = re.search(r"field\s+['\"]?(\w+)['\"]?", message, re.IGNORECASE)
                if match:
                    field_name = match.group(1)

        super().__init__(message, field_name=field_name, code="MISSING_REQUIRED_FIELD")


class ModelDefinitionError(ValidationError):
    """Raised when model definition is invalid.

    This can occur when:
    - Fields are missing required metadata
    - Field types are unsupported
    - Field names conflict with reserved names
    """

    def __init__(self, message: str) -> None:
        """Initialize ModelDefinitionError.

        Args:
            message: Human-readable error message
        """
        super().__init__(message, code="INVALID_MODEL_DEFINITION")


class ResolverError(ConfigError):
    """Raised when source resolution fails.

    This can occur when:
    - Priority policy is invalid
    - Source merge fails
    - Circular dependencies detected
    """

    def __init__(self, message: str, code: str = "RESOLVER_FAILED") -> None:
        """Initialize ResolverError.

        Args:
            message: Human-readable error message
            code: Machine-readable error code
        """
        super().__init__(message, code=code)


class ConversionError(ConfigError):
    """Raised when type conversion fails.

    This can occur when:
    - String value cannot be converted to target type
    - Invalid boolean value (not "true"/"false"/"1"/"0")
    - Invalid numeric value (not an integer/float)
    """

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_type: Optional[str] = None,
        value: Optional[str] = None,
    ) -> None:
        """Initialize ConversionError.

        Args:
            message: Human-readable error message
            field_name: Name of the field that failed conversion
            field_type: Target type name (e.g., "int", "bool")
            value: The value that failed to convert
        """
        self.field_name = field_name
        self.field_type = field_type
        self.value = value

        details = []
        if field_name:
            details.append(f"field={field_name}")
        if field_type:
            details.append(f"type={field_type}")
        if value:
            details.append(f"value={value!r}")

        if details:
            message = f"{message} ({', '.join(details)})"

        super().__init__(message, code="TYPE_CONVERSION_FAILED")


# Error code registry (for documentation)
ERROR_CODES = {
    "CONFIG_LOAD_FAILED": ConfigLoadError,
    "SOURCE_LOAD_FAILED": SourceLoadError,
    "VALIDATION_FAILED": ValidationError,
    "MISSING_REQUIRED_FIELD": RequiredFieldError,
    "INVALID_MODEL_DEFINITION": ModelDefinitionError,
    "RESOLVER_FAILED": ResolverError,
    "TYPE_CONVERSION_FAILED": ConversionError,
}


def get_error_class(code: str) -> Optional[type]:
    """Get exception class by error code.

    Args:
        code: Error code (e.g., "CONFIG_LOAD_FAILED")

    Returns:
        Exception class or None if code not found

    Example:
        >>> cls = get_error_class("CONFIG_LOAD_FAILED")
        >>> cls  # doctest: +SKIP
        <class 'varlord.exceptions.ConfigLoadError'>
    """
    return ERROR_CODES.get(code)
