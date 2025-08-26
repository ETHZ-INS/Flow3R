from typing import List, Literal

from PySide6.QtCore import QAbstractListModel, Qt
from PySide6.QtWidgets import QDialog, QFileDialog

from app.config.variable_config import VariableConfig
from app.controller import Controller
from app.layout.text_editor_dialog import Ui_TextEditorDialog


class VariableModel(QAbstractListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    LabelRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, variables: List[VariableConfig]):
        super().__init__()
        self._variables = variables

    def rowCount(self, parent=None):
        return len(self._variables)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self._variables[index.row()].variable_label
        elif role == self.NameRole:
            return self._variables[index.row()].variable_name
        elif role == self.LabelRole:
            return self._variables[index.row()].variable_label
        return None

    def mimeData(self, indexes):
        mime_data = super().mimeData(indexes)
        if indexes:
            mime_data.setText("{" + self._variables[indexes[0].row()].variable_name + "}")
        return mime_data

    def mimeTypes(self):
        return ["text/plain"]

    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled

    def supportedDropActions(self):
        return Qt.DropAction.CopyAction


class TextEditorDialog(Ui_TextEditorDialog, QDialog):
    def __init__(self, controller: Controller, name: str = "Text", value: str = "", value_type: Literal["text", "directory", "file"] = "text", parent=None):
        super(TextEditorDialog, self).__init__(parent)
        self.setupUi(self)

        self.setWindowTitle(f"Edit {name}")
        self.lbl_name.setText(name + ":")

        self.controller = controller

        self.directory = value_type == "directory"
        self.variables = list(self.controller.config.variable_config_list.variables.values())

        self.lst_variables.setModel(VariableModel(self.variables))
        self.lst_variables.setDragEnabled(True)
        self.lst_variables.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.txt_value.setAcceptDrops(True)
        self.txt_value.setText(value)

        self.btn_select_path.setVisible(value_type == "directory" or value_type == "file")

        self.btn_select_path.clicked.connect(self.select_path)
        self.lst_variables.doubleClicked.connect(lambda idx: self.txt_value.insert("{" + idx.data() + "}"))

    def select_path(self):
        if self.directory:
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", filter="All Files (*)")

        self.txt_value.setText(path)