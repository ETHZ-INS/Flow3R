from copy import deepcopy
from typing import Dict, Any

from PySide6.QtCore import QObject, Signal, Slot, Qt

from aaaflow3r.app.controller.controller import Controller
from aaaflow3r.core.api.app.settings_service import Handler
from aaaflow3r.core.settings import KeyPath


class SettingsService(QObject):
    # Store -> UI subscribers (always emitted on UI thread)
    changed = Signal(object)    # patch: Dict[KeyPath, Any]

    # UI -> Store
    snapshot_requested = Signal()
    patch_requested = Signal(object)

    def __init__(self, controller: Controller) -> None:
        super().__init__()
        self._controller = controller
        self._cache_state: Dict[KeyPath, Any] = {}

        # Controller thread -> UI thread (force queued)
        controller.settings_changed.connect(self._on_store_changed, Qt.ConnectionType.QueuedConnection)
        controller.settings_snapshot.connect(self._on_store_snapshot, Qt.ConnectionType.QueuedConnection)

        # UI thread -> Controller thread (force queued)
        self.patch_requested.connect(controller.set_settings, Qt.ConnectionType.QueuedConnection)
        self.snapshot_requested.connect(controller.send_settings_snapshot, Qt.ConnectionType.QueuedConnection)

        self.snapshot_requested.emit()

    def get(self, key_path: KeyPath, default: Any = None) -> Any:
        return self._cache_state.get(key_path, default)

    def set(self, key_path: KeyPath, value: Any) -> None:
        print("set", key_path, value)
        self.patch_requested.emit({key_path: deepcopy(value)})

    def set_many(self, patch: Dict[KeyPath, Any]) -> None:
        self.patch_requested.emit(deepcopy(patch))

    @Slot(object)
    def _on_store_changed(self, patch: Dict[KeyPath, Any]) -> None:
        print("Store changed", patch)
        # Update cache then notify UI subscribers
        for k, v in patch.items():
            self._cache_state[k] = deepcopy(v)
        self.changed.emit(deepcopy(patch))

    @Slot(object)
    def _on_store_snapshot(self, state: Dict[KeyPath, Any]) -> None:
        print("Store snapshot", state)
        self._cache_state = deepcopy(state)
        self.changed.emit(deepcopy(state))
        self._controller.settings_snapshot.disconnect(self._on_store_snapshot)
