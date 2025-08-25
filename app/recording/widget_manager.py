from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import QMainWindow, QFrame, QDockWidget

from app.thread_bound_callable import thread_bound


class WidgetManager(QObject):
    def __init__(self, dock_window: QMainWindow, recordings_frame: QFrame):
        super().__init__()
        self.dock_window = dock_window
        self.recordings_frame = recordings_frame

        self.widget_types = {}
        self.widgets = {}

        self.recording_control_widgets = {}

    @thread_bound(timeout_ms=2000)
    def register_widget_type(self, widget_type: str, widget_factory):
        print(f"Registering widget type {widget_type}")
        """Register a new widget type with its factory."""
        if widget_type in self.widget_types:
            raise ValueError(f"Widget type {widget_type} is already registered.")
        self.widget_types[widget_type] = widget_factory

    @thread_bound(timeout_ms=2000)
    def get_widget(self, widget_id: str, widget_config: dict = None):
        """Get a widget by its ID, creating it if it doesn't exist."""
        widget = self.widgets.get(widget_id)
        if widget:
            if widget_config:
                # If a config is provided, update the widget
                factory = self.widget_types.get(widget_config.get("type"))
                if factory:
                    widget = factory.update_widget(widget, widget_config)
                else:
                    raise ValueError(f"Unknown widget type: {widget_config.get('type')}")
            return widget

        if not widget_config:
            raise ValueError(f"Widget {widget_id} does not exist and no config provided to create it.")

        widget_type = widget_config.get("type")
        if not widget_type:
            raise ValueError("Widget config must specify a 'type'.")

        factory = self.widget_types.get(widget_type)
        if not factory:
            raise ValueError(f"Unknown widget type: {widget_type}")

        widget = factory.create_widget(widget_config)
        widget.setObjectName(widget_type + "." + widget_id)

        if isinstance(widget, QDockWidget):
            if not self.dock_window.restoreDockWidget(widget):
                # Fallback if no saved info (first run, renamed, etc.)
                self.dock_window.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, widget)
        else:
            self.recordings_frame.layout().addWidget(widget)

        self.widgets[widget_id] = widget

        return widget

    @thread_bound(timeout_ms=2000)
    def remove_widget(self, widget_id: str):
        if widget_id not in self.widgets:
            print(f"Widget with ID {widget_id} not found.")
            return
        widget = self.widgets.pop(widget_id)
        if isinstance(widget, QDockWidget):
            self.dock_window.removeDockWidget(widget)
        else:
            self.recordings_frame.layout().removeWidget(widget)
        widget.deleteLater()
