from aaaflow3r.app.widget_service import WidgetService
from flow3r.core.app.app_context import IAppContext


class AppContext(IAppContext):
    def __init__(self, widget_service: WidgetService):
        self._widget_service = widget_service

    @property
    def widget_service(self) -> WidgetService:
        return self._widget_service
