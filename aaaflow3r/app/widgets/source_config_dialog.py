from typing import List, Dict, Optional

from PySide6.QtWidgets import QDialog, QComboBox, QVBoxLayout, QWidget, QLineEdit, QDialogButtonBox, QFormLayout

from aaaflow3r.core.source.abc.source_type import ISourceType
from aaaflow3r.core.source.source_config import SourceConfig


class SourceConfigDialog(QDialog):
    def __init__(self, source_types: List[ISourceType], config: SourceConfig = None, parent=None):
        super().__init__(parent)

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
        source_form_layout.addRow("Source Type", self.dpd_source_type)
        self.dpd_source_type.currentTextChanged.connect(self._source_type_changed)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self._widget_cache: Dict[str, QWidget] = {}
        self._current_widget: Optional[QWidget] = None

        self.show_source_type_config_widget()

    def show_source_type_config_widget(self):
        if self._current_widget:
            self.content_layout.removeWidget(self._current_widget)
            self._current_widget.setParent(None)

        source_type: ISourceType = self.dpd_source_type.currentData()
        config_factory = source_type.get_config_factory()
        widget_factory = source_type.get_config_widget_factory()

        config = self.config.get_sub_config(source_type.name)
        if not config:
            config = config_factory()
            self.config.set_sub_config(source_type.name, config)

        widget = self._widget_cache.get(source_type.name)
        if not widget:
            widget = widget_factory(config, self)
            self._widget_cache[source_type.name] = widget

        widget.setParent(self.content)

        self._current_widget = widget
        self.content_layout.addWidget(widget)

    def _name_changed(self):
        text = self.txt_name.text()
        self.config.name = text

    def _source_type_changed(self, source_type_name: str):
        self.config.source_type = source_type_name
        self.show_source_type_config_widget()
