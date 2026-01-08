"""
Configuration resolver and merger.

Handles merging configuration from multiple sources according to priority.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from varlord.policy import PriorityPolicy
from varlord.sources.base import Source


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

        # Build source ID -> source mapping (for PriorityPolicy with exact ID matching)
        self._source_map: Dict[str, Source] = {source.id: source for source in sources}

        # Build name -> sources mapping (for PriorityPolicy with name matching)
        self._name_to_sources: Dict[str, List[Source]] = {}
        for source in sources:
            name = source.name
            if name not in self._name_to_sources:
                self._name_to_sources[name] = []
            self._name_to_sources[name].append(source)

    def _get_source_order(self, key: Optional[str] = None) -> List[Source]:
        """Get ordered list of sources for a given key.

        Args:
            key: Optional configuration key (for per-key priority rules)

        Returns:
            List of sources in priority order (later sources override earlier ones).
        """
        # Use policy if available (for per-key rules)
        if self._policy:
            priority_names_or_ids = self._policy.get_priority(key or "")
            sources = []
            for name_or_id in priority_names_or_ids:
                if name_or_id in self._source_map:
                    # Exact ID match
                    sources.append(self._source_map[name_or_id])
                elif name_or_id in self._name_to_sources:
                    # Name match - add all sources with this name
                    # Maintain order from sources list
                    for source in self._sources:
                        if source.name == name_or_id and source not in sources:
                            sources.append(source)
            return sources

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
                from varlord.logging import log_merge, log_source_load

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
        # First, load all sources (use source.id as key)
        all_configs: Dict[str, Dict[str, Any]] = {}
        for source in self._sources:
            all_configs[source.id] = source.load()

        # Collect all keys from all sources
        all_keys: set[str] = set()
        for config in all_configs.values():
            all_keys.update(config.keys())

        # Resolve each key according to its priority
        result: Dict[str, Any] = {}
        for key in all_keys:
            priority_names_or_ids = self._policy.get_priority(key)  # type: ignore
            # Merge sources in priority order for this key
            # Later sources in the list override earlier ones
            for name_or_id in priority_names_or_ids:
                # Check if it's an exact ID match
                if name_or_id in all_configs:
                    if key in all_configs[name_or_id]:
                        result[key] = all_configs[name_or_id][key]
                        # Don't break - continue to let later sources override
                # Check if it's a name match (match all sources with this name)
                elif name_or_id in self._name_to_sources:
                    # Check all sources with this name, in order
                    for source in self._name_to_sources[name_or_id]:
                        if source.id in all_configs and key in all_configs[source.id]:
                            result[key] = all_configs[source.id][key]
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
