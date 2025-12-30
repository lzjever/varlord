"""
Configuration resolver and merger.

Handles merging configuration from multiple sources according to priority.
"""

from __future__ import annotations
from typing import Mapping, Any, List, Dict, Optional
from collections.abc import MutableMapping

from varlord.sources.base import Source
from varlord.policy import PriorityPolicy


class Resolver:
    """Resolves and merges configuration from multiple sources.

    Handles:
    - Source ordering by priority
    - Merging configurations (later sources override earlier ones)
    - Per-key priority rules via PriorityPolicy
    """

    def __init__(
        self,
        sources: List[Source],
        policy: Optional[PriorityPolicy] = None,
    ):
        """Initialize Resolver.

        Args:
            sources: List of configuration sources (order determines priority)
            policy: Optional PriorityPolicy for per-key rules

        Note:
            Priority is determined by sources order: later sources override earlier ones.
            Use PriorityPolicy only when you need per-key priority rules.
        """
        self._sources = sources
        self._policy = policy

        # Build source name -> source mapping (for PriorityPolicy)
        self._source_map: Dict[str, Source] = {source.name: source for source in sources}

    def _get_source_order(self, key: Optional[str] = None) -> List[Source]:
        """Get ordered list of sources for a given key.

        Args:
            key: Optional configuration key (for per-key priority rules)

        Returns:
            List of sources in priority order (later sources override earlier ones).
        """
        # Use policy if available (for per-key rules)
        if self._policy:
            priority_names = self._policy.get_priority(key or "")
            return [self._source_map[name] for name in priority_names if name in self._source_map]

        # Default: use sources in order provided
        return self._sources

    def resolve(self, key: Optional[str] = None) -> Dict[str, Any]:
        """Resolve configuration by merging sources.

        Args:
            key: Optional key for per-key priority rules (if using PriorityPolicy)

        Returns:
            Merged configuration dictionary.
        """
        # If using PriorityPolicy, resolve each key separately
        if self._policy:
            return self._resolve_with_policy()

        result: Dict[str, Any] = {}
        source_order = self._get_source_order(key)

        # Merge sources in priority order (later sources override earlier ones)
        for source in source_order:
            config = source.load()
            try:
                from varlord.logging import log_source_load, log_merge

                log_source_load(source.name, len(config))
                # Log individual merges in debug mode
                for k, v in config.items():
                    log_merge(source.name, k, v)
            except ImportError:
                pass  # Logging not available

            self._deep_merge(result, config)

        return result

    def _resolve_with_policy(self) -> Dict[str, Any]:
        """Resolve configuration using PriorityPolicy (per-key rules).

        Returns:
            Merged configuration dictionary.
        """
        # First, load all sources
        all_configs: Dict[str, Dict[str, Any]] = {}
        for source in self._sources:
            all_configs[source.name] = source.load()

        # Collect all keys from all sources
        all_keys: set[str] = set()
        for config in all_configs.values():
            all_keys.update(config.keys())

        # Resolve each key according to its priority
        result: Dict[str, Any] = {}
        for key in all_keys:
            priority_names = self._policy.get_priority(key)  # type: ignore
            # Merge sources in priority order for this key
            # Later sources in the list override earlier ones
            for source_name in priority_names:
                if source_name in all_configs and key in all_configs[source_name]:
                    result[key] = all_configs[source_name][key]
                    # Don't break - continue to let later sources override

        return result

    def _deep_merge(self, base: Dict[str, Any], update: Mapping[str, Any]) -> None:
        """Deep merge update into base.

        Args:
            base: Base dictionary to merge into (modified in place)
            update: Dictionary to merge from
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                self._deep_merge(base[key], value)
            else:
                # Overwrite with new value
                base[key] = value

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Resolver(sources={len(self._sources)}, policy={self._policy is not None})>"
