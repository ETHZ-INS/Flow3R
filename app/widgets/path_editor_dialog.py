from typing import List

from PySide6.QtCore import QAbstractListModel, Qt
from PySide6.QtWidgets import QDialog, QFileDialog

from app.layout.path_editor_dialog import Ui_PathEditorDialog


class VariableModel(QAbstractListModel):
    def __init__(self, variables: List[str]):
        super().__init__()
        self._variables = variables

    def rowCount(self, parent=None):
        return len(self._variables)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self._variables[index.row()]
        return None

    def mimeData(self, indexes):
        mime_data = super().mimeData(indexes)
        if indexes:
            mime_data.setText("{" + self._variables[indexes[0].row()] + "}")
        return mime_data

    def mimeTypes(self):
        return ["text/plain"]

    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled

    def supportedDropActions(self):
        return Qt.DropAction.CopyAction


class PathEditorDialog(Ui_PathEditorDialog, QDialog):
    def __init__(self, directory: bool = False, parent=None):
        super(PathEditorDialog, self).__init__(parent)
        self.setupUi(self)

        self.directory = directory

        self.lst_variables.setModel(VariableModel(["test", "my_variable"]))
        self.lst_variables.setDragEnabled(True)
        self.lst_variables.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.txt_path.setAcceptDrops(True)

        self.btn_select_path.clicked.connect(self.select_path)
        self.lst_variables.doubleClicked.connect(lambda idx: self.txt_path.insert("{" + idx.data() + "}"))

    def select_path(self):
        #if self.directory:
        #    path = QFileDialog.getExistingDirectory(self, "Select Directory", "")
        #else:
        #    path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")

        dialog = QFileDialog(self)
        dialog.setProxyModel(None)
        if dialog.exec_():
            path = dialog.selectedFiles()[0]
        else:
            path = None

        if path:
            self.txt_path.setText(path)
