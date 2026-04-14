from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy


class ClickableHeader(QWidget):
    clicked = Signal()

    def __init__(self, title="", parent=None):
        super().__init__(parent)

        self.indicator = QLabel("+")
        self.indicator.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.indicator.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.indicator.setStyleSheet("font-weight: bold; font-size: 16px;")

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.title_label.setStyleSheet("font-weight: bold;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.indicator)
        layout.addWidget(self.title_label)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def setExpanded(self, expanded: bool):
        self.indicator.setText("−" if expanded else "+")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class CollapsibleSection(QWidget):
    def __init__(self, title="", parent=None, animation_duration=180):
        super().__init__(parent)

        self._expanded = False
        self._content_widget = None

        self.header = ClickableHeader(title)
        self.header.clicked.connect(self.toggle)

        self.content_area = QWidget()
        self.content_area.setVisible(False)
        self.content_area.setMaximumHeight(0)
        self.content_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._inner_layout = QVBoxLayout(self.content_area)
        self._inner_layout.setContentsMargins(4, 4, 0, 4)
        self._inner_layout.setSpacing(0)

        self.animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.animation.setDuration(animation_duration)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.content_area)

    def setWidget(self, widget: QWidget):
        if self._content_widget is not None:
            self._inner_layout.removeWidget(self._content_widget)
            self._content_widget.setParent(None)
        self._content_widget = widget
        self._inner_layout.addWidget(widget)

    def widget(self) -> QWidget | None:
        return self._content_widget

    def toggle(self):
        self.setExpanded(not self._expanded)

    def setExpanded(self, expanded: bool):
        if self._expanded == expanded:
            return

        self._expanded = expanded
        self.header.setExpanded(expanded)

        content_height = self._inner_layout.sizeHint().height()

        self.animation.stop()
        if expanded:
            self.content_area.setVisible(True)
            self.animation.setStartValue(self.content_area.maximumHeight())
            self.animation.setEndValue(content_height)
        else:
            self.animation.setStartValue(self.content_area.maximumHeight())
            self.animation.setEndValue(0)
            self.animation.finished.connect(self._hide_if_collapsed_once)

        self.animation.start()

    def _hide_if_collapsed_once(self):
        try:
            self.animation.finished.disconnect(self._hide_if_collapsed_once)
        except RuntimeError:
            pass

        if not self._expanded:
            self.content_area.setVisible(False)
