from typing import List, Literal

from PySide6.QtWidgets import QFrame, QFileDialog

from app.config.variable_config import VariableConfig
from app.config.welfare_recorder_config import WelfareRecorderConfig, CameraConfigView
from app.layout.variable_text_widget import Ui_VariableTextWidget
from app.placeholder_context import PlaceholderContext
from app.placeholder_formatter import PlaceholderFormatter
from app.widgets.placeholder_line_edit import PlaceholderHighlighter


class VariableTextWidget(Ui_VariableTextWidget, QFrame):
    def __init__(self, parent=None, text: str = "", mode: Literal["text", "file", "folder"] = "text", allow_editor: bool = True, show_preview: bool = True):
        super().__init__(parent)
        self.setupUi(self)

        self.mode = mode
        self.show_preview = show_preview

        self.textChanged = self.txt_value.textChanged

        self.placeholders = []
        self.placeholder_context = None

        self.variable_highlighter = PlaceholderHighlighter(self.txt_value.document(), [])

        self.txt_value.setText(text)

        self.txt_value.textChanged.connect(self._value_changed)
        self.btn_select_file.clicked.connect(self.select_file)
        self.btn_editor.clicked.connect(self.open_editor)

        self.set_mode(self.mode)
        self.set_allow_editor(allow_editor)
        self.set_show_preview(show_preview)

    def update_lbl_preview(self):
        if not self.show_preview or not self.placeholder_context:
            self.lbl_preview.setVisible(False)
            return

        value = self.txt_value.toPlainText()
        dependencies = PlaceholderFormatter(value).get_placeholders()
        if not dependencies:
            self.lbl_preview.setVisible(False)
            return

        self.lbl_preview.setVisible(True)
        preview_text = self.placeholder_context.format(value)
        self.lbl_preview.setText("Preview: " + preview_text)

    def text(self) -> str:
        return self.txt_value.toPlainText()

    def setText(self, text: str):
        self.txt_value.setPlainText(text)
        self.update_lbl_preview()

    def insertPlainText(self, text: str):
        self.txt_value.insertPlainText(text)

    def set_mode(self, mode: Literal["text", "file", "folder"]):
        self.mode = mode
        self.btn_select_file.setVisible(mode in ["file", "folder"])

    def set_allow_editor(self, allow: bool):
        self.btn_editor.setVisible(allow)

    def set_show_preview(self, show: bool):
        self.show_preview = show
        self.lbl_preview.setVisible(show)

    def set_placeholders(self, placeholders: List[VariableConfig]):
        self.placeholders = placeholders
        self.variable_highlighter.setAllowed([v.variable_name for v in placeholders])

    def set_placeholder_context(self, context: PlaceholderContext):
        self.placeholder_context = context
        self.update_lbl_preview()

    def set_config_view(self, config: CameraConfigView):
        print(config.placeholders)
        self.set_placeholders(config.placeholders)
        self.set_placeholder_context(config.preview_placeholder_context)

    def select_file(self):
        if self.mode == "folder":
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", filter="All Files (*)")

        if path:
            self.setText(path)

    def open_editor(self):
        from app.widgets.text_editor_dialog import TextEditorDialog
        dialog = TextEditorDialog("Video File", self.txt_value.text(), mode=self.mode, placeholders=self.placeholders, placeholder_context=self.placeholder_context, parent=self)
        if dialog.exec():
            self.txt_value.setText(dialog.text())

    def _value_changed(self):
        self.update_lbl_preview()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    widget = VariableTextWidget()
    widget.show()

    sys.exit(app.exec())