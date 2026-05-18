from typing import Optional, Tuple

import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QWidget, QMenu, QFrame
from py3r.media.types import VideoFrame
from py3r.pose.core.visualization.pose_renderer import PoseRenderer

from flow3r.core.visualization.abc.numpy_image_visualizer_widget import BaseNumpyImageVisualizerWidget
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.pose_estimation.typing.pose_format import PoseFormat


class SettingsDialog(QtWidgets.QDialog):
    color_mode_changed = QtCore.Signal(str)

    def __init__(self, color_mode: str, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pose Visualization Settings")
        self.resize(300, 200)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        frm_settings = QFrame(self)
        frm_settings_layout = QtWidgets.QFormLayout(frm_settings)
        frm_settings_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(frm_settings)

        self.dpd_color_mode = QtWidgets.QComboBox(frm_settings)
        self.dpd_color_mode.addItems(["Auto", "Grayscale"])
        self.dpd_color_mode.setCurrentText(color_mode)
        frm_settings_layout.addRow("Color Mode", self.dpd_color_mode)

        self.dpd_color_mode.currentTextChanged.connect(self.color_mode_changed.emit)


class VideoWidget(BaseNumpyImageVisualizerWidget[VideoFormat, VideoFrame]):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._pose_renderer: Optional[PoseRenderer] = None
        self._latest_item: Optional[VideoFrame] = None
        self._color_mode = "Auto"
        self._video_fmt: Optional[VideoFormat] = None

    def _reset_visualizer_state(self) -> None:
        self._latest_item = None
        self._color_mode = "Auto"
        self._video_fmt = None

    def _on_format(self, fmt: Optional[VideoFormat]) -> None:
        self._video_fmt = fmt
        self.request_render()

    def _pixel_fmt(self) -> str:
        return "mono8" if self._color_mode == "Grayscale" else self._video_fmt.fmt if self._video_fmt is not None else "bgr24"

    def _on_item(self, item: Optional[VideoFrame]) -> None:
        self._latest_item = item
        self.request_render()

    def _on_error(self, err: Optional[Exception]) -> None:
        if err:
            self.set_status_text(str(err))
        else:
            self.set_status_text("")

    def _on_completed(self) -> None:
        if self.handle() is not None and self.handle().completed:
            self.set_status_text("Video completed.")

    def _generate_image(self) -> Optional[np.ndarray]:
        if self._latest_item is None:
            self.set_status_text("Waiting for video...")
            return None

        frame = self._latest_item
        img = self._convert_color_mode(frame.img)

        return img

    def _convert_color_mode(self, frame: np.ndarray) -> np.ndarray:
        if frame.ndim == 2:
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            return frame

        if frame.ndim == 3 and frame.shape[2] == 3:
            if self._color_mode == "Grayscale":
                frame = np.mean(frame, axis=2)
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            return frame

        raise ValueError(f"Unsupported frame shape: {frame.shape}")

    def populate_context_menu(self, menu: QMenu) -> None:
        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self._on_settings_triggered)

    def _on_settings_triggered(self) -> None:
        if self._pose_renderer is None:
            return

        dialog = SettingsDialog(self._color_mode, self)
        dialog.exec()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.set_handle(None)
        super().closeEvent(event)
