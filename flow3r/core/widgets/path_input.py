from typing import Literal

from PySide6.QtCore import QMargins, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QSizePolicy, QToolButton, QLineEdit, QHBoxLayout, QWidget


class PathWidget(QWidget):
    path_changed = Signal(str)

    def __init__(self, mode: Literal["folder", "file"], parent=None):
        super().__init__(parent)
        self.mode = mode

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(QMargins(0, 0, 0, 0))
        self.layout.setSpacing(0)

        self.txt_path = QLineEdit(self)
        self.txt_path.editingFinished.connect(self._path_changed)
        self.layout.addWidget(self.txt_path)

        self.btn_select_folder = QToolButton(self)
        if mode == "folder":
            self.btn_select_folder.setIcon(QIcon.fromTheme("folder"))
        else:
            self.btn_select_folder.setIcon(QIcon.fromTheme("document-open"))
        self.btn_select_folder.clicked.connect(self._select_folder)
        self.layout.addWidget(self.btn_select_folder)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def get_path(self) -> str:
        return self.txt_path.text()

    def set_path(self, path: str):
        self.txt_path.setText(path)

    def _path_changed(self):
        self.path_changed.emit(self.txt_path.text())

    def _select_folder(self):
        if self.mode == "folder":
            path = QFileDialog.getExistingDirectory(self, "Select Folder")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File")

        if path:
            self.txt_path.setText(path)
            self.path_changed.emit(path)
