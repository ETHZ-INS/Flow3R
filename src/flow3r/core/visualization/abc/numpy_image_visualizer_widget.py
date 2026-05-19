from abc import abstractmethod
from typing import Generic, Optional, TypeVar

import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QWidget

from flow3r.core.visualization.abc.visualizer_widget import BaseVisualizerWidget

TFormat = TypeVar("TFormat")
TItem = TypeVar("TItem")


class BaseNumpyImageVisualizerWidget(
    BaseVisualizerWidget[TFormat, TItem],
    Generic[TFormat, TItem],
):
    """
    Optimized base class for visualizers that render a numpy image.

    Main changes vs the old version:
    - paints directly from QImage in paintEvent()
    - avoids QPixmap.fromImage(...) per frame
    - avoids QPixmap.scaled(...) per frame
    - uses a capped repaint timer instead of interval=0
    - keeps only the latest image to display
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        preview_fps: float = 30.0,
    ) -> None:
        super().__init__(parent)

        self.setMinimumSize(20, 20)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        self._status_text: str = ""
        self._latest_qimage: Optional[QtGui.QImage] = None

        # Keep a numpy reference alive for as long as the QImage may wrap it.
        self._backing_array: Optional[np.ndarray] = None

        # Latest raw frame waiting to be converted for painting.
        self._pending_frame: Optional[np.ndarray] = None

        # Fixed-rate repaint timer. This decouples render cadence from frame arrival cadence.
        interval_ms = max(1, int(round(1000.0 / max(0.1, float(preview_fps)))))
        self._render_timer = QtCore.QTimer(self)
        self._render_timer.setInterval(interval_ms)
        self._render_timer.timeout.connect(self._render_latest)

    def request_render(self) -> None:
        self._schedule_render_if_visible()

    def clear_display(self) -> None:
        self._render_timer.stop()
        self._latest_qimage = None
        self._backing_array = None
        self._pending_frame = None
        self._status_text = ""
        self.update()

    def set_status_text(self, text: str) -> None:
        self._status_text = text
        self.update()

    def _reset(self) -> None:
        self._render_timer.stop()
        self._latest_qimage = None
        self._backing_array = None
        self._pending_frame = None
        self._status_text = ""
        self.update()
        self._reset_visualizer_state()

    def _reset_visualizer_state(self) -> None:
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
            self.update()

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
        return

    @QtCore.Slot()
    def _render_latest(self) -> None:
        if not self._can_render_now():
            return

        try:
            frame = self._generate_image()
        except Exception as e:
            self._latest_qimage = None
            self._backing_array = None
            self._pending_frame = None
            self._status_text = f"Render error:\n{e}"
            self.update()
            return

        if frame is not None:
            try:
                qimg, backing = self._frame_to_qimage(frame, pixel_fmt=self._pixel_fmt())
            except Exception as e:
                self._latest_qimage = None
                self._backing_array = None
                self._pending_frame = None
                self._status_text = f"Frame conversion error:\n{e}"
                self.update()
                return

            self._latest_qimage = qimg
            self._backing_array = backing
            self._status_text = ""

        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, False)

        rect = self.rect()
        painter.fillRect(rect, QtCore.Qt.GlobalColor.transparent)

        if self._latest_qimage is None:
            if self._status_text:
                painter.setPen(self.palette().color(QtGui.QPalette.ColorRole.WindowText))
                painter.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter, self._status_text)
            return

        img = self._latest_qimage
        target = self._fit_rect_keep_aspect(rect, img.width(), img.height())
        painter.drawImage(target, img)

        if self._status_text:
            painter.setPen(self.palette().color(QtGui.QPalette.ColorRole.WindowText))
            painter.drawText(
                rect.adjusted(8, 8, -8, -8),
                QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop,
                self._status_text,
            )

    @staticmethod
    def _fit_rect_keep_aspect(
        outer: QtCore.QRect,
        img_w: int,
        img_h: int,
    ) -> QtCore.QRect:
        if img_w <= 0 or img_h <= 0 or outer.width() <= 0 or outer.height() <= 0:
            return QtCore.QRect()

        scale = min(outer.width() / img_w, outer.height() / img_h)
        w = max(1, int(img_w * scale))
        h = max(1, int(img_h * scale))
        x = outer.x() + (outer.width() - w) // 2
        y = outer.y() + (outer.height() - h) // 2
        return QtCore.QRect(x, y, w, h)

    @staticmethod
    def _normalize_frame(frame: np.ndarray) -> np.ndarray:
        frame = np.asarray(frame)

        if frame.ndim == 2:
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8, copy=False)
            return np.ascontiguousarray(frame)

        if frame.ndim == 3 and frame.shape[2] == 3:
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8, copy=False)
            return np.ascontiguousarray(frame)

        raise ValueError(f"Unsupported frame shape: {frame.shape}")

    @classmethod
    def _frame_to_qimage(
        cls,
        frame: np.ndarray,
        pixel_fmt: str = "rgb24",
    ) -> tuple[QtGui.QImage, np.ndarray]:
        """
        Return (QImage, backing_array).

        The QImage wraps backing_array memory directly, so the returned numpy
        array must be kept alive for at least as long as the QImage is used.

        Args:
            pixel_fmt: Pixel format of the frame ('rgb24', 'bgr24', 'mono8').
                For 3-channel frames Qt's Format_BGR888 is used for 'bgr24' and
                Format_RGB888 otherwise — no channel copy is ever performed.
                For 2-channel / grayscale frames the value is ignored and
                Format_Grayscale8 is always used.
        """
        frame = cls._normalize_frame(frame)

        if frame.ndim == 2:
            h, w = frame.shape
            qimg = QtGui.QImage(
                frame.data,
                w,
                h,
                frame.strides[0],
                QtGui.QImage.Format.Format_Grayscale8,
            )
            return qimg, frame

        h, w, _ = frame.shape
        qfmt = QtGui.QImage.Format.Format_BGR888 if pixel_fmt == "bgr24" else QtGui.QImage.Format.Format_RGB888
        qimg = QtGui.QImage(
            frame.data,
            w,
            h,
            frame.strides[0],
            qfmt,
        )
        return qimg, frame

    def _pixel_fmt(self) -> str:
        """Return the pixel format of the current frame (e.g. 'rgb24', 'bgr24', 'mono8').

        Override in subclasses that receive frames with a known pixel format so
        that the correct QImage format is selected without any channel-copy
        overhead.  The default is 'rgb24'.
        """
        return "rgb24"

    @abstractmethod
    def _generate_image(self) -> Optional[np.ndarray]:
        raise NotImplementedError