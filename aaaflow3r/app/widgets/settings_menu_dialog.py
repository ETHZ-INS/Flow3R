from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget, QDialogButtonBox, QSizePolicy

from aaaflow3r.core.api.app.app_context import IAppContext


class SettingsMenuDialog(QDialog):
    def __init__(self, app_context: IAppContext, settings_widget_factory, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.content = settings_widget_factory(app_context, self)
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

        self.adjustSize()
        self.resize(400, self.height())
