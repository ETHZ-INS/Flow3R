from typing import Any, Dict, List, Protocol

from flow3r.core.placeholder.placeholder_info import PlaceholderInfo
from flow3r.core.visualization.abc.visualizer_handle import IConnectableSignal


class IPlaceholderService(Protocol):
    @property
    def changed(self) -> IConnectableSignal:
        """Emitted whenever the flat preview values or names change."""
        ...

    @property
    def group_values_changed(self) -> IConnectableSignal:
        """Emitted with (group_id: str, values: Dict[str, Any]) when a specific group's values change."""
        ...

    @property
    def placeholders(self) -> List[PlaceholderInfo]:
        """
        Full list of known placeholders (system built-ins + user-configured),
        each carrying a ``name`` and a human-readable ``label``.
        """
        ...

    @property
    def names(self) -> List[str]:
        """Convenience: just the ``name`` field of every PlaceholderInfo in ``placeholders``."""
        ...

    @property
    def values(self) -> Dict[str, Any]:
        """Best-effort flat preview dict: first group's values if any groups exist, otherwise config values."""
        ...

