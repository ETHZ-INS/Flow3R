from typing import Protocol

from aaaflow3r.core.api.app.widget_service import IWidgetService


class IAppContext(Protocol):
    @property
    def widget_service(self) -> IWidgetService: ...
