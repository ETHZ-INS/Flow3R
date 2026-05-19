from typing import Dict, Any

from flow3r.core.api.app.settings_view import ISettingsView
from flow3r.core.settings import KeyPath


class SettingsView(ISettingsView):
    def __init__(self, settings: Dict[KeyPath, Any]):
        self._settings = settings

    def get(self, key_path: KeyPath) -> Any:
        return self._settings.get(key_path)
