"""
Varlord - A powerful Python configuration management library.

Provides unified interface for loading configuration from multiple sources
with customizable priority ordering and optional dynamic updates.
"""

from varlord.config import Config
from varlord.store import ConfigStore
from varlord.policy import PriorityPolicy
from varlord import sources
from varlord.logging import set_log_level, get_logger

__all__ = [
    "Config",
    "ConfigStore",
    "PriorityPolicy",
    "sources",
    "set_log_level",
    "get_logger",
]

__version__ = "0.1.0"
