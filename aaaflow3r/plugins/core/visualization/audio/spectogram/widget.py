from dataclasses import dataclass
from typing import Optional

import numpy as np
from PySide6 import QtWidgets, QtGui, QtCore

from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from aaaflow3r.plugins.core.typing.audio import AudioFormat, AudioChunk


@dataclass(frozen=True)
class SpectrogramConfig:
    sample_rate: int = 48_000
    n_fft: int = 1024
    hop: int = 256
    window: str = "hann"          # "hann" or "rect"
    min_db: float = -90.0         # corresponds to colourMin/colourMax idea
    max_db: float = -20.0
    fps_limit: int = 60           # repaint cap (doesn't limit processing)
    # If True: apply a softer scale for low amplitudes (optional “lowAmpColourScaleEnabled” feel)
    low_amp_scale: bool = True


def _make_lut_256() -> np.ndarray:
    """
    Blue → cyan → yellow → red spectrogram palette.
    No white; good contrast on light backgrounds.
    Returns uint8 RGBA LUT of shape (256, 4).
    """
    x = np.linspace(0.0, 1.0, 256, dtype=np.float32)

    r = np.zeros_like(x)
    g = np.zeros_like(x)
    b = np.zeros_like(x)

    # Segment 1: deep blue -> cyan
    s1 = x < 0.33
    t = x[s1] / 0.33
    r[s1] = 0.0
    g[s1] = 0.3 * t
    b[s1] = 0.6 + 0.4 * t

    # Segment 2: cyan -> yellow
    s2 = (x >= 0.33) & (x < 0.66)
    t = (x[s2] - 0.33) / 0.33
    r[s2] = t
    g[s2] = 0.3 + 0.7 * t
    b[s2] = 1.0 - t

    # Segment 3: yellow -> red
    s3 = x >= 0.66
    t = (x[s3] - 0.66) / 0.34
    r[s3] = 1.0
    g[s3] = 1.0 - 0.8 * t
    b[s3] = 0.0

    # Gentle gamma shaping for smoother contrast
    gamma = 0.85
    r = r ** gamma
    g = g ** gamma
    b = b ** gamma

    a = np.ones_like(r)

    lut = np.stack([r, g, b, a], axis=1)
    return (lut * 255).astype(np.uint8)


