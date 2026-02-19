from typing import Tuple, Any, Protocol


class ISettingsRegistry(Protocol):
    def register_setting(self, key: Tuple[str, ...], default: Any = None): ...
