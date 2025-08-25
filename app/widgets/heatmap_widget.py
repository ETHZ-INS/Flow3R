from typing import Optional, Tuple
import numpy as np
import cv2

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, Signal

import rx
from rx import operators as ops
from rx.scheduler import ThreadPoolScheduler

from app.layout.heatmap_widget import Ui_HeatmapWidget


# ---------------------------------------------------------------------
# OpenCV colour-maps
_COLORMAPS = {
    "jet":     cv2.COLORMAP_JET,
    "hot":     cv2.COLORMAP_HOT,
    "bone":    cv2.COLORMAP_BONE,
    "parula":  cv2.COLORMAP_PARULA,
    "magma":   cv2.COLORMAP_MAGMA,
    "inferno": cv2.COLORMAP_INFERNO,
    "plasma":  cv2.COLORMAP_PLASMA,
    "turbo":   cv2.COLORMAP_TURBO,
}


class HeatmapWidget(Ui_HeatmapWidget, QtWidgets.QDockWidget):
    """
    RxPY sink + Qt widget.
      • Call `attach(Observable[np.ndarray])` to start.
      • Each item must be a 2-D float32 array (any range; it is normalised).
      • Heavy OpenCV work is done on a worker thread, GUI calls on Qt thread.
    """

    image_signal = Signal(np.ndarray)

    # -------- construction ------------------------------------------
    def __init__(self, colour_map: str = "jet"):
        super().__init__()
        self.setupUi(self)

        self._cmap_code = _COLORMAPS.get(colour_map.lower(),
                                         cv2.COLORMAP_JET)

        self.setWindowTitle("Heatmap")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setMinimumSize(20, 20)

        # persistent buffers (allocated once, reused forever)
        self._u8:  np.ndarray | None = None   # normalised greyscale
        self._bgr: np.ndarray | None = None   # colour-mapped
        self._rgb: np.ndarray | None = None   # resized + RGB

        self._qimg: QImage  | None = None
        self._pix:  QPixmap | None = None

        # current label size; updated in resizeEvent
        self._label_size: Tuple[int, int] = (1, 1)

        # schedulers
        self._worker   = ThreadPoolScheduler(1)   # single thread ⇒ FIFO

        self.image_signal.connect(self._update_label)

        self._sub = None

    @classmethod
    def create_widget(cls, config):
        """
        Factory method to create a HeatmapWidget with configuration.
        """
        colour_map = config.get("colour_map", "jet")
        return cls(colour_map)

    @classmethod
    def update_widget(cls, widget, config):
        colour_map = config.get("colour_map", "jet")
        widget._cmap_code = _COLORMAPS.get(colour_map.lower(), cv2.COLORMAP_JET)
        return widget

    # -------- public -------------------------------------------------
    def attach(self, obs):
        """
        Subscribe to a heat-map stream.
        `scheduler` lets you override which Qt thread receives the images.
        """
        self.dispose()

        # Build one clean pipeline:
        #   (heatmap) --heavy--> (RGB buf, w, h) --GUI--> setPixmap
        self._sub = (
            obs.pipe(
                ops.observe_on(self._worker),        # heavy work
            )
            .subscribe(self._process)           # light call
        )
        return self._sub

    def dispose(self):
        if self._sub:
            self._sub.dispose()
            self._sub = None

    # -------- Qt size change ----------------------------------------
    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._label_size = (max(1, self.label.width()),
                            max(1, self.label.height()))

    # -------- heavy work (worker thread) ----------------------------
    def _process(self, hm: np.ndarray):
        """
        • normalise   • colour-map   • resize with aspect-ratio preserved
        Returns (rgb_buffer, w, h) where w×h fits the QLabel.
        """
        if hm.size == 0:
            return None

        src_h, src_w = hm.shape
        # ---------- allocate greyscale + colour buffer --------------
        if self._u8 is None or self._u8.shape != hm.shape:
            self._u8  = np.empty_like(hm, np.uint8)
            self._bgr = np.empty((src_h, src_w, 3), np.uint8)

        # 1. normalise in-place
        vmin, vmax = float(hm.min()), float(hm.max())
        np.multiply(hm - vmin, 255.0 / max(vmax - vmin, 1e-9),
                    out=self._u8, casting="unsafe")

        # 2. colour-map in-place
        cv2.applyColorMap(self._u8, self._cmap_code, dst=self._bgr)

        # ---------- aspect-ratio preserving target size -------------
        lbl_w, lbl_h = self._label_size
        scale = min(lbl_w / src_w, lbl_h / src_h)
        tgt_w = max(1, int(src_w * scale))
        tgt_h = max(1, int(src_h * scale))

        # allocate / reallocate RGB buffer if label size changed
        if self._rgb is None or self._rgb.shape[:2] != (tgt_h, tgt_w):
            self._rgb = np.empty((tgt_h, tgt_w, 3), np.uint8)

        # 3. resize + BGR→RGB in-place
        cv2.resize(self._bgr, (tgt_w, tgt_h), dst=self._rgb,
                   interpolation=cv2.INTER_NEAREST)
        cv2.cvtColor(self._rgb, cv2.COLOR_BGR2RGB, dst=self._rgb)

        self.image_signal.emit(self._rgb)

    # -------- very light GUI call ----------------------------------
    def _update_label(self, rgb):
        w, h = rgb.shape[1], rgb.shape[0]
        self._qimg = QImage(rgb.data, w, h, 3 * w,
                            QImage.Format.Format_RGB888)
        self._pix  = QPixmap.fromImage(self._qimg)

        # buffer already updated in worker thread
        self.label.setPixmap(self._pix)
