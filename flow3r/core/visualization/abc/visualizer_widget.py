from abc import ABC
from typing import Generic, Optional, TypeVar

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QWidget, QMenu

from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle

TFormat = TypeVar("TFormat")
TItem = TypeVar("TItem")


class QGenericABCMeta(type(QWidget), type(ABC)):
    pass


class BaseVisualizerWidget(QWidget, Generic[TFormat, TItem], ABC, metaclass=QGenericABCMeta):
    """
    Base widget that manages connecting/disconnecting a visualizer handle and
    dispatches handle updates into overridable hook methods.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._handle: Optional[IVisualizerHandle[TFormat, TItem]] = None

    def set_handle(self, handle: Optional[IVisualizerHandle[TFormat, TItem]]) -> None:
        if self._handle is handle:
            return

        self._disconnect_handle_signals()

        self._handle = handle
        self._reset()

        if self._handle is not None:
            self._connect_handle_signals()

            self._on_format(self._handle.format)
            self._on_item(self._handle.item)
            self._on_error(self._handle.error)
            self._on_completed()

    def handle(self) -> Optional[IVisualizerHandle[TFormat, TItem]]:
        return self._handle

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.set_handle(None)
        super().closeEvent(event)

    def populate_context_menu(self, menu: QMenu) -> None:
        return

    def _connect_handle_signals(self) -> None:
        if self._handle is None:
            return

        self._handle.format_changed.connect(self._dispatch_format)
        self._handle.item_changed.connect(self._dispatch_item)
        self._handle.error_changed.connect(self._dispatch_error)
        self._handle.completed_changed.connect(self._dispatch_completed)

    def _disconnect_handle_signals(self) -> None:
        if self._handle is None:
            return

        try:
            self._handle.format_changed.disconnect(self._dispatch_format)
            self._handle.item_changed.disconnect(self._dispatch_item)
            self._handle.error_changed.disconnect(self._dispatch_error)
            self._handle.completed_changed.disconnect(self._dispatch_completed)
        except (TypeError, RuntimeError):
            pass

    @QtCore.Slot(object)
    def _dispatch_format(self, fmt: Optional[TFormat]) -> None:
        self._on_format(fmt)

    @QtCore.Slot(object)
    def _dispatch_item(self, item: Optional[TItem]) -> None:
        self._on_item(item)

    @QtCore.Slot(object)
    def _dispatch_error(self, err: Optional[Exception]) -> None:
        self._on_error(err)

    @QtCore.Slot()
    def _dispatch_completed(self) -> None:
        self._on_completed()

    #
    # Overridable hooks
    #

    def _reset(self) -> None:
        """
        Called whenever the handle changes, before new signals are connected.
        Subclasses should clear internal state here.
        """
        return

    def _on_format(self, fmt: Optional[TFormat]) -> None:
        return

    def _on_item(self, item: Optional[TItem]) -> None:
        return

    def _on_error(self, err: Optional[Exception]) -> None:
        return

    def _on_completed(self) -> None:
        return
