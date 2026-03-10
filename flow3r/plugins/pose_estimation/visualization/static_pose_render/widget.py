from typing import Optional, Tuple

import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QWidget, QMenu, QFrame
from py3r.media.types import VideoFrame
from py3r.pose.core.types import VideoFramePoses
from py3r.pose.core.visualization.pose_renderer import PoseRenderer

from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.pose_estimation.typing.pose_format import PoseFormat


class SettingsDialog(QtWidgets.QDialog):
    color_mode_changed = QtCore.Signal(str)
    point_size_changed = QtCore.Signal(int)

    def __init__(self, point_size: int, color_mode: str, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pose Visualization Settings")
        self.resize(300, 200)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        frm_settings = QFrame(self)
        frm_settings_layout = QtWidgets.QFormLayout(frm_settings)
        frm_settings_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(frm_settings)

        self.sld_point_size = QtWidgets.QSlider(frm_settings)
        self.sld_point_size.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.sld_point_size.setRange(2, 20)
        self.sld_point_size.setValue(point_size)
        self.sld_point_size.setTickInterval(2)
        self.sld_point_size.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)

        frm_settings_layout.addRow("Point Size", self.sld_point_size)

        self.dpd_color_mode = QtWidgets.QComboBox(frm_settings)
        self.dpd_color_mode.addItems(["Color", "Grayscale", "Auto"])
        self.dpd_color_mode.setCurrentText(color_mode)
        frm_settings_layout.addRow("Color Mode", self.dpd_color_mode)

        self.sld_point_size.valueChanged.connect(self.point_size_changed.emit)
        self.dpd_color_mode.currentTextChanged.connect(self.color_mode_changed.emit)


class StaticPoseWidget(QWidget):
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
        self._handle: Optional[
            IVisualizerHandle[
                Tuple[VideoFormat, PoseFormat],
                Tuple[VideoFrame, VideoFramePoses],
            ]
        ] = None

        self.color_mode = "Auto"

        # latest-only pending data
        self._pending_frame: Optional[Tuple[np.ndarray, VideoFramePoses]] = None

        self._render_timer = QtCore.QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(0)  # render ASAP on event loop
        self._render_timer.timeout.connect(self._render_latest)

        # keep last frame pixmap around so we can rescale on resize
        self._pixmap_raw: Optional[QtGui.QPixmap] = None

    def set_handle(
        self,
        handle: Optional[
            IVisualizerHandle[
                Tuple[VideoFormat, PoseFormat],
                Tuple[VideoFrame, VideoFramePoses],
            ]
        ],
    ) -> None:
        if self._handle is not None:
            try:
                self._handle.desc_changed.disconnect(self._on_desc)
                self._handle.item_changed.disconnect(self._on_frame)
                self._handle.error_changed.disconnect(self._on_error)
                self._handle.completed_changed.disconnect(self._on_completed)
            except (TypeError, RuntimeError):
                pass

        self._handle = handle
        self._render_timer.stop()
        self._pixmap_raw = None
        self._pose_renderer = None
        self._label.clear()

        if self._handle is not None:
            self._handle.desc_changed.connect(self._on_desc)
            self._handle.item_changed.connect(self._on_frame)
            self._handle.error_changed.connect(self._on_error)
            self._handle.completed_changed.connect(self._on_completed)

            self._on_desc(self._handle.desc)
            self._on_frame(self._handle.item)
            self._on_error(self._handle.error)
            self._on_completed()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.set_handle(None)
        super().closeEvent(event)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        self._schedule_render_if_visible()

    def hideEvent(self, event: QtGui.QHideEvent) -> None:
        self._render_timer.stop()
        super().hideEvent(event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        # Only rescale when actually drawable
        if self._can_render_now():
            self._update_scaled_pixmap()

    def event(self, event: QtCore.QEvent) -> bool:
        # Useful for dock/tab visibility changes that may not map cleanly
        # to show/hide in all parent setups.
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

    @QtCore.Slot(object)
    def _on_desc(self, desc: Tuple[VideoFormat, PoseFormat]) -> None:
        self._pose_renderer = PoseRenderer(desc[1].instance_types)

    @QtCore.Slot(object)
    def _on_frame(self, res: Tuple[VideoFrame, VideoFramePoses] = None) -> None:
        # Always keep only the latest frame/poses.
        # If hidden, this is cheap and avoids wasted rendering work.
        self._pending_frame = (res[0].img, res[1]) if res else None
        self._schedule_render_if_visible()

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

        if not self._can_render_now():
            return

        if self._pending_frame is None:
            self._label.setText("Waiting for video...")
            return

        frame, poses = self._pending_frame

        self._pending_frame = None

        if self._pose_renderer is not None and poses is not None:
            try:
                frame = self._convert_color_mode(frame)
                frame = self._pose_renderer.render(frame, poses)
            except Exception as e:
                self._label.setText(f"Pose render error:\n{e}")
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

    def _convert_color_mode(self, frame: np.ndarray) -> np.ndarray:
        if frame.ndim == 2:
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            if self.color_mode == "Color":
                frame = np.stack([frame] * 3, axis=2)
            return frame
        elif frame.ndim == 3 and frame.shape[2] == 3:
            if self.color_mode == "Grayscale":
                frame = np.mean(frame, axis=2)
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            return frame
        else:
            raise ValueError(f"Unsupported frame shape: {frame.shape}")

    def _frame_to_pixmap_rgb(self, frame: np.ndarray) -> QtGui.QPixmap:
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

        if frame.ndim == 3 and frame.shape[2] == 3:
            h, w, _ = frame.shape
            qimg = QtGui.QImage(
                frame.data,
                w,
                h,
                3 * w,
                QtGui.QImage.Format.Format_RGB888,
            )
            return QtGui.QPixmap.fromImage(qimg.copy())

        raise ValueError(f"Unsupported frame shape: {frame.shape}")

    def populate_context_menu(self, menu: QMenu) -> None:
        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self._on_settings_triggered)

    def _on_settings_triggered(self) -> None:
        dialog = SettingsDialog(self._pose_renderer.point_radius, self.color_mode, self)
        dialog.color_mode_changed.connect(self._on_color_mode_changed)
        dialog.point_size_changed.connect(self._on_point_size_changed)
        dialog.exec()

    @QtCore.Slot(str)
    def _on_color_mode_changed(self, color_mode: str) -> None:
        self.color_mode = color_mode

    @QtCore.Slot(int)
    def _on_point_size_changed(self, point_size: int) -> None:
        self._pose_renderer.set_point_radius(point_size)