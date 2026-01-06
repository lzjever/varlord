"""
Logging support for varlord.

Provides configurable logging to track configuration loading,
merging, and type conversion.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

# Default logger
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Get or create the varlord logger.

    Returns:
        Logger instance for varlord.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger("varlord")
        # Set default level to WARNING to avoid noise
        _logger.setLevel(logging.WARNING)
        # Add handler if none exists
        if not _logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
            _logger.addHandler(handler)
    return _logger


def set_log_level(level: int) -> None:
    """Set the logging level for varlord.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
    """
    get_logger().setLevel(level)


def log_source_load(source_name: str, count: int) -> None:
    """Log source loading.

    Args:
        source_name: Name of the source
        count: Number of configuration items loaded
    """
    logger = get_logger()
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Loaded {count} items from source '{source_name}'")


def log_merge(source_name: str, key: str, value: Any) -> None:
    """Log configuration merge.

    Args:
        source_name: Name of the source
        key: Configuration key
        value: Configuration value
    """
    logger = get_logger()
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Merged '{key}' = {value!r} from source '{source_name}'")


def log_type_conversion(key: str, value: Any, target_type: type, result: Any) -> None:
    """Log type conversion.

    Args:
        key: Configuration key
        value: Original value
        target_type: Target type
        result: Converted value
    """
    logger = get_logger()
    if logger.isEnabledFor(logging.DEBUG):
        if value != result or type(value) is not type(result):
            logger.debug(
                f"Converted '{key}': {value!r} ({type(value).__name__}) -> "
                f"{result!r} ({type(result).__name__})"
            )


def log_validation_error(key: str, value: Any, error: str) -> None:
    """Log validation error.

    Args:
        key: Configuration key
        value: Invalid value
        error: Error message
    """
    logger = get_logger()
    logger.warning(f"Validation failed for '{key}' = {value!r}: {error}")


def log_config_loaded(model_name: str, keys: list[str]) -> None:
    """Log successful configuration load.

    Args:
        model_name: Name of the configuration model
        keys: List of loaded configuration keys
    """
    logger = get_logger()
    if logger.isEnabledFor(logging.INFO):
        logger.info(f"Loaded configuration '{model_name}' with {len(keys)} keys")


def log_error(message: str, exc: Optional[Exception] = None) -> None:
    """Log error.

    Args:
        message: Error message
        exc: Optional exception
    """
    logger = get_logger()
    logger.error(message, exc_info=exc)
