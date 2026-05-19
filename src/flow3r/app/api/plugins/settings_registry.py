from typing import Tuple, Any, Dict


class SettingsRegistry:
    def __init__(self):
        self._settings: Dict[Tuple[str, ...], Any] = {}

    def register_setting(self, key: Tuple[str, ...], default: Any = None):
        self._settings[key] = default
