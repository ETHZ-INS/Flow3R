from typing import Protocol, Tuple, Callable, TypeVar

from PySide6.QtWidgets import QWidget

from aaaflow3r.core.api.app.app_context import IAppContext


class ISettingsMenu(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def path(self) -> Tuple[str, ...]: ...
    @property
    def widget_factory(self) -> Callable[[IAppContext, QWidget], QWidget]: ...
