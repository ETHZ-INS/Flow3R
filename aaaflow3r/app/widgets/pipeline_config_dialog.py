from typing import List, Dict, Optional

from PySide6.QtWidgets import QDialog, QComboBox, QVBoxLayout, QWidget, QLineEdit, QDialogButtonBox, QFormLayout, \
    QSizePolicy

from aaaflow3r.core.api.app.app_context import IAppContext
from aaaflow3r.core.pipeline.abc.pipeline_type import IPipelineType
from aaaflow3r.core.pipeline.pipeline_config import PipelineConfig


class PipelineConfigDialog(QDialog):
    def __init__(self, app_context: IAppContext, pipeline_types: List[IPipelineType], config: PipelineConfig = None, parent=None):
        super().__init__(parent)

        self.app_context = app_context
        self.pipeline_types = pipeline_types
        self.config = config

        layout = QVBoxLayout(self)

        self.pipeline_form = QWidget(self)
        pipeline_form_layout = QFormLayout(self.pipeline_form)
        layout.addWidget(self.pipeline_form)

        self.txt_name = QLineEdit(self.config.name)
        pipeline_form_layout.addRow("Name", self.txt_name)
        self.txt_name.editingFinished.connect(self._name_changed)

        self.dpd_pipeline_type = QComboBox(self)
        for pipeline_type in self.pipeline_types:
            self.dpd_pipeline_type.addItem(pipeline_type.name, pipeline_type)

        self.dpd_pipeline_type.setCurrentText(self.config.pipeline_type)
        pipeline_form_layout.addRow("pipeline Type", self.dpd_pipeline_type)
        self.dpd_pipeline_type.currentTextChanged.connect(self._pipeline_type_changed)

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

        self._widget_cache: Dict[str, QWidget] = {}
        self._current_widget: Optional[QWidget] = None

        self.show_pipeline_type_config_widget()

        self.adjustSize()
        self.resize(400, self.height())

    def show_pipeline_type_config_widget(self):
        if self._current_widget:
            self.content_layout.removeWidget(self._current_widget)
            self._current_widget.setParent(None)

        pipeline_type: IPipelineType = self.dpd_pipeline_type.currentData()
        config_factory = pipeline_type.get_config_factory()
        widget_factory = pipeline_type.get_config_widget_factory()

        config = self.config.get_sub_config(pipeline_type.name)
        if not config:
            config = config_factory()
            print("Setting up new config:")
            self.config.set_sub_config(pipeline_type.name, config)

        widget = self._widget_cache.get(pipeline_type.name)
        if not widget:
            widget = widget_factory(self.app_context, config, self)
            self._widget_cache[pipeline_type.name] = widget

        widget.setParent(self.content)

        self._current_widget = widget
        self.content_layout.addWidget(widget)

    def _name_changed(self):
        text = self.txt_name.text()
        self.config.name = text

    def _pipeline_type_changed(self, pipeline_type_name: str):
        self.config.pipeline_type = pipeline_type_name
        self.show_pipeline_type_config_widget()
