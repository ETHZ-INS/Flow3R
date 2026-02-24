from typing import Dict

from flow3r.core.settings.abc.settings_menu import ISettingsMenu


class SettingsMenuRegistry:
    def __init__(self):
        self._settings_menus: Dict[str, ISettingsMenu] = {}

    def register(self, settings_menu: ISettingsMenu):
        self._settings_menus[settings_menu.name] = settings_menu

    def get_settings_menus(self) -> Dict[str, ISettingsMenu]:
        return self._settings_menus
