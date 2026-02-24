from copy import deepcopy

from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListView, QHBoxLayout, QPushButton, QDialog, QFormLayout, \
    QLineEdit, QDialogButtonBox, QSizePolicy

from flow3r.core.api.app.app_context import IAppContext
from flow3r.plugins.pose_estimation.settings.pose_estimation_models.settings import PoseEstimationModelsSettings, \
    PoseEstimationModelConfig


class PoseEstimationModelEditDialog(QDialog):
    def __init__(self, config: PoseEstimationModelConfig, parent=None):
        super().__init__(parent)

        self.config = config

        layout = QVBoxLayout(self)

        self.form = QWidget(self)
        source_form_layout = QFormLayout(self.form)
        source_form_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.form)

        self.txt_name = QLineEdit(self.config.name)
        source_form_layout.addRow("Name", self.txt_name)
        self.txt_name.editingFinished.connect(self._name_changed)

        self.txt_model_folder = QLineEdit(self.config.model_identifier)
        source_form_layout.addRow("Model Folder", self.txt_model_folder)
        self.txt_model_folder.editingFinished.connect(self._model_folder_changed)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.adjustSize()
        self.resize(400, self.height())

    def _name_changed(self):
        self.config.name = self.txt_name.text()

    def _model_folder_changed(self):
        self.config.model_identifier = self.txt_model_folder.text()


class PoseEstimationModelsModel(QAbstractListModel):
    ConfigRole = Qt.ItemDataRole(Qt.ItemDataRole.UserRole + 1)

    def __init__(self, settings: PoseEstimationModelsSettings):
        super().__init__()
        self.settings = settings

    def rowCount(self, parent=None):
        return len(self.settings.models)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self.settings.models):
            return None

        config = list(self.settings.models.values())[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return config.name
        elif role == self.ConfigRole:
            return config
        return None

    def add_model(self, config: PoseEstimationModelConfig):
        self.beginInsertRows(QModelIndex(), len(self.settings.models), len(self.settings.models))
        self.settings.models[config.id] = config
        self.endInsertRows()

    def set_model(self, model_id: str, config: PoseEstimationModelConfig):
        index = list(self.settings.models.keys()).index(model_id)
        self.settings.models[model_id] = config
        self.dataChanged.emit(self.index(index), self.index(index))

    def remove_model(self, model_id: str):
        index = list(self.settings.models.keys()).index(model_id)
        self.beginRemoveRows(QModelIndex(), index, index)
        self.settings.models.pop(model_id)
        self.endRemoveRows()


class PoseEstimationModelsSettingsWidget(QWidget):
    def __init__(self, app_context: IAppContext, parent=None):
        super().__init__(parent)

        self.app_context = app_context

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        pose_estimation_models_settings = self.app_context.settings_service.get(("pose_estimation", "models"), PoseEstimationModelsSettings())

        self.model = PoseEstimationModelsModel(pose_estimation_models_settings)

        self.lst_models = QListView(self)
        self.lst_models.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.lst_models.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.lst_models.setModel(self.model)
        layout.addWidget(self.lst_models)

        self.frm_buttons = QWidget(self)
        self.frm_buttons.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        frm_buttons_layout = QHBoxLayout(self.frm_buttons)
        frm_buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_add = QPushButton("Add")
        frm_buttons_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton("Edit")
        frm_buttons_layout.addWidget(self.btn_edit)

        self.btn_remove = QPushButton("Remove")
        frm_buttons_layout.addWidget(self.btn_remove)

        layout.addWidget(self.frm_buttons)

        self.btn_add.clicked.connect(self._add_model)
        self.btn_edit.clicked.connect(self._edit_model)
        self.btn_remove.clicked.connect(self._remove_model)

        self.lst_models.doubleClicked.connect(self._edit_model)

    def _add_model(self):
        config = PoseEstimationModelConfig()
        dialog = PoseEstimationModelEditDialog(config)
        res = dialog.exec()
        if res == QDialog.DialogCode.Accepted:
            self.model.add_model(dialog.config)
            self.app_context.settings_service.set(("pose_estimation", "models"), self.model.settings)

    def _edit_model(self):
        index = self.lst_models.currentIndex()
        if not index.isValid():
            return

        config = deepcopy(index.data(self.model.ConfigRole))
        dialog = PoseEstimationModelEditDialog(config)
        res = dialog.exec()
        if res == QDialog.DialogCode.Accepted:
            self.model.set_model(config.id, dialog.config)
            self.app_context.settings_service.set(("pose_estimation", "models"), self.model.settings)

    def _remove_model(self):
        index = self.lst_models.currentIndex()
        if not index.isValid():
            return
        config = index.data(self.model.ConfigRole)
        self.model.remove_model(config.id)
        self.app_context.settings_service.set(("pose_estimation", "models"), self.model.settings)
