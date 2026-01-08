"""
Tests for Resolver class.
"""

from varlord.policy import PriorityPolicy
from varlord.resolver import Resolver
from varlord.sources.base import Source


class MockSource(Source):
    """Mock source for testing."""

    def __init__(self, name: str, config: dict, source_id: str = None):
        super().__init__(source_id=source_id or name)
        self._name = name
        self._config = config

    @property
    def name(self) -> str:
        return self._name

    def load(self):
        return self._config


def test_resolver_basic():
    """Test basic resolver functionality."""
    source1 = MockSource("source1", {"key1": "value1", "key2": "value2"})
    source2 = MockSource("source2", {"key2": "value2_override", "key3": "value3"})

    resolver = Resolver(sources=[source1, source2])
    result = resolver.resolve()

    assert result["key1"] == "value1"
    assert result["key2"] == "value2_override"  # source2 overrides source1
    assert result["key3"] == "value3"


def test_resolver_priority():
    """Test resolver with sources order."""
    source1 = MockSource("source1", {"key": "value1"})
    source2 = MockSource("source2", {"key": "value2"})

    # Later source overrides earlier one
    resolver = Resolver(sources=[source1, source2])
    result = resolver.resolve()

    # source2 is later, so it should override source1
    assert result["key"] == "value2"


def test_resolver_priority_policy():
    """Test resolver with PriorityPolicy per-key rules."""
    source1 = MockSource("source1", {"key1": "value1", "key2": "value2"})
    source2 = MockSource("source2", {"key1": "value1_override", "key2": "value2_override"})

    policy = PriorityPolicy(
        default=["source1", "source2"],
        overrides={
            "key2": ["source1"],  # key2 should only use source1
        },
    )

    resolver = Resolver(sources=[source1, source2], policy=policy)
    result = resolver.resolve()

    assert result["key1"] == "value1_override"  # source2 overrides
    assert result["key2"] == "value2"  # Only source1 (per policy)


def test_resolver_deep_merge():
    """Test deep merge functionality."""
    source1 = MockSource("source1", {"nested": {"key1": "value1", "key2": "value2"}})
    source2 = MockSource("source2", {"nested": {"key2": "value2_override", "key3": "value3"}})

    resolver = Resolver(sources=[source1, source2])
    result = resolver.resolve()

    assert result["nested"]["key1"] == "value1"
    assert result["nested"]["key2"] == "value2_override"
    assert result["nested"]["key3"] == "value3"
