from typing import List, Dict, Optional

from PySide6.QtWidgets import QDialog, QComboBox, QVBoxLayout, QWidget, QLineEdit, QDialogButtonBox, QFormLayout, \
    QLabel, QSizePolicy, QMessageBox

from flow3r.core.source.abc.source_type import ISourceType
from flow3r.core.widgets.config_widget import IConfigWidget
from flow3r.app.config.source_config import SourceConfig


class SourceConfigDialog(QDialog):
    def __init__(self, source_types: List[ISourceType], config: Optional[SourceConfig] = None, parent=None):
        super().__init__(parent)

        if config is None:
            raise ValueError("config must be provided")

        self.source_types = source_types
        self.config = config

        layout = QVBoxLayout(self)

        self.source_form = QWidget(self)
        source_form_layout = QFormLayout(self.source_form)
        layout.addWidget(self.source_form)

        self.txt_name = QLineEdit(self.config.name)
        source_form_layout.addRow("Name", self.txt_name)
        self.txt_name.editingFinished.connect(self._name_changed)

        self.dpd_source_type = QComboBox(self)
        for source_type in self.source_types:
            self.dpd_source_type.addItem(source_type.name, source_type)

        self.dpd_source_type.setCurrentText(self.config.source_type)
        source_form_layout.addRow("Type", self.dpd_source_type)
        self.dpd_source_type.currentTextChanged.connect(self._source_type_changed)

        self.lbl_source_config_title = QLabel("Source configuration")
        layout.addWidget(self.lbl_source_config_title)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content)

        self.bottom_spacer = QWidget(self)
        layout.addWidget(self.bottom_spacer)
        self.bottom_spacer.setContentsMargins(0, 0, 0, 0)
        self.bottom_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self._widget_cache: Dict[str, IConfigWidget] = {}
        self._current_source_type: Optional[ISourceType] = None
        self._current_widget: Optional[IConfigWidget] = None

        self.show_source_type_config_widget()

        self.adjustSize()
        self.resize(400, self.height())

    def accept(self):
        try:
            self._commit_current_widget()
        except Exception as e:
            QMessageBox.critical(self, "Invalid configuration", str(e))
            return
        super().accept()

    def _commit_current_widget(self):
        """Commit the current widget's config back into the source config. Raises on error."""
        if self._current_widget and self._current_source_type:
            new_config = self._current_widget.get_config()
            self.config.set_sub_config(self._current_source_type.name, new_config)

    def show_source_type_config_widget(self):
        # Commit the departing widget before switching so its result is not lost
        # even if get_config() returns a new object rather than mutating in place.
        try:
            self._commit_current_widget()
        except Exception:
            pass  # Best-effort; don't block the user from switching types

        if self._current_widget:
            self.content_layout.removeWidget(self._current_widget)
            self._current_widget.setParent(None)

        source_type: ISourceType = self.dpd_source_type.currentData()
        config_factory = source_type.config_factory
        widget_factory = source_type.config_widget_factory

        config = self.config.get_sub_config(source_type.name)
        if not config:
            config = config_factory()
            self.config.set_sub_config(source_type.name, config)

        widget = self._widget_cache.get(source_type.name)
        if not widget:
            widget = widget_factory(config, self)
            self._widget_cache[source_type.name] = widget

        widget.setParent(self.content)

        self._current_source_type = source_type
        self._current_widget = widget
        self.content_layout.addWidget(widget)

    def _name_changed(self):
        text = self.txt_name.text()
        self.config.name = text

    def _source_type_changed(self, source_type_name: str):
        self.config.source_type = source_type_name
        self.show_source_type_config_widget()
