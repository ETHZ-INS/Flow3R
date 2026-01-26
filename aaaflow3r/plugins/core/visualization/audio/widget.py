from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle


@dataclass(frozen=True)
class AudioVizConfig:
    sample_rate: int = 48_000
    window_seconds: float = 2.0   # visible history
    channels: int = 1             # expected channels; widget will handle mono from stereo
    latest_only: bool = True
    repaint_hz: int = 60          # max repaint rate


class AudioWidget(QtWidgets.QWidget):
    """
    Dumb widget: shows a rolling waveform for streamed audio chunks.
    Connect a source's chunk signal to push_chunk().
    """

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(20)

        #self._cfg = AudioVizConfig(384_000)
        self._cfg = AudioVizConfig()
        self._handle: Optional[IVisualizerHandle[np.ndarray]] = None

        self._n_window = max(1, int(self._cfg.sample_rate * self._cfg.window_seconds))
        self._ring = np.zeros(self._n_window, dtype=np.float32)
        self._write_idx = 0
        self._filled = 0

        self._pending: Optional[np.ndarray] = None

        # Latest-only render scheduling
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(max(1, int(1000 / max(1, self._cfg.repaint_hz))))
        self._timer.timeout.connect(self.update)

        # Transparent background
        self._bg_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
        self._pen = QtGui.QPen(QtGui.QColor("blue"))
        self._pen.setWidth(1)

    # --- Qt-ish "setSource" (optional but nice, like the video widget) ---

    def set_handle(self, handle: Optional[IVisualizerHandle[np.ndarray]]) -> None:
        if self._handle is not None:
            try:
                self._handle.item_changed.disconnect(self.push_chunk)
                self._handle.error_changed.disconnect(self._on_error)
                self._handle.completed_changed.disconnect(self._on_completed)
            except (TypeError, RuntimeError):
                pass

        self._handle = handle

        if self._handle is not None:
            self._handle.item_changed.connect(self.push_chunk)
            self._handle.error_changed.connect(self._on_error)
            self._handle.completed_changed.connect(self._on_completed)

            if self._handle.item:
                self.push_chunk(self._handle.item)
            if self._handle.error:
                self._on_error(self._handle.error)
            if self._handle.completed:
                self._on_completed()

            self._timer.start()
        else:
            self._timer.stop()

    # --- Slots for data/error/status ---

    @QtCore.Slot(object)
    def push_chunk(self, chunk_obj: object) -> None:
        if not isinstance(chunk_obj, np.ndarray):
            return

        if self._cfg.latest_only:
            self._pending = chunk_obj
        else:
            # If you ever want “no dropping”, you’d queue chunks instead.
            self._pending = chunk_obj

        # In latest-only mode, it’s fine to just let the paint timer draw at repaint_hz.

        # Push into ring immediately (cheap) so even if chunks come fast, we keep newest data.
        self._append_to_ring(chunk_obj)

    @QtCore.Slot(object)
    def _on_error(self, msg: Optional[Exception]) -> None:
        # simplest: show message as overlay via tooltip or store state; here we store for paint
        if msg:
            self.setToolTip(f"Audio error: {msg}")
        else:
            self.setToolTip("")

    @QtCore.Slot(bool)
    def _on_completed(self, completed: bool = True) -> None:
        self.setToolTip("Audio completed.")

    # --- Ring buffer logic ---

    def _append_to_ring(self, chunk: np.ndarray) -> None:
        x = self._to_mono_float32(chunk)  # 1D float32 approx [-1..1]
        if x.size == 0:
            return

        n = x.size
        if n >= self._n_window:
            # take only last window
            x = x[-self._n_window:]
            n = x.size

        end = self._write_idx + n
        if end <= self._n_window:
            self._ring[self._write_idx:end] = x
        else:
            first = self._n_window - self._write_idx
            self._ring[self._write_idx:] = x[:first]
            self._ring[: end % self._n_window] = x[first:]

        self._write_idx = (self._write_idx + n) % self._n_window
        self._filled = min(self._n_window, self._filled + n)

    @staticmethod
    def _to_mono_float32(chunk: np.ndarray) -> np.ndarray:
        x = chunk

        # Accept shapes:
        # - (samples,)
        # - (channels, samples)
        # - (samples, channels)
        if x.ndim == 2:
            # heuristics: treat smaller dimension as channels if it's <= 8
            if x.shape[0] <= 8 and x.shape[1] > x.shape[0]:
                x = x.mean(axis=0)
            elif x.shape[1] <= 8 and x.shape[0] > x.shape[1]:
                x = x.mean(axis=1)
            else:
                # ambiguous; default to mean over axis 0
                x = x.mean(axis=0)

        # Convert dtype to float32 in roughly [-1, 1]
        if np.issubdtype(x.dtype, np.floating):
            xf = x.astype(np.float32, copy=False)
            # If it looks like 0..1 or 0..255, user can normalize upstream; here we assume audio-ish [-1..1]
            # We’ll still clamp.
            return np.clip(xf, -1.0, 1.0)
        if x.dtype == np.int16:
            return (x.astype(np.float32) / 32768.0).clip(-1.0, 1.0)
        if x.dtype == np.int32:
            return (x.astype(np.float32) / 2147483648.0).clip(-1.0, 1.0)

        # fallback
        xf = x.astype(np.float32)
        # heuristic scale if big ints
        max_abs = float(np.max(np.abs(xf))) if xf.size else 1.0
        if max_abs > 1.0:
            xf = xf / max_abs
        return np.clip(xf, -1.0, 1.0)

    def _ordered_window_view(self) -> np.ndarray:
        """Return ring in time order (oldest -> newest) for the filled portion."""
        if self._filled == 0:
            return self._ring[:0]
        if self._filled < self._n_window:
            return self._ring[:self._filled]

        # full: oldest starts at write_idx
        idx = self._write_idx
        return np.concatenate((self._ring[idx:], self._ring[:idx]), axis=0)

    # --- Painting ---

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, False)

        # background
        p.fillRect(self.rect(), self._bg_brush)

        w = self.width()
        h = self.height()
        if w <= 1 or h <= 1:
            return

        y_mid = h // 2
        amp = (h * 0.48)

        data = self._ordered_window_view()
        if data.size < 2:
            # draw midline
            p.setPen(self._pen)
            p.drawLine(0, y_mid, w, y_mid)
            return

        # Draw min/max envelope per x pixel for speed and visual clarity
        n = data.size
        samples_per_px = max(1, n // w)

        p.setPen(self._pen)
        # midline
        p.drawLine(0, y_mid, w, y_mid)

        # For each x, compute min/max over a slice
        for x in range(w):
            start = x * samples_per_px
            if start >= n:
                break
            end = min(n, start + samples_per_px)
            seg = data[start:end]
            lo = float(seg.min())
            hi = float(seg.max())
            y1 = int(y_mid - hi * amp)
            y2 = int(y_mid - lo * amp)
            p.drawLine(x, y1, x, y2)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.set_handle(None)
        super().closeEvent(event)
