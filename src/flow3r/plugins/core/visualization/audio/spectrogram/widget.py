from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional

import numpy as np
from PySide6 import QtWidgets, QtGui, QtCore

from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.plugins.core.typing.audio import AudioFormat, AudioChunk


@dataclass(frozen=True)
class SpectrogramConfig:
    sample_rate: int = 48_000
    n_fft: int = 2048
    hop: int = 512
    window: str = "hann"                 # "hann" or "rect"
    min_db: float = -120.0         # corresponds to colourMin/colourMax idea
    max_db: float = -100.0
    fps_limit: int = 30                  # UI repaint cap
    low_amp_scale: bool = True
    display_columns_per_second: float = 80.0
    history_seconds: float = 10.0
    column_aggregation: str = "max"      # "max" or "mean"
    ema_alpha: float = 1.0               # 0..1, higher = less smoothing


def _make_lut_256() -> np.ndarray:
    """
    Blue -> cyan -> yellow -> red RGBA LUT.
    Returns uint8 array of shape (256, 4).
    """
    x = np.linspace(0.0, 1.0, 256, dtype=np.float32)

    r = np.zeros_like(x)
    g = np.zeros_like(x)
    b = np.zeros_like(x)

    s1 = x < 0.33
    t = x[s1] / 0.33
    r[s1] = 0.0
    g[s1] = 0.3 * t
    b[s1] = 0.6 + 0.4 * t

    s2 = (x >= 0.33) & (x < 0.66)
    t = (x[s2] - 0.33) / 0.33
    r[s2] = t
    g[s2] = 0.3 + 0.7 * t
    b[s2] = 1.0 - t

    s3 = x >= 0.66
    t = (x[s3] - 0.66) / 0.34
    r[s3] = 1.0
    g[s3] = 1.0 - 0.8 * t
    b[s3] = 0.0

    gamma = 0.85
    r = r ** gamma
    g = g ** gamma
    b = b ** gamma
    a = np.ones_like(r)

    lut = np.stack([r, g, b, a], axis=1)
    return (lut * 255).astype(np.uint8)


