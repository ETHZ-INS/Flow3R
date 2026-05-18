from typing import Protocol

from flow3r.core.api.app.settings_view import ISettingsView
from flow3r.core.api.app.widget_service import IWidgetService


class ISessionContext(Protocol):
    @property
    def widget_service(self) -> IWidgetService: ...
    @property
    def settings(self) -> ISettingsView: ...

