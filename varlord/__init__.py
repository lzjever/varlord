"""
Varlord - A powerful Python configuration management library.

Provides unified interface for loading configuration from multiple sources
with customizable priority ordering and optional dynamic updates.
"""

from varlord import sources
from varlord.config import Config
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
]

__version__ = "0.5.0"
