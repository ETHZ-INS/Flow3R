from aaaflow3r.core.api.app.widget_service import IWidgetService
from flow3r.core.app.app_context import IAppContext


class AppContext(IAppContext):
    def __init__(self, widget_service: IWidgetService):
        self._widget_service = widget_service

    @property
    def widget_service(self) -> IWidgetService:
        return self._widget_service
