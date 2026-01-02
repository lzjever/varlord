"""
Priority policy for configuration sources.

Defines how sources are ordered and merged, with support for
per-key priority rules.
"""

from __future__ import annotations
from typing import List, Dict, Optional
import re
from dataclasses import dataclass


@dataclass
class PriorityPolicy:
    """Defines priority ordering for configuration sources.

    Supports:
    - Default priority for all keys
    - Per-key/namespace overrides using pattern matching

    Example:
        >>> policy = PriorityPolicy(
        ...     default=["defaults", "dotenv", "env", "cli"],
        ...     overrides={
        ...         "secrets.*": ["defaults", "etcd", "env"],  # Different rules for secrets
        ...     }
        ... )
    """

    default: List[str]
    """Default priority order for all keys."""

    overrides: Optional[Dict[str, List[str]]] = None
    """Per-key priority overrides.

    Keys are glob patterns (e.g., "secrets.*", "db.*").
    Values are priority lists for matching keys.
    """

    def get_priority(self, key: str) -> List[str]:
        """Get priority order for a specific key.

        Args:
            key: Configuration key (e.g., "db.host", "secrets.api_key")

        Returns:
            List of source names in priority order (highest to lowest).
        """
        if self.overrides:
            for pattern, priority in self.overrides.items():
                # Convert glob pattern to regex
                regex_pattern = pattern.replace(".", r"\.").replace("*", ".*")
                if re.match(regex_pattern, key):
                    return priority

        return self.default

    def __repr__(self) -> str:
        """Return string representation."""
        overrides_str = (
            f", overrides={len(self.overrides or {})} patterns" if self.overrides else ""
        )
        return f"<PriorityPolicy(default={self.default}{overrides_str})>"