class SpectrogramWidget(QtWidgets.QWidget):
    """
    Live scrolling spectrogram (waterfall):
      - computes STFT from incoming audio chunks
      - shifts image left by 1 column per rendered spectrum
      - draws the newest column at the right edge
    """

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(120)

        self._cfg = SpectrogramConfig(
            sample_rate=48_000,
            n_fft=2048,
            hop=512,
            min_db=-80.0,
            max_db=10.0,
            low_amp_scale=True,
        )
        self._handle: Optional[IVisualizerHandle[AudioFormat, AudioChunk]] = None

        # Precompute window
        if self._cfg.window == "hann":
            self._win = np.hanning(self._cfg.n_fft).astype(np.float32)
        else:
            self._win = np.ones(self._cfg.n_fft, dtype=np.float32)

        # STFT input buffer (rolling)
        self._inbuf = np.zeros(self._cfg.n_fft, dtype=np.float32)
        self._infill = 0  # how many valid samples currently staged

        self._ema_power: Optional[np.ndarray] = None
        self._ema_alpha = 1  # 0..1, higher = less smoothing

        # LUT
        self._lut = _make_lut_256()  # RGBA

        # Backing image (created/updated on resize)
        self._img: Optional[QtGui.QImage] = None

        # Cache size to rebuild image when needed
        self._img_w = 0
        self._img_h = 0

        # Repaint timer (limits UI updates)
        self._paint_timer = QtCore.QTimer(self)
        self._paint_timer.setInterval(max(1, int(1000 / max(1, self._cfg.fps_limit))))
        self._paint_timer.timeout.connect(self.update)

        # Track last error as tooltip
        self.setToolTip("")

    # ---- Qt-ish model hookup ----

    def set_handle(self, handle: Optional[IVisualizerHandle[None, np.ndarray]]) -> None:
        if self._handle is not None:
            try:
                self._handle.item_changed.disconnect(self._on_chunk)
                self._handle.error_changed.disconnect(self._on_error)
                self._handle.completed_changed.disconnect(self._on_completed)
            except (TypeError, RuntimeError):
                pass

        self._handle = handle

        if self._handle is not None:
            self._handle.item_changed.connect(self._on_chunk)
            self._handle.error_changed.connect(self._on_error)
            self._handle.completed_changed.connect(self._on_completed)
            self._paint_timer.start()
        else:
            self._paint_timer.stop()

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        self.set_handle(None)
        super().closeEvent(e)

    # ---- Data slots ----

    @QtCore.Slot(object)
    def _on_chunk(self, chunk_obj: AudioChunk) -> None:
        x = self._to_mono_float32(chunk_obj.samples)
        if x.size == 0:
            return

        # Feed samples; emit as many hop-sized steps as possible
        self._feed_samples(x)

    @QtCore.Slot(str)
    def _on_error(self, exc: Exception) -> None:
        self.setToolTip(f"Audio error: {exc}")

    @QtCore.Slot()
    def _on_completed(self) -> None:
        self.setToolTip("Audio completed.")

    # ---- Audio -> STFT columns ----

    def _feed_samples(self, x: np.ndarray) -> None:
        """
        Adds samples to internal buffer and computes one spectrum column per hop.
        """
        cfg = self._cfg

        i = 0
        while i < x.size:
            # Fill _inbuf until n_fft
            need = cfg.n_fft - self._infill
            take = min(need, x.size - i)
            self._inbuf[self._infill:self._infill + take] = x[i:i + take]
            self._infill += take
            i += take

            if self._infill < cfg.n_fft:
                break

            # We have a full frame for STFT
            # We have a full frame for STFT
            frame = self._inbuf.copy()

            # DC removal helps a lot for USB mics
            frame -= float(frame.mean())

            # Window
            frame *= self._win

            # rFFT
            spec = np.fft.rfft(frame)
            mag = np.abs(spec).astype(np.float32)

            # --- Normalization to roughly dBFS-like scale ---
            # For a real-valued sinusoid at full scale, magnitude scales with sum(window)/2.
            ref = (self._win.sum() / 2.0)
            mag = mag / max(ref, 1e-12)

            # Power
            power = mag * mag

            # Time smoothing (EMA) to reduce speckle/noise
            if self._ema_power is None or self._ema_power.shape != power.shape:
                self._ema_power = power
            else:
                a = self._ema_alpha
                self._ema_power = (1.0 - a) * self._ema_power + a * power

            # Power dB
            db = 10.0 * np.log10(self._ema_power + 1e-20)

            self._draw_spectrum_column(db)

            # Slide buffer by hop
            hop = cfg.hop
            if hop >= cfg.n_fft:
                self._infill = 0
            else:
                self._inbuf[:cfg.n_fft - hop] = self._inbuf[hop:]
                self._infill = cfg.n_fft - hop

    def _ensure_image(self) -> None:
        w = max(1, self.width())
        h = max(1, self.height())
        if self._img is not None and w == self._img_w and h == self._img_h:
            return

        self._img_w, self._img_h = w, h
        self._img = QtGui.QImage(w, h, QtGui.QImage.Format.Format_RGBA8888)
        self._img.fill(QtGui.QColor("black"))

    def _draw_spectrum_column(self, db: np.ndarray) -> None:
        """
        Shift image left and draw newest spectrum at rightmost column.
        """
        self._ensure_image()
        if self._img is None:
            return

        cfg = self._cfg
        w, h = self._img_w, self._img_h

        # Shift image left by 1px
        # (QImage.copy is OK at typical sizes; if you want ultra-fast, we can do raw buffer memmove)
        shifted = self._img.copy(1, 0, w - 1, h)
        painter = QtGui.QPainter(self._img)
        painter.drawImage(0, 0, shifted)
        painter.end()

        # Map FFT bins -> pixel rows (top=high freq, bottom=low freq like their stftIndexLookup)
        # rfft bins count = n_fft/2 + 1
        n_bins = db.shape[0]
        # Create indices for each pixel row (0..h-1), highest freq at row 0
        # similar to their: STFT_OUTPUT_SAMPLES - 1 - round(...)
        row_to_bin = (np.linspace(n_bins - 1, 0, h)).astype(np.int32)

        # Normalize dB -> [0,255]
        min_db = cfg.min_db
        max_db = cfg.max_db
        vals = db[row_to_bin]

        if cfg.low_amp_scale:
            # Optional: gently expand low end (similar “low amp colour scale” feel)
            # Map to 0..1 then apply sqrt to emphasize low amplitudes a bit
            t = (vals - min_db) / (max_db - min_db)
            t = np.clip(t, 0.0, 1.0)
            t = np.sqrt(t)
            idx = (t * 255.0).astype(np.uint8)
        else:
            t = (vals - min_db) / (max_db - min_db)
            idx = np.clip(t * 255.0, 0.0, 255.0).astype(np.uint8)

        # Write the rightmost column pixels using LUT
        # Access raw QImage buffer via bits()
        ptr = self._img.bits()  # memoryview
        # Ensure we only read exactly the image bytes (safe even if the view is larger/smaller)
        nbytes = self._img.sizeInBytes()
        arr = np.frombuffer(ptr, dtype=np.uint8, count=nbytes)

        # QImage rows may be padded; use bytesPerLine instead of assuming w*4
        bpl = self._img.bytesPerLine()
        buf = arr.reshape((h, bpl // 4, 4))  # width in pixels = bpl/4 for RGBA8888

        # rightmost column in the actual image width
        buf[:, w - 1, :] = self._lut[idx]

    # ---- Painting ----

    def paintEvent(self, e: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QColor("black"))

        if self._img is None:
            return

        # Draw 1:1 (image already matches widget size)
        p.drawImage(0, 0, self._img)

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        super().resizeEvent(e)

        new_w = max(1, e.size().width())
        new_h = max(1, e.size().height())

        # If we have no image yet, just create one
        if self._img is None:
            self._img_w, self._img_h = new_w, new_h
            self._img = QtGui.QImage(new_w, new_h, QtGui.QImage.Format.Format_RGBA8888)
            self._img.fill(QtGui.QColor("black"))
            return

        # If size unchanged, nothing to do
        if new_w == self._img_w and new_h == self._img_h:
            return

        old_img = self._img

        # Create new backing image
        new_img = QtGui.QImage(new_w, new_h, QtGui.QImage.Format.Format_RGBA8888)
        new_img.fill(QtGui.QColor("black"))

        # Paint old content into the new image (scaled to fill)
        p = QtGui.QPainter(new_img)
        p.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, False)
        p.drawImage(QtCore.QRect(0, 0, new_w, new_h), old_img, old_img.rect())
        p.end()

        self._img = new_img
        self._img_w, self._img_h = new_w, new_h

    # ---- Helpers ----

    @staticmethod
    def _to_mono_float32(chunk: np.ndarray) -> np.ndarray:
        x = chunk

        # Allow (samples,), (samples, channels), (channels, samples)
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

        # Fallback scaling for other ints
        xf = x.astype(np.float32)
        max_abs = float(np.max(np.abs(xf))) if xf.size else 1.0
        if max_abs > 1.0:
            xf /= max_abs
        return np.clip(xf, -1.0, 1.0)
