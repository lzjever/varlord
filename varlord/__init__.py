"""
Varlord - A powerful Python configuration management library.

Provides unified interface for loading configuration from multiple sources
with customizable priority ordering and optional dynamic updates.
"""

from varlord import sources
from varlord.config import Config
from varlord.global_config import (
    clear_global_configs,
    get_global_config,
    has_global_config,
    list_global_configs,
    remove_global_config,
    set_global_config,
)
from varlord.logging import get_logger, set_log_level
from varlord.policy import PriorityPolicy
from varlord.store import ConfigStore

__all__ = [
    "Config",
    "ConfigStore",
    "PriorityPolicy",
    "sources",
    "set_log_level",
    "get_logger",
    # Global config functions (optional feature)
    "set_global_config",
    "get_global_config",
    "has_global_config",
    "remove_global_config",
    "clear_global_configs",
    "list_global_configs",
]

__version__ = "0.7.0"
