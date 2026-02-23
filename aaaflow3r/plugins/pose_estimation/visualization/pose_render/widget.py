from typing import Optional, Tuple

import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QWidget
from py3r.media.types import VideoFrame
from py3r.pose.core.types import VideoFramePoses, PoseInstanceType
from py3r.pose.core.visualization.pose_renderer import PoseRenderer

from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from aaaflow3r.plugins.core.typing.video import VideoFormat
from aaaflow3r.plugins.pose_estimation.typing.pose_format import PoseFormat


class PoseWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._label = QtWidgets.QLabel(self)
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

        self._pose_renderer: Optional[PoseRenderer] = None

        self._handle: Optional[IVisualizerHandle[Tuple[VideoFormat, PoseFormat], Tuple[VideoFrame, VideoFramePoses]]] = None

        # latest-only buffer
        self._pending: Optional[np.ndarray] = None
        self._render_timer = QtCore.QTimer(self)
        self._render_timer.setInterval(0)  # render ASAP on event loop
        self._render_timer.timeout.connect(self._render_latest)

        # keep last frame pixmap around so we can rescale on resize
        self._pixmap_raw: Optional[QtGui.QPixmap] = None

    def set_handle(self, handle: Optional[IVisualizerHandle[Tuple[VideoFormat, PoseFormat], Tuple[VideoFrame, VideoFramePoses]]]) -> None:
        # disconnect old
        if self._handle is not None:
            try:
                self._handle.desc_changed.disconnect(self._on_desc)
                self._handle.item_changed.disconnect(self._on_frame)
                self._handle.error_changed.disconnect(self._on_error)
                self._handle.completed_changed.disconnect(self._on_completed)
            except (TypeError, RuntimeError):
                pass

        self._handle = handle
        self._pending = None
        self._render_timer.stop()
        self._pixmap_raw = None
        self._label.clear()

        if self._handle is not None:
            print(type(self._handle))
            self._handle.desc_changed.connect(self._on_desc)
            self._handle.item_changed.connect(self._on_frame)
            self._handle.error_changed.connect(self._on_error)
            self._handle.completed_changed.connect(self._on_completed)

            if self._handle.desc:
                self._on_desc(self._handle.desc)
            if self._handle.item:
                self._on_frame(self._handle.item)
            if self._handle.error:
                self._on_error(self._handle.error)
            if self._handle.completed:
                self._on_completed()

    def closeEvent(self, event) -> None:
        self.set_handle(None)
        super().closeEvent(event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        # Recompute scaled pixmap for the new size
        self._update_scaled_pixmap()

    @QtCore.Slot(object)
    def _on_desc(self, desc: Tuple[VideoFormat, PoseFormat]):
        print(desc[1].instance_types)
        self._pose_renderer = PoseRenderer(desc[1].instance_types)

    @QtCore.Slot(object)
    def _on_frame(self, res: Tuple[VideoFrame, VideoFramePoses]) -> None:
        self._pending_frame = res[0].img
        self._pending_poses = res[1]
        if not self._render_timer.isActive():
            self._render_timer.start()

    @QtCore.Slot(object)
    def _on_error(self, err: Optional[Exception]) -> None:
        if err:
            self._label.setText(str(err))
        else:
            self._label.setText("")

    @QtCore.Slot()
    def _on_completed(self) -> None:
        self._label.setText("Video completed.")

    @QtCore.Slot()
    def _render_latest(self) -> None:
        self._render_timer.stop()
        frame = self._pending_frame
        self._pending_frame = None

        if frame is None:
            return

        if self._pose_renderer:
            frame = self._pose_renderer.render(frame, self._pending_poses)

        try:
            self._pixmap_raw = self._frame_to_pixmap_rgb(frame)
        except Exception as e:
            self._pixmap_raw = None
            self._label.setText(f"Frame conversion error:\n{e}")
            return

        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self) -> None:
        """Scale the last received frame pixmap to the current label size."""
        if self._pixmap_raw is None:
            return

        target = self._label.size()
        if target.width() <= 0 or target.height() <= 0:
            return

        scaled = self._pixmap_raw.scaled(
            target,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.FastTransformation
        )
        self._label.setPixmap(scaled)

    @staticmethod
    def _frame_to_pixmap_rgb(frame: np.ndarray) -> QtGui.QPixmap:
        if frame.ndim == 2:
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            h, w = frame.shape
            qimg = QtGui.QImage(frame.data, w, h, w, QtGui.QImage.Format.Format_Grayscale8)
            return QtGui.QPixmap.fromImage(qimg.copy())

        if frame.ndim == 3 and frame.shape[2] == 3:
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            h, w, _ = frame.shape
            qimg = QtGui.QImage(frame.data, w, h, 3 * w, QtGui.QImage.Format.Format_RGB888)
            return QtGui.QPixmap.fromImage(qimg.copy())

        raise ValueError(f"Unsupported frame shape: {frame.shape}")
