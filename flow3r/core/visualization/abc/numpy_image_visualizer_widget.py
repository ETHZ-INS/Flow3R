from abc import abstractmethod
from typing import Generic, Optional, TypeVar

import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QLabel, QWidget

from flow3r.core.visualization.abc.visualizer_widget import BaseVisualizerWidget

TFormat = TypeVar("TFormat")
TItem = TypeVar("TItem")


class BaseNumpyImageVisualizerWidget(
    BaseVisualizerWidget[TFormat, TItem],
    Generic[TFormat, TItem],
):
    """
    Base class for visualizers that render a numpy image.

    Subclasses should:
    - react to handle updates in _on_format/_on_item/etc.
    - keep whatever raw state they need
    - call request_render() when the displayed image should change
    - implement _generate_image()
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._label = QLabel(self)
        self._label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("background: none;")
        self._label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self._label.setMinimumSize(20, 20)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)

        self._render_timer = QtCore.QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(0)
        self._render_timer.timeout.connect(self._render_latest)

        self._pixmap_raw: Optional[QtGui.QPixmap] = None

    def request_render(self) -> None:
        self._schedule_render_if_visible()

    def clear_display(self) -> None:
        self._render_timer.stop()
        self._pixmap_raw = None
        self._label.clear()

    def set_status_text(self, text: str) -> None:
        self._label.setText(text)

    def _reset(self) -> None:
        self._render_timer.stop()
        self._pixmap_raw = None
        self._label.clear()
        self._reset_visualizer_state()

    def _reset_visualizer_state(self) -> None:
        """
        Optional subclass hook called from _reset() after image/display state
        has been cleared.
        """
        return

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        self._schedule_render_if_visible()

    def hideEvent(self, event: QtGui.QHideEvent) -> None:
        self._render_timer.stop()
        super().hideEvent(event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._can_render_now():
            self._on_target_size_changed()
            self._update_scaled_pixmap()

    def event(self, event: QtCore.QEvent) -> bool:
        if event.type() in (
            QtCore.QEvent.Type.Show,
            QtCore.QEvent.Type.Hide,
            QtCore.QEvent.Type.WindowStateChange,
        ):
            if self._can_render_now():
                self._schedule_render_if_visible()
            else:
                self._render_timer.stop()
        return super().event(event)

    def _can_render_now(self) -> bool:
        return self.isVisible()

    def _schedule_render_if_visible(self) -> None:
        if self._can_render_now():
            if not self._render_timer.isActive():
                self._render_timer.start()
        else:
            self._render_timer.stop()

    def _on_target_size_changed(self) -> None:
        """
        Optional subclass hook. Override if resize should cause regeneration
        from raw state instead of only rescaling the last pixmap.
        """
        return

    @QtCore.Slot()
    def _render_latest(self) -> None:
        self._render_timer.stop()

        if not self._can_render_now():
            return

        try:
            frame = self._generate_image()
        except Exception as e:
            self._pixmap_raw = None
            self._label.setText(f"Render error:\n{e}")
            return

        if frame is None:
            return

        try:
            self._pixmap_raw = self._frame_to_pixmap_rgb(frame)
        except Exception as e:
            self._pixmap_raw = None
            self._label.setText(f"Frame conversion error:\n{e}")
            return

        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self) -> None:
        if self._pixmap_raw is None:
            return

        target = self._label.size()
        if target.width() <= 0 or target.height() <= 0:
            return

        scaled = self._pixmap_raw.scaled(
            target,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.FastTransformation,
        )
        self._label.setPixmap(scaled)

    @staticmethod
    def _normalize_frame(frame: np.ndarray) -> np.ndarray:
        frame = np.ascontiguousarray(frame)

        if frame.ndim == 2:
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            return frame

        if frame.ndim == 3 and frame.shape[2] == 3:
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            return frame

        raise ValueError(f"Unsupported frame shape: {frame.shape}")

    @classmethod
    def _frame_to_pixmap_rgb(cls, frame: np.ndarray) -> QtGui.QPixmap:
        frame = cls._normalize_frame(frame)

        if frame.ndim == 2:
            h, w = frame.shape
            qimg = QtGui.QImage(
                frame.data,
                w,
                h,
                w,
                QtGui.QImage.Format.Format_Grayscale8,
            )
            return QtGui.QPixmap.fromImage(qimg.copy())

        h, w, _ = frame.shape
        qimg = QtGui.QImage(
            frame.data,
            w,
            h,
            3 * w,
            QtGui.QImage.Format.Format_RGB888,
        )
        return QtGui.QPixmap.fromImage(qimg.copy())

    @abstractmethod
    def _generate_image(self) -> Optional[np.ndarray]:
        raise NotImplementedError
