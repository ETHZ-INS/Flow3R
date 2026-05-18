from typing import Protocol

from flow3r.core.api.app.navigator_service import INavigatorService
from flow3r.core.api.app.placeholder_service import IPlaceholderService
from flow3r.core.api.app.settings_service import ISettingsService


class IAppContext(Protocol):
    @property
    def navigator_service(self) -> INavigatorService: ...
    @property
    def settings_service(self) -> ISettingsService: ...
    @property
    def placeholder_service(self) -> IPlaceholderService: ...
    # TODO: plugin information and general app information
