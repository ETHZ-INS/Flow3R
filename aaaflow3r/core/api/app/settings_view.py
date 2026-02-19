from typing import Protocol, Any

from aaaflow3r.core.settings import KeyPath


class ISettingsView(Protocol):
    def get(self, key_path: KeyPath) -> Any: ...
