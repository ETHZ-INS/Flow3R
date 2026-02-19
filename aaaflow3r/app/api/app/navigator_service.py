from typing import Tuple, Optional, Dict

from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import QWidget

from aaaflow3r.app.widgets.settings_menu_dialog import SettingsMenuDialog
from aaaflow3r.core.api.app.app_context import IAppContext
from aaaflow3r.core.settings.abc.settings_menu import ISettingsMenu


class NavigatorService(QObject):
    """
    Opens a settings dialog with tree navigation on the left and page on the right.
    Plugins can open a page by path: navigator.open(("Pose Estimation", "Models"), modal=True)
    """
    def __init__(self, settings_menus: Dict[Tuple[str, ...], ISettingsMenu]) -> None:
        super().__init__()
        self._settings_menus = settings_menus
        self.__app_context: IAppContext | None = None

    @property
    def _app_context(self) -> IAppContext:
        assert self.__app_context is not None
        return self.__app_context

    def set_app_context(self, app_context: IAppContext):
        self.__app_context = app_context

    def open(self, path: Tuple[str, ...], parent: Optional[QWidget] = None, modal: bool = True) -> None:
        settings_menu = self._settings_menus[path]

        dialog = SettingsMenuDialog(self._app_context, settings_menu.widget_factory, parent=parent)
        dialog.setWindowTitle(settings_menu.path[-1])

        if modal:
            dialog.exec()
        else:
            dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
            dialog.show()
