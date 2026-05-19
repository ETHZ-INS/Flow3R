from typing import Any, Dict, List

from PySide6.QtCore import QObject, Signal, Slot, Qt

from flow3r.app.config.system_placeholders import SYSTEM_PLACEHOLDERS
from flow3r.app.controller.controller import Controller
from flow3r.core.placeholder.placeholder_info import PlaceholderInfo
from flow3r.logger import get_logger

logger = get_logger(__name__)


class PlaceholderService(QObject):
    # UI subscribers
    changed = Signal()                          # flat preview dict or placeholder list changed
    group_values_changed = Signal(str, object)  # group_id, Dict[str, Any]

    # UI -> Controller snapshot requests
    _config_snapshot_requested = Signal()
    _group_snapshot_requested = Signal()

    def __init__(self, controller: Controller) -> None:
        super().__init__()
        # User-configured placeholders (derived from config)
        self._user_placeholders: List[PlaceholderInfo] = []
        self._config_values: Dict[str, Any] = {}
        self._group_values: Dict[str, Dict[str, Any]] = {}

        # Controller thread -> UI thread (force queued — controller is on worker thread)
        controller.config_snapshot.connect(self._on_config, Qt.ConnectionType.QueuedConnection)
        controller.config_changed.connect(self._on_config, Qt.ConnectionType.QueuedConnection)
        controller.group_placeholder_values_changed.connect(
            self._on_group_values, Qt.ConnectionType.QueuedConnection
        )
        controller.group_removed.connect(self._on_group_removed, Qt.ConnectionType.QueuedConnection)

        # UI thread -> Controller thread (force queued)
        self._config_snapshot_requested.connect(
            controller.send_config_snapshot, Qt.ConnectionType.QueuedConnection
        )
        self._group_snapshot_requested.connect(
            controller.send_group_placeholder_snapshots, Qt.ConnectionType.QueuedConnection
        )

        # Request initial state
        self._config_snapshot_requested.emit()
        self._group_snapshot_requested.emit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def placeholders(self) -> List[PlaceholderInfo]:
        """
        Full list of known placeholders: system built-ins first, then
        user-configured ones (in config order).  Each entry carries both
        a ``name`` (template key) and a human-readable ``label``.
        """
        return list(SYSTEM_PLACEHOLDERS) + self._user_placeholders

    @property
    def names(self) -> List[str]:
        """Convenience: just the ``name`` field of every PlaceholderInfo."""
        return [p.name for p in self.placeholders]

    @property
    def values(self) -> Dict[str, Any]:
        """First group's values (includes global values) if any groups exist, else config values."""
        if self._group_values:
            return next(iter(self._group_values.values()))
        return self._config_values

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot(object)
    def _on_config(self, config) -> None:
        self._user_placeholders = [
            PlaceholderInfo(name=pc.name, label=pc.label)
            for pc in config.placeholders.values()
        ]
        self._config_values = dict(config.global_placeholder_values_dict)
        self.changed.emit()

    @Slot(str, object)
    def _on_group_values(self, group_id: str, values: Dict[str, Any]) -> None:
        logger.debug("Received group placeholder values for group %s", group_id)
        self._group_values[group_id] = values
        self.group_values_changed.emit(group_id, values)
        self.changed.emit()

    @Slot(str)
    def _on_group_removed(self, group_id: str) -> None:
        if group_id in self._group_values:
            del self._group_values[group_id]
            self.changed.emit()


