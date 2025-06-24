import numpy as np
import rx
from rx import operators as ops


class PositionHeatmapTransform:
    """
    upstream  : Instance           – pose estimate per frame
    downstream: np.ndarray[H,W]    – cumulative heat-map
    """

    def __init__(self,
                 width: int,
                 height: int,
                 kernel_sigma: int = 8,
                 decay: float = 0.0):
        """
        kernel_sigma  – std-dev of the Gaussian kernel in *pixels*.
        decay         – 0.0 keeps every visit forever,
                        0.01 fades map by 1 % each frame.
        """
        self.width   = width
        self.height  = height
        self.decay   = decay
        self.kernel  = self._make_kernel(kernel_sigma)

    # ------------------------------------------------------------------
    def _make_kernel(self, sigma: int) -> np.ndarray:
        k = int(3 * sigma)          # crop at ±3σ
        ax = np.arange(-k, k + 1)
        g  = np.exp(-(ax**2) / (2 * sigma**2))
        kernel = np.outer(g, g)     # 2-D Gaussian
        kernel /= kernel.max()      # peak = 1
        return kernel

    # ------------------------------------------------------------------
    def _accumulate(self, heatmap: np.ndarray, instances) -> np.ndarray:
        center_points = [instance.points[5] for instance in instances]
        """Add one centre point; apply optional decay."""
        if self.decay:
            heatmap *= (1.0 - self.decay)

        # --- choose a reference point; index 5 in your taxonomy -----------
        for p in center_points:
            cx, cy = p.x, p.y
            cx, cy = int(round(cx)), int(round(cy))

            # --- add kernel, trimmed at frame borders -------------------------
            k = self.kernel.shape[0] // 2
            xs = slice(max(0, cx - k), min(self.width,  cx + k + 1))
            ys = slice(max(0, cy - k), min(self.height, cy + k + 1))

            kx0 = xs.start - (cx - k)
            ky0 = ys.start - (cy - k)

            heatmap[ys, xs] += self.kernel[ky0:ky0 + ys.stop - ys.start,
                                           kx0:kx0 + xs.stop - xs.start]

        return heatmap

    # ------------------------------------------------------------------
    def __call__(self, upstream: rx.Observable) -> rx.Observable:
        initial = np.zeros((self.height, self.width), dtype=np.float32)

        return upstream.pipe(
            ops.scan(self._accumulate, seed=initial),
            # normalise [0,1] so GUI can apply a colour-map
            ops.map(lambda heatmap: heatmap / heatmap.max() if heatmap.max() > 0 else heatmap),
        )
