from typing import Protocol

from flow3r.core.settings.abc.settings_menu import ISettingsMenu


class ISettingsMenusRegistry(Protocol):
    def register(self, settings_menu: ISettingsMenu): ...
