from typing import Protocol

from reactivex.disposable import Disposable

from aaaflow3r.core.api.app.widget_service import IWidgetService


class ISessionContext(Protocol):
    @property
    def widget_service(self) -> IWidgetService: ...
    def add_disposable(self, disposable: Disposable): ...