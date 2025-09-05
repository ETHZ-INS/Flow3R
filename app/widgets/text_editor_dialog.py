from typing import List, Literal

from PySide6.QtCore import QAbstractListModel, Qt
from PySide6.QtWidgets import QDialog

from app.config.variable_config import VariableConfig
from app.layout.text_editor_dialog import Ui_TextEditorDialog
from app.placeholder_context import PlaceholderContext


class VariableModel(QAbstractListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    LabelRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, variables: List[VariableConfig] = None):
        super().__init__()
        self._variables = variables if variables is not None else []

    def set_variables(self, variables: List[VariableConfig]):
        self.beginResetModel()
        self._variables = variables
        self.endResetModel()

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
    def __init__(self, name: str = "Text", text: str = "", mode: Literal["text", "folder", "file"] = "text",
                 placeholders: List[VariableConfig] = None, placeholder_context: PlaceholderContext = None, parent=None):
        super(TextEditorDialog, self).__init__(parent)
        self.setupUi(self)

        self.txt_value.set_allow_editor(False)

        self.variable_model = VariableModel()
        self.lst_variables.setModel(self.variable_model)
        self.lst_variables.setDragEnabled(True)
        self.lst_variables.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.lst_variables.doubleClicked.connect(lambda idx: self.txt_value.insertPlainText("{" + idx.data(VariableModel.NameRole) + "}"))

        self.set_name(name)
        self.setText(text)
        self.set_mode(mode)

        if placeholders:
            self.set_placeholders(placeholders)

        if placeholder_context:
            self.set_placeholder_context(placeholder_context)

    def set_name(self, name: str):
        self.setWindowTitle(f"Edit {name}")
        self.lbl_name.setText(name + ":")

    def text(self):
        return self.txt_value.text()

    def setText(self, text: str):
        self.txt_value.setText(text)

    def set_mode(self, mode: Literal["text", "folder", "file"]):
        self.txt_value.set_mode(mode)

    def set_placeholders(self, placeholders: List[VariableConfig]):
        self.variable_model.set_variables(placeholders)
        self.txt_value.set_placeholders(placeholders)

    def set_placeholder_context(self, placeholder_context: PlaceholderContext):
        self.txt_value.set_placeholder_context(placeholder_context)
