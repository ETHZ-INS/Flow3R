from typing import Protocol

from aaaflow3r.core.api.app.navigator_service import INavigatorService
from aaaflow3r.core.api.app.settings_service import ISettingsService


class IAppContext(Protocol):
    @property
    def navigator_service(self) -> INavigatorService: ...
    @property
    def settings_service(self) -> ISettingsService: ...
    # TODO: plugin information and general app information
