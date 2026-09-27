"""
#23 foduucom/stockmarket-pattern-detection-yolov8 — chart patterns on a rendered chart.

The model was trained on screen captures of trading charts; we draw a
platform-style candlestick chart of the recent bars, run the detector and map
each box back to the dates it spans.
"""

from typing import Dict

import pandas as pd

from .base import Integration
from .render import render_screen_chart, to_bgr
from .yolo_common import load_yolo, predict

REPO, WEIGHTS = "foduucom/stockmarket-pattern-detection-yolov8", "model.pt"
LABELS = {
    "Head and shoulders bottom": ("inverse_head_shoulders", "bullish"),
    "Head and shoulders top": ("head_shoulders", "bearish"),
    "M_Head": ("double_top", "bearish"),
    "W_Bottom": ("double_bottom", "bullish"),
    "Triangle": ("triangle", "neutral"),
    "StockLine": ("trend_line", "neutral"),
}


def yolo_chart_patterns(prices: pd.DataFrame, bars: int = 120, conf: float = 0.25) -> Dict:
    window = prices.tail(bars)
    image, mapper = render_screen_chart(window)
    model = load_yolo(REPO, WEIGHTS)
    dates = [d.isoformat() if hasattr(d, "isoformat") else str(d) for d in window.index]
    found = []
    for det in predict(model, to_bgr(image), conf):
        x1, _, x2, _ = det["xyxyn"]
        i1 = int(max(0, min(len(dates) - 1, round(mapper.candle_at(x1)))))
        i2 = int(max(0, min(len(dates) - 1, round(mapper.candle_at(x2)))))
        name, direction = LABELS.get(det["label"], (det["label"].lower().replace(" ", "_"), "neutral"))
        found.append({"type": "vision", "name": name, "model_label": det["label"], "direction": direction,
                      "confidence": round(det["confidence"], 3), "start_date": dates[i1], "completed_date": dates[i2],
                      "recent": i2 >= len(dates) - 10})
    return {"model": REPO, "bars_rendered": len(window), "patterns": sorted(found, key=lambda p: -p["confidence"]),
            "note": "Trained on screen captures (mAP@0.5 ≈ 0.61 per its card); treat detections as hints."}


INTEGRATION = Integration(
    key="yolo_chart_patterns", title="YOLOv8 chart patterns (foduucom)", hf_id=REPO, hf_kind="model",
    category="pattern_detector",
    description="Detects head & shoulders (top/bottom), double tops (M) and bottoms (W), triangles and trend lines on a rendered chart.",
    requires=["ultralytics", "mplfinance", "huggingface_hub"], pip=["ultralytics", "mplfinance", "huggingface_hub"])
INTEGRATION.run = lambda prices=None, **kw: yolo_chart_patterns(prices, **kw)
