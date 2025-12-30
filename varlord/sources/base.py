"""
Base source abstraction.

Defines the interface that all configuration sources must implement.
"""

from __future__ import annotations
from typing import Mapping, Any, Iterator, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from typing import Protocol


@dataclass(frozen=True)
class ChangeEvent:
    """Represents a configuration change event.

    Attributes:
        key: The configuration key that changed
        old_value: The old value (None if key was added)
        new_value: The new value (None if key was removed)
        event_type: Type of change ('added', 'modified', 'deleted')
    """

    key: str
    old_value: Any
    new_value: Any
    event_type: str  # 'added', 'modified', 'deleted'


class Source:
    """Base class for all configuration sources.

    Each source must implement:
    - load() -> Mapping[str, Any]: Load configuration snapshot
    - name: str: Source name for debugging and priority configuration

    Optional:
    - watch() -> Iterator[ChangeEvent]: Stream of changes for dynamic updates
    """

    @property
    def name(self) -> str:
        """Return the source name.

        Returns:
            Source name, used for debugging and priority configuration.
        """
        raise NotImplementedError("Subclasses must implement name property")

    def load(self) -> Mapping[str, Any]:
        """Load configuration from this source.

        Returns:
            A mapping of configuration key-value pairs.
            Keys should be normalized (e.g., "db.host" for nested configs).
        """
        raise NotImplementedError("Subclasses must implement load()")

    def watch(self) -> Iterator[ChangeEvent]:
        """Watch for configuration changes (optional).

        Yields:
            ChangeEvent objects representing configuration changes.

        Note:
            This method is optional. Only sources that support dynamic
            updates (like etcd) should implement this.

            To enable watch support, override this method in your subclass.
            The default implementation returns an empty iterator, which
            indicates the source does not support watching.
        """
        # Default implementation: no-op
        # Sources that don't support watching can leave this as-is
        return iter([])

    def supports_watch(self) -> bool:
        """Check if this source supports watching.

        Returns:
            False by default. Subclasses that support watching must override
            this method to return True when watch is enabled.

        Note:
            To enable watch support, override this method in your subclass
            and return True when watch should be enabled.
        """
        return False

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<{self.__class__.__name__}(name={self.name!r})>"
