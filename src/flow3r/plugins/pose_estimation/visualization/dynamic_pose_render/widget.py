import colorsys
from typing import Optional, Tuple, Any

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QWidget
from py3r.media.types import VideoFrame
from py3r.pose.core.types import VideoFramePoses

from flow3r.core.visualization.visualizer_handle import VisualizerHandle
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.pose_estimation.typing.pose_format import PoseFormat


def color_from_hue(hue: float) -> Tuple[int, int, int]:
    color = colorsys.hsv_to_rgb(hue, 1, 1)
    return int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)


class DynamicPoseWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._plot = pg.PlotWidget(self)
        self._plot.setMenuEnabled(False)
        self._plot.hideAxis("left")
        self._plot.hideAxis("bottom")
        self._plot.setAspectLocked(True)
        self._plot.invertY(True)
        self._plot.setBackground(None)

        vb = self._plot.getViewBox()
        vb.setMouseEnabled(x=True, y=True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plot)

        self._status_label = QtWidgets.QLabel(self)
        self._status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(
            "background: rgba(0, 0, 0, 0)"
        )
        self._status_label.hide()

        # Graphics items
        self._image_item = pg.ImageItem(axisOrder="row-major")
        self._plot.addItem(self._image_item)

        self._lines_item = pg.PlotCurveItem(
            pen=pg.mkPen("k", width=2),
            connect="finite",
            skipFiniteCheck=False,
        )
        self._plot.addItem(self._lines_item)

        self._points_item = pg.ScatterPlotItem(
            pxMode=True,
            symbol="o",
            size=12,
            pen=None,  # solid circles, no outline
        )
        self._plot.addItem(self._points_item)

        self._color_map: dict[Tuple[str, str], Tuple[int, int, int]] = {}

        self._handle: Optional[VisualizerHandle[Tuple[VideoFormat, PoseFormat], Tuple[VideoFrame, VideoFramePoses]]] = None

        # latest-only pending data
        self._pending_frame: Optional[Tuple[np.ndarray, VideoFramePoses]] = None

        self._render_timer = QtCore.QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(0)
        self._render_timer.timeout.connect(self._render_latest)

        # track current image size
        self._frame_w: Optional[int] = None
        self._frame_h: Optional[int] = None

        # fit only once, on first visible frame / size
        self._did_initial_fit = False

    def set_handle(self, handle: Optional[VisualizerHandle[Tuple[VideoFormat, PoseFormat], Tuple[VideoFrame, VideoFramePoses]]]) -> None:
        if self._handle is not None:
            try:
                self._handle.format_changed.disconnect(self._on_format)
                self._handle.item_changed.disconnect(self._on_frame)
                self._handle.error_changed.disconnect(self._on_error)
                self._handle.completed_changed.disconnect(self._on_completed)
            except (TypeError, RuntimeError):
                pass

        self._handle = handle
        self._pending_frame = None
        self._render_timer.stop()
        self._frame_w = None
        self._frame_h = None
        self._did_initial_fit = False

        self._image_item.clear()
        self._lines_item.setData([], [])
        self._points_item.setData([])
        self._set_status(None)

        if self._handle is not None:
            self._handle.format_changed.connect(self._on_format)
            self._handle.item_changed.connect(self._on_frame)
            self._handle.error_changed.connect(self._on_error)
            self._handle.completed_changed.connect(self._on_completed)

            self._on_format(self._handle.format)
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
        # Only auto-fit before the first real render fit has happened.
        if self._can_render_now() and not self._did_initial_fit and self._frame_w and self._frame_h:
            self._schedule_render_if_visible()

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

    def _set_status(self, text: Optional[str]) -> None:
        if text:
            self._status_label.setText(text)
            self._status_label.show()
            self._status_label.raise_()
            self._status_label.setGeometry(self.rect())
        else:
            self._status_label.hide()
            self._status_label.clear()

    @QtCore.Slot(object)
    def _on_format(self, desc: Tuple[VideoFormat, PoseFormat]) -> None:
        self._color_map = {
            (instance_type.name, point_name): color_from_hue(point_index / len(instance_type.point_names))
            for instance_type in desc[1].instance_types
            for point_index, point_name in enumerate(instance_type.point_names)
        }

    @QtCore.Slot(object)
    def _on_frame(self, res: Tuple[VideoFrame, VideoFramePoses] = None) -> None:
        try:
            self._pending_frame = (res[0].img, res[1]) if res else None
            self._schedule_render_if_visible()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._set_status(f"Error in _on_frame:\n{e}")

    @QtCore.Slot(object)
    def _on_error(self, err: Optional[Exception]) -> None:
        self._pending_frame = None
        self._set_status(str(err) if err else None)

    @QtCore.Slot()
    def _on_completed(self) -> None:
        self._pending_frame = None
        self._schedule_render_if_visible()
        self._set_status("Video finished")

    @QtCore.Slot()
    def _render_latest(self) -> None:
        self._render_timer.stop()

        if not self._can_render_now():
            return

        if self._pending_frame is None:
            self._set_status("Waiting for video...")
            return

        frame, poses = self._pending_frame

        self._pending_frame = None

        try:
            frame = self._normalize_frame(frame)
            self._update_image(frame)
            self._update_pose(poses)
            self._set_status(None)
        except Exception as e:
            self._set_status(f"Render error:\n{e}")

    def _normalize_frame(self, frame: np.ndarray) -> np.ndarray:
        if not isinstance(frame, np.ndarray):
            raise TypeError(f"Expected numpy array, got {type(frame)!r}")

        if frame.ndim == 2:
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            return frame

        if frame.ndim == 3 and frame.shape[2] in (3, 4):
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            return frame

        raise ValueError(f"Unsupported frame shape: {frame.shape}")

    def _update_image(self, frame: np.ndarray) -> None:
        h, w = frame.shape[:2]

        self._image_item.setImage(frame, autoLevels=False)

        size_changed = (w != self._frame_w) or (h != self._frame_h)
        if size_changed:
            self._frame_w = w
            self._frame_h = h
            self._image_item.setRect(0, 0, w, h)

            # Allow zooming out and some panning outside image bounds.
            # Avoid maxXRange/maxYRange=image size, or zoom-out gets blocked.
            self._plot.setLimits(
                xMin=-w,
                xMax=2*w,
                yMin=-h,
                yMax=2*h,
            )

        if not self._did_initial_fit:
            self._did_initial_fit = True
            self._plot.getViewBox().autoRange(padding=0)

    def _update_pose(self, poses: Optional[VideoFramePoses]) -> None:
        if poses is None:
            self._points_item.setData([])
            self._lines_item.setData([], [])
            return

        points = [(p.x, p.y) for instance in poses.instances for p in instance.points]
        point_colors = [
            self._color_map.get((instance.type.name, point_name), (0, 0, 0))
            for instance in poses.instances
            for point_name, p in zip(instance.type.point_names, instance.points)
        ]
        vertices = []

        points = np.asarray(points, dtype=float)
        if points.size == 0:
            self._points_item.setData([])
            self._lines_item.setData([], [])
            return

        if points.ndim != 2 or points.shape[1] != 2:
            raise ValueError(f"Expected points with shape (N, 2), got {points.shape}")

        # Colored points
        spots = []
        for i, (x, y) in enumerate(points):
            spots.append(
                {
                    "pos": (float(x), float(y)),
                    "brush": pg.mkBrush(point_colors[i]),
                    "pen": None,
                    "size": 7,
                    "symbol": "o",
                }
            )
        self._points_item.setData(spots)

        # Black line segments
        if not vertices:
            self._lines_item.setData([], [])
            return

        xs = []
        ys = []
        n_points = len(points)

        for i, j in vertices:
            if not (0 <= i < n_points and 0 <= j < n_points):
                continue
            xi, yi = points[i]
            xj, yj = points[j]
            xs.extend([xi, xj, np.nan])
            ys.extend([yi, yj, np.nan])

        self._lines_item.setData(xs, ys)

    def resize_overlay(self) -> None:
        self._status_label.setGeometry(self.rect())
