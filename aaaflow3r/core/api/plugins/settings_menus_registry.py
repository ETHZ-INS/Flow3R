from typing import Protocol

from aaaflow3r.core.settings.abc.settings_menu import ISettingsMenu


class ISettingsMenusRegistry(Protocol):
    def register(self, settings_menu: ISettingsMenu): ...