class SpectrogramWidget(QtWidgets.QWidget):
    """
    Live scrolling spectrogram with:
      - fixed UI refresh rate (default 30 FPS)
      - sample-rate-independent scroll speed
      - incremental append during streaming
      - full rebuild from history on resize
    """

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(120)

        self._cfg = SpectrogramConfig()
        self._handle: Optional[IVisualizerHandle[AudioFormat, AudioChunk]] = None

        self._lut = _make_lut_256()
        self._reset_dsp_state()
        self._rebuild_window()

        self._img: Optional[QtGui.QImage] = None
        self._img_w = 0
        self._img_h = 0

        self._paint_timer = QtCore.QTimer(self)
        self._paint_timer.setInterval(max(1, int(round(1000.0 / max(1, self._cfg.fps_limit)))))
        self._paint_timer.timeout.connect(self._on_paint_timer)

        self._dirty = False
        self.setToolTip("")

    # ------------------------------------------------------------------
    # Public configuration
    # ------------------------------------------------------------------

    def set_config(self, cfg: SpectrogramConfig) -> None:
        self._cfg = cfg
        self._rebuild_window()
        self._reset_dsp_state()
        self._recreate_image()
        self.update()

        if self._paint_timer.isActive():
            self._paint_timer.setInterval(max(1, int(round(1000.0 / max(1, self._cfg.fps_limit)))))

    # ------------------------------------------------------------------
    # Handle hookup
    # ------------------------------------------------------------------

    def set_handle(self, handle: Optional[IVisualizerHandle[AudioFormat, AudioChunk]]) -> None:
        if self._handle is not None:
            try:
                self._handle.format_changed.disconnect(self._on_format)
                self._handle.item_changed.disconnect(self._on_chunk)
                self._handle.error_changed.disconnect(self._on_error)
                self._handle.completed_changed.disconnect(self._on_completed)
            except (TypeError, RuntimeError):
                pass

        self._handle = handle
        self._reset_dsp_state()
        self._recreate_image()
        self.setToolTip("")

        if self._handle is not None:
            self._handle.format_changed.connect(self._on_format)
            self._handle.item_changed.connect(self._on_chunk)
            self._handle.error_changed.connect(self._on_error)
            self._handle.completed_changed.connect(self._on_completed)

            self._on_format(self._handle.format)
            self._on_error(self._handle.error)
            if self._handle.item is not None:
                self._on_chunk(self._handle.item)
            if self._handle.completed:
                self._on_completed()

            if self.isVisible():
                self._paint_timer.start()
        else:
            self._paint_timer.stop()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.set_handle(None)
        super().closeEvent(event)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        if self._handle is not None:
            self._paint_timer.start()

    def hideEvent(self, event: QtGui.QHideEvent) -> None:
        self._paint_timer.stop()
        super().hideEvent(event)

    # ------------------------------------------------------------------
    # Data slots
    # ------------------------------------------------------------------

    @QtCore.Slot(object)
    def _on_format(self, fmt: Optional[AudioFormat]) -> None:
        if fmt is None:
            return

        sample_rate = getattr(fmt, "sample_rate", None)
        if sample_rate is None:
            return

        sample_rate = int(sample_rate)
        if sample_rate <= 0 or sample_rate == self._cfg.sample_rate:
            return

        self._cfg = replace(self._cfg, sample_rate=sample_rate)
        self._rebuild_window()
        self._reset_dsp_state()
        self._recreate_image()
        self.update()

    @QtCore.Slot(object)
    def _on_chunk(self, chunk_obj: AudioChunk) -> None:
        x = self._to_mono_float32(chunk_obj.samples)
        if x.size == 0:
            return

        self._feed_samples(x)

    @QtCore.Slot(object)
    def _on_error(self, exc: Optional[Exception]) -> None:
        self.setToolTip(f"Audio error: {exc}" if exc else "")

    @QtCore.Slot()
    def _on_completed(self) -> None:
        self.setToolTip("Audio completed.")

    @QtCore.Slot()
    def _on_paint_timer(self) -> None:
        if not self.isVisible():
            return

        if self._pending_columns_db:
            self._flush_pending_columns_to_image()

        if self._dirty:
            self._dirty = False
            self.update()

    # ------------------------------------------------------------------
    # DSP / bucketing
    # ------------------------------------------------------------------

    def _reset_dsp_state(self) -> None:
        self._inbuf = np.zeros(self._cfg.n_fft, dtype=np.float32)
        self._infill = 0

        self._ema_power: Optional[np.ndarray] = None

        self._samples_processed = 0

        self._current_bucket_index: Optional[int] = None
        self._bucket_accum: Optional[np.ndarray] = None
        self._bucket_count = 0

        self._column_history_db: list[np.ndarray] = []
        self._pending_columns_db: list[np.ndarray] = []

        self._dirty = True

    def _rebuild_window(self) -> None:
        if self._cfg.window == "hann":
            self._win = np.hanning(self._cfg.n_fft).astype(np.float32)
        else:
            self._win = np.ones(self._cfg.n_fft, dtype=np.float32)

    def _feed_samples(self, x: np.ndarray) -> None:
        cfg = self._cfg

        i = 0
        while i < x.size:
            need = cfg.n_fft - self._infill
            take = min(need, x.size - i)
            self._inbuf[self._infill:self._infill + take] = x[i:i + take]
            self._infill += take
            i += take

            if self._infill < cfg.n_fft:
                break

            frame = self._inbuf.copy()
            frame -= float(frame.mean())
            frame *= self._win

            spec = np.fft.rfft(frame)
            mag = np.abs(spec).astype(np.float32)

            ref = self._win.sum() / 2.0
            mag = mag / max(ref, 1e-12)

            power = mag * mag

            if self._ema_power is None or self._ema_power.shape != power.shape:
                self._ema_power = power
            else:
                a = float(np.clip(cfg.ema_alpha, 0.0, 1.0))
                self._ema_power = (1.0 - a) * self._ema_power + a * power

            db = 10.0 * np.log10(self._ema_power + 1e-20)
            self._push_stft_frame(db)

            hop = cfg.hop
            self._samples_processed += hop

            if hop >= cfg.n_fft:
                self._infill = 0
            else:
                self._inbuf[:cfg.n_fft - hop] = self._inbuf[hop:]
                self._infill = cfg.n_fft - hop

    def _push_stft_frame(self, db: np.ndarray) -> None:
        """
        Bucket STFT frames into fixed-time display columns so the spectrogram
        scroll speed is independent of sample rate.
        """
        cfg = self._cfg

        t_sec = self._samples_processed / float(max(1, cfg.sample_rate))
        bucket = int(np.floor(t_sec * cfg.display_columns_per_second))

        if self._current_bucket_index is None:
            self._current_bucket_index = bucket
            self._bucket_accum = db.copy()
            self._bucket_count = 1
            return

        if bucket == self._current_bucket_index:
            if cfg.column_aggregation == "mean":
                self._bucket_accum += db
            else:
                self._bucket_accum = np.maximum(self._bucket_accum, db)
            self._bucket_count += 1
            return

        self._finalize_current_bucket()

        self._current_bucket_index = bucket
        self._bucket_accum = db.copy()
        self._bucket_count = 1

    def _finalize_current_bucket(self) -> None:
        if self._bucket_accum is None or self._bucket_count <= 0:
            return

        if self._cfg.column_aggregation == "mean":
            col_db = self._bucket_accum / float(self._bucket_count)
        else:
            col_db = self._bucket_accum.copy()

        self._column_history_db.append(col_db)
        self._pending_columns_db.append(col_db)

        max_cols = max(1, int(round(self._cfg.history_seconds * self._cfg.display_columns_per_second)))
        if len(self._column_history_db) > max_cols:
            extra = len(self._column_history_db) - max_cols
            del self._column_history_db[:extra]

        self._bucket_accum = None
        self._bucket_count = 0
        self._dirty = True

    # ------------------------------------------------------------------
    # Image management
    # ------------------------------------------------------------------

    def _ensure_image(self) -> None:
        w = max(1, self.width())
        h = max(1, self.height())

        if self._img is not None and w == self._img_w and h == self._img_h:
            return

        self._img_w = w
        self._img_h = h
        self._img = QtGui.QImage(w, h, QtGui.QImage.Format.Format_RGBA8888)
        self._img.fill(QtGui.QColor("black"))

    def _recreate_image(self) -> None:
        self._img = None
        self._img_w = 0
        self._img_h = 0
        self._ensure_image()
        self._rebuild_image_from_history()
        self._dirty = True

    def _rebuild_image_from_history(self) -> None:
        self._ensure_image()
        if self._img is None:
            return

        self._img.fill(QtGui.QColor("black"))

        if not self._column_history_db:
            return

        visible_cols = self._column_history_db[-self._img_w:]
        rgba_cols = [self._db_column_to_rgba_column(col_db, self._img_h) for col_db in visible_cols]
        if not rgba_cols:
            return

        buf = self._image_buffer_view(self._img)
        n = len(rgba_cols)
        stacked = np.stack(rgba_cols, axis=1)  # (h, n, 4)
        buf[:, self._img_w - n:self._img_w, :] = stacked

        self._dirty = True

    def _flush_pending_columns_to_image(self) -> None:
        self._ensure_image()
        if self._img is None or not self._pending_columns_db:
            return

        buf = self._image_buffer_view(self._img)

        n = min(len(self._pending_columns_db), self._img_w)
        cols_db = self._pending_columns_db[-n:]
        self._pending_columns_db.clear()

        rgba_cols = [self._db_column_to_rgba_column(col_db, self._img_h) for col_db in cols_db]
        stacked = np.stack(rgba_cols, axis=1)  # (h, n, 4)

        if n < self._img_w:
            buf[:, :self._img_w - n, :] = buf[:, n:self._img_w, :]

        buf[:, self._img_w - n:self._img_w, :] = stacked
        self._dirty = True

    def _db_column_to_rgba_column(self, db: np.ndarray, out_h: int) -> np.ndarray:
        n_bins = db.shape[0]
        row_to_bin = np.linspace(n_bins - 1, 0, out_h).astype(np.int32)
        vals = db[row_to_bin]

        t = (vals - self._cfg.min_db) / max(1e-12, (self._cfg.max_db - self._cfg.min_db))
        t = np.clip(t, 0.0, 1.0)

        if self._cfg.low_amp_scale:
            t = np.sqrt(t)

        idx = (t * 255.0).astype(np.uint8)
        return self._lut[idx]

    @staticmethod
    def _image_buffer_view(img: QtGui.QImage) -> np.ndarray:
        ptr = img.bits()
        arr = np.frombuffer(ptr, dtype=np.uint8, count=img.sizeInBytes())
        bpl = img.bytesPerLine()
        return arr.reshape((img.height(), bpl // 4, 4))

    # ------------------------------------------------------------------
    # Painting / resize
    # ------------------------------------------------------------------

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor("black"))

        if self._img is not None:
            painter.drawImage(0, 0, self._img)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)

        new_w = max(1, event.size().width())
        new_h = max(1, event.size().height())

        if new_w == self._img_w and new_h == self._img_h:
            return

        self._img_w = new_w
        self._img_h = new_h
        self._img = QtGui.QImage(new_w, new_h, QtGui.QImage.Format.Format_RGBA8888)
        self._img.fill(QtGui.QColor("black"))
        self._rebuild_image_from_history()
        self.update()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_mono_float32(chunk: np.ndarray) -> np.ndarray:
        x = chunk

        if x.ndim == 2:
            if x.shape[0] <= 8 and x.shape[1] > x.shape[0]:
                x = x.mean(axis=0)
            elif x.shape[1] <= 8 and x.shape[0] > x.shape[1]:
                x = x.mean(axis=1)
            else:
                x = x.mean(axis=1)

        if np.issubdtype(x.dtype, np.floating):
            xf = x.astype(np.float32, copy=False)
            return np.clip(xf, -1.0, 1.0)

        if x.dtype == np.int16:
            return (x.astype(np.float32) / 32768.0).clip(-1.0, 1.0)

        xf = x.astype(np.float32)
        max_abs = float(np.max(np.abs(xf))) if xf.size else 1.0
        if max_abs > 1.0:
            xf /= max_abs
        return np.clip(xf, -1.0, 1.0)
