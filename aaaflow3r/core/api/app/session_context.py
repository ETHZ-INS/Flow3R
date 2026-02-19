from typing import Protocol

from aaaflow3r.core.api.app.settings_view import ISettingsView
from aaaflow3r.core.api.app.widget_service import IWidgetService


class ISessionContext(Protocol):
    @property
    def widget_service(self) -> IWidgetService: ...
    @property
    def settings(self) -> ISettingsView: ...
