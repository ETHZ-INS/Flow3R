from typing import Optional, Tuple

import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QWidget
from py3r.media.types import VideoFrame
from py3r.pose.core.types import VideoFramePoses

from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.pose_estimation.typing.pose_format import PoseFormat


class PoseMagnifierWidget(QWidget):
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
        self._label.setScaledContents(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)

        self._handle: Optional[
            IVisualizerHandle[
                Tuple[VideoFormat, PoseFormat],
                Tuple[VideoFrame, VideoFramePoses],
            ]
        ] = None

        # latest-only pending item
        self._pending_frame: Optional[Tuple[np.ndarray, VideoFramePoses]] = None

        self._render_timer = QtCore.QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(0)
        self._render_timer.timeout.connect(self._render_latest)

        # store latest full-resolution data so crop can be recomputed on resize
        self._frame_raw: Optional[np.ndarray] = None
        self._box_raw: Optional[Tuple[float, float, float, float]] = None

        # last cropped pixmap, for final rescaling into label
        self._pixmap_raw: Optional[QtGui.QPixmap] = None

        self._instance_id: str = "mouse_top_0"
        self._box_padding: int = 20

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
                self._handle.format_changed.disconnect(self._on_desc)
                self._handle.item_changed.disconnect(self._on_frame)
                self._handle.error_changed.disconnect(self._on_error)
                self._handle.completed_changed.disconnect(self._on_completed)
            except (TypeError, RuntimeError):
                pass

        self._handle = handle
        self._pending_frame = None
        self._frame_raw = None
        self._box_raw = None
        self._pixmap_raw = None
        self._render_timer.stop()
        self._label.clear()

        if self._handle is not None:
            self._handle.format_changed.connect(self._on_desc)
            self._handle.item_changed.connect(self._on_frame)
            self._handle.error_changed.connect(self._on_error)
            self._handle.completed_changed.connect(self._on_completed)

            self._on_desc(self._handle.format)
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
        if self._can_render_now():
            # recompute crop from full frame + box for new aspect ratio
            self._rebuild_pixmap_from_raw()
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

    @QtCore.Slot(object)
    def _on_desc(self, desc: Tuple[VideoFormat, PoseFormat]) -> None:
        # not needed here currently, but kept for symmetry
        pass

    @QtCore.Slot(object)
    def _on_frame(self, res: Tuple[VideoFrame, VideoFramePoses] = None) -> None:
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
            if self._frame_raw is None:
                self._label.setText("Waiting for video...")
            return

        frame, poses = self._pending_frame
        self._pending_frame = None

        self._frame_raw = frame
        self._box_raw = self._extract_instance_box(poses)

        self._rebuild_pixmap_from_raw()
        self._update_scaled_pixmap()

    def _extract_instance_box(
        self,
        poses: VideoFramePoses,
    ) -> Optional[Tuple[float, float, float, float]]:
        if poses is None or not poses.instances:
            return self._box_raw

        instance = next(
            (instance for instance in poses.instances if instance.id == self._instance_id),
            None,
        )
        if instance is None:
            return self._box_raw

        x1, y1, x2, y2 = instance.box
        return float(x1), float(y1), float(x2), float(y2)

    def _rebuild_pixmap_from_raw(self) -> None:
        if self._frame_raw is None or self._box_raw is None:
            self._label.setText("No data")
            return

        cropped = self._crop_frame_for_widget(self._frame_raw, self._box_raw)

        try:
            self._pixmap_raw = self._frame_to_pixmap_rgb(cropped)
        except Exception as e:
            self._pixmap_raw = None
            self._label.setText(f"Frame conversion error:\n{e}")

    def _crop_frame_for_widget(
        self,
        frame: np.ndarray,
        box: Optional[Tuple[float, float, float, float]],
    ) -> np.ndarray:
        if box is None:
            return frame

        frame_h, frame_w = frame.shape[:2]

        target_size = self._label.size()
        target_w = max(1, target_size.width())
        target_h = max(1, target_size.height())
        target_aspect = target_w / target_h

        x1, y1, x2, y2 = box

        # pad around the original box first
        x1 -= self._box_padding
        y1 -= self._box_padding
        x2 += self._box_padding
        y2 += self._box_padding

        # clamp initial padded box to image
        x1 = max(0.0, x1)
        y1 = max(0.0, y1)
        x2 = min(float(frame_w), x2)
        y2 = min(float(frame_h), y2)

        # fallback if box is degenerate
        if x2 <= x1 or y2 <= y1:
            return frame

        crop_w = x2 - x1
        crop_h = y2 - y1
        crop_aspect = crop_w / crop_h

        cx = 0.5 * (x1 + x2)
        cy = 0.5 * (y1 + y2)

        # expand the crop so it matches widget aspect ratio while still containing the box
        if crop_aspect < target_aspect:
            # too tall/narrow -> expand width
            crop_w = crop_h * target_aspect
        else:
            # too wide/short -> expand height
            crop_h = crop_w / target_aspect

        # if expanded crop exceeds image bounds, shrink to max possible while preserving aspect
        max_w_from_h = frame_h * target_aspect
        max_h_from_w = frame_w / target_aspect

        if crop_w > frame_w:
            crop_w = float(frame_w)
            crop_h = crop_w / target_aspect

        if crop_h > frame_h:
            crop_h = float(frame_h)
            crop_w = crop_h * target_aspect

        # center expanded crop around the box center
        x1 = cx - crop_w / 2.0
        x2 = cx + crop_w / 2.0
        y1 = cy - crop_h / 2.0
        y2 = cy + crop_h / 2.0

        # shift crop back inside image without changing size
        if x1 < 0:
            x2 -= x1
            x1 = 0.0
        if x2 > frame_w:
            x1 -= (x2 - frame_w)
            x2 = float(frame_w)

        if y1 < 0:
            y2 -= y1
            y1 = 0.0
        if y2 > frame_h:
            y1 -= (y2 - frame_h)
            y2 = float(frame_h)

        # final clamp
        x1 = max(0.0, x1)
        y1 = max(0.0, y1)
        x2 = min(float(frame_w), x2)
        y2 = min(float(frame_h), y2)

        ix1 = int(np.floor(x1))
        iy1 = int(np.floor(y1))
        ix2 = int(np.ceil(x2))
        iy2 = int(np.ceil(y2))

        if ix2 <= ix1 or iy2 <= iy1:
            return frame

        return frame[iy1:iy2, ix1:ix2]

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
    def _frame_to_pixmap_rgb(frame: np.ndarray) -> QtGui.QPixmap:
        frame = np.ascontiguousarray(frame)

        if frame.ndim == 2:
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
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
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
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