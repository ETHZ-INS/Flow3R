from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.api.app.navigator_service import INavigatorService
from flow3r.core.api.app.settings_service import ISettingsService


class AppContext(IAppContext):
    def __init__(self, navigator_service: INavigatorService, settings_service: ISettingsService):
        self._navigator_service = navigator_service
        self._settings_service = settings_service

    @property
    def navigator_service(self) -> INavigatorService:
        return self._navigator_service

    @property
    def settings_service(self) -> ISettingsService:
        return self._settings_service
