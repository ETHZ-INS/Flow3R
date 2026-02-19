from typing import Protocol, Any, Dict, Callable

from aaaflow3r.core.settings import KeyPath
from aaaflow3r.core.visualization.abc.visualizer_handle import IConnectableSignal

Handler = Callable[[Dict[KeyPath, Any]], None]


class ISettingsService(Protocol):
    @property
    def changed(self) -> IConnectableSignal: ...

    def get(self, key_path: KeyPath, default: Any = None) -> Any: ...
    def set(self, key_path: KeyPath, value: Any) -> None: ...
    def set_many(self, patch: Dict[KeyPath, Any]) -> None: ...
