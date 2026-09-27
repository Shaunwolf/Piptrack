"""
Chart renderers that reproduce, exactly, how each vision model's training images were drawn.
A model only recognises charts drawn the way it was trained, so every model gets its own renderer.

render_candlestick_window is ported from rohanjain2312/candlestick-pattern-recognition-system
(src/data_pipeline/render_charts.py, MIT License).
render_candlefusion_window follows tuankg1028/CandleFusion (build_dataset/chart_generator.py, Apache-2.0).
"""

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd

from .base import IntegrationUnavailable

# rohanjain2312 config: 20 candles, 640x640, 100 dpi
CANDLE_WINDOW = 20
CANDLE_IMG_SIZE = 640
CANDLE_DPI = 100
X_MARGIN = 0.8
Y_MARGIN_FRAC = 0.04


def _mpf():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import mplfinance as mpf
    except ImportError:
        raise IntegrationUnavailable("chart rendering needs matplotlib and mplfinance (pip install matplotlib mplfinance)")
    return plt, mpf


def _ohlc_frame(df: pd.DataFrame) -> pd.DataFrame:
    """mplfinance wants a DatetimeIndex and capitalised OHLCV columns"""
    out = df.rename(columns={c: c.capitalize() for c in df.columns})[["Open", "High", "Low", "Close", "Volume"]].astype(float)
    out.index = pd.DatetimeIndex(pd.to_datetime(out.index))
    return out


@dataclass(frozen=True)
class PixelMapper:
    width: int
    height: int
    x0: float
    x_scale: float

    def candle_at(self, x_norm: float) -> float:
        """Candle index (float) at a normalised x position of the image"""
        return (x_norm * self.width - self.x0) / self.x_scale


def render_candlestick_window(window: pd.DataFrame) -> Tuple[np.ndarray, PixelMapper]:
    """The exact rendering used to train rohanjain2312/candlestick-pattern-recognition-system-yolo (RGB)"""
    if len(window) != CANDLE_WINDOW:
        raise ValueError(f"expected {CANDLE_WINDOW} rows, got {len(window)}")
    plt, mpf = _mpf()
    style = mpf.make_mpf_style(
        base_mpf_style="charles",
        marketcolors=mpf.make_marketcolors(up="#26A69A", down="#EF5350", edge={"up": "#26A69A", "down": "#EF5350"},
                                           wick={"up": "#26A69A", "down": "#EF5350"}, volume="in"),
        gridstyle="", facecolor="#FFFFFF", figcolor="#FFFFFF", edgecolor="#FFFFFF",
    )
    frame = _ohlc_frame(window)
    size = CANDLE_IMG_SIZE / CANDLE_DPI
    fig, axes = mpf.plot(frame, type="candle", style=style, figsize=(size, size), volume=False, axisoff=True,
                         returnfig=True, tight_layout=True, scale_padding=0.0,
                         update_width_config={"candle_linewidth": 0.9, "candle_width": 0.62})
    ax = axes[0]
    ax.set_position([0.0, 0.0, 1.0, 1.0])
    ax.set_axis_off()
    ax.set_xlim(-X_MARGIN, CANDLE_WINDOW - 1 + X_MARGIN)
    low, high = float(frame["Low"].min()), float(frame["High"].max())
    span = max(high - low, 1e-9)
    ax.set_ylim(low - Y_MARGIN_FRAC * span, high + Y_MARGIN_FRAC * span)
    fig.set_dpi(CANDLE_DPI)
    fig.canvas.draw()
    width, height = fig.canvas.get_width_height()
    (px0, _), (px1, _) = ax.transData.transform([(0.0, 0.0), (1.0, 1.0)])
    image = np.asarray(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(height, width, 4)[:, :, :3].copy()
    plt.close(fig)
    return image, PixelMapper(width, height, px0, px1 - px0)


def render_screen_chart(window: pd.DataFrame, size: int = 768) -> Tuple[np.ndarray, PixelMapper]:
    """A trading-platform-style chart (candles with axes and gridlines) for screen-capture models like foduucom's"""
    plt, mpf = _mpf()
    frame = _ohlc_frame(window)
    fig, axes = mpf.plot(frame, type="candle", style="yahoo", figsize=(size / 100, size / 100), volume=False,
                         returnfig=True, tight_layout=True)
    fig.set_dpi(100)
    fig.canvas.draw()
    ax = axes[0]
    width, height = fig.canvas.get_width_height()
    (px0, _), (px1, _) = ax.transData.transform([(0.0, 0.0), (1.0, 1.0)])
    image = np.asarray(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(height, width, 4)[:, :, :3].copy()
    plt.close(fig)
    return image, PixelMapper(width, height, px0, px1 - px0)


def render_candlefusion_window(window: pd.DataFrame):
    """CandleFusion's training charts: 30 candles, 'charles' style, volume panel, 3/6 moving averages (PIL image)"""
    plt, mpf = _mpf()
    import io
    try:
        from PIL import Image
    except ImportError:
        raise IntegrationUnavailable("CandleFusion needs Pillow (pip install pillow)")
    buf = io.BytesIO()
    mpf.plot(_ohlc_frame(window), type="candle", style="charles", volume=True, mav=(3, 6),
             savefig=dict(fname=buf, dpi=100, bbox_inches="tight", pad_inches=0.1), tight_layout=True,
             show_nontrading=False, scale_padding=dict(left=0.3, top=0.8, right=0.3, bottom=0.8))
    plt.close("all")
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def to_bgr(image: np.ndarray) -> np.ndarray:
    """Ultralytics expects BGR arrays; matplotlib renders RGB"""
    return np.ascontiguousarray(image[:, :, ::-1])
