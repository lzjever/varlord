"""
Priority policy for configuration sources.

Defines how sources are ordered and merged, with support for
per-key priority rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PriorityPolicy:
    """Defines priority ordering for configuration sources.

    Supports:
    - Default priority for all keys
    - Per-key/namespace overrides using pattern matching
    - Source ID (exact match) or name (match all of type)

    Example:
        >>> policy = PriorityPolicy(
        ...     default=["defaults", "dotenv", "env", "cli"],
        ...     overrides={
        ...         "secrets.*": ["defaults", "etcd", "env"],  # Different rules for secrets
        ...     }
        ... )

        >>> # Using source ID for exact match:
        >>> policy = PriorityPolicy(
        ...     default=["defaults", "yaml:/etc/config.yaml", "yaml:~/.config/app.yaml", "env", "cli"],
        ... )

        >>> # Using source name to match all of type:
        >>> policy = PriorityPolicy(
        ...     default=["defaults", "yaml", "env", "cli"],  # All yaml sources before env
        ... )

        >>> # Mixed usage:
        >>> policy = PriorityPolicy(
        ...     default=["defaults", "yaml:/etc/config.yaml", "yaml", "env", "cli"],
        ...     # First specific system config, then all other yaml sources, then env and CLI
        ... )
    """

    default: List[str]
    """Default priority order for all keys.

    Can contain:
    - Source IDs (exact match, e.g., "yaml:/etc/config.yaml")
    - Source names (match all of type, e.g., "yaml")
    """

    overrides: Optional[Dict[str, List[str]]] = None
    """Per-key priority overrides.

    Keys are glob patterns (e.g., "secrets.*", "db.*").
    Values are priority lists for matching keys.
    Can contain source IDs or names (same as default).
    """

    def get_priority(self, key: str) -> List[str]:
        """Get priority order for a specific key.

        Args:
            key: Configuration key (e.g., "db.host", "secrets.api_key")

        Returns:
            List of source IDs or names in priority order (highest to lowest).
            - Source ID (e.g., "yaml:/etc/config.yaml"): Exact match
            - Source name (e.g., "yaml"): Match all sources with this name
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
