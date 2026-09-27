"""
#25 rohanjain2312/candlestick-pattern-recognition-system-yolo — 8 candlestick patterns.

Charts are drawn exactly like the model's training images (20 candles, 640x640,
no axes, BGR), so detections map to specific candles of the latest 20 bars.
Its own card reports the patterns don't improve next-day prediction on SPY;
it's a pattern reader, not a forecaster.
"""

from typing import Dict

import pandas as pd

from .base import Integration
from .render import CANDLE_WINDOW, render_candlestick_window, to_bgr
from .yolo_common import load_yolo, predict

REPO, WEIGHTS = "rohanjain2312/candlestick-pattern-recognition-system-yolo", "best.pt"
CLASSES = ["Hammer", "ShootingStar", "BullishEngulfing", "BearishEngulfing", "MorningStar", "EveningStar", "Doji", "Harami"]
DIRECTION = {"Hammer": "bullish", "ShootingStar": "bearish", "BullishEngulfing": "bullish", "BearishEngulfing": "bearish",
             "MorningStar": "bullish", "EveningStar": "bearish", "Doji": "neutral", "Harami": "neutral"}


def yolo_candlesticks(prices: pd.DataFrame, conf: float = 0.25) -> Dict:
    window = prices.tail(CANDLE_WINDOW)
    if len(window) < CANDLE_WINDOW:
        return {"error": f"needs {CANDLE_WINDOW} bars"}
    image, mapper = render_candlestick_window(window)
    model = load_yolo(REPO, WEIGHTS)
    dates = [d.isoformat() if hasattr(d, "isoformat") else str(d) for d in window.index]
    found = []
    for det in predict(model, to_bgr(image), conf):
        x1, _, x2, _ = det["xyxyn"]
        last = int(max(0, min(CANDLE_WINDOW - 1, round(mapper.candle_at(x2) - 0.31))))  # right edge minus half a candle
        found.append({"type": "vision", "name": det["label"], "direction": DIRECTION.get(det["label"], "neutral"),
                      "confidence": round(det["confidence"], 3), "completed_date": dates[last],
                      "on_last_candle": last == CANDLE_WINDOW - 1})
    return {"model": REPO, "window": [dates[0], dates[-1]], "patterns": sorted(found, key=lambda p: p["completed_date"]),
            "note": "Labels imitate TA-Lib rules; the model's card finds no next-day predictive value on SPY."}


INTEGRATION = Integration(
    key="yolo_candlesticks", title="YOLO candlestick reader (rohanjain2312)", hf_id=REPO, hf_kind="model",
    category="pattern_detector",
    description="Reads Hammer, Shooting Star, Engulfing, Morning/Evening Star, Doji and Harami off the latest 20 candles.",
    requires=["ultralytics", "mplfinance", "huggingface_hub"], pip=["ultralytics", "mplfinance", "huggingface_hub"])
INTEGRATION.run = lambda prices=None, ticker="", **kw: yolo_candlesticks(prices, **kw)
