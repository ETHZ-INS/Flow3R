from aaaflow3r.core.api.app.session_context import ISessionContext
from aaaflow3r.core.api.app.settings_view import ISettingsView
from aaaflow3r.core.api.app.widget_service import IWidgetService


class SessionContext(ISessionContext):
    def __init__(self, widget_service: IWidgetService, settings: ISettingsView):
        self._widget_service = widget_service
        self._settings = settings

    @property
    def widget_service(self) -> IWidgetService:
        return self._widget_service

    @property
    def settings(self) -> ISettingsView:
        return self._settings
