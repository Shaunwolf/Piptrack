"""
JONNYVERSE/stockmarket-pattern-detection-yolov8-onnx — the foduucom chart-pattern detector
exported to ONNX (Apache-2.0). Same six labels as #23, but it runs on onnxruntime alone:
no PyTorch or Ultralytics, so it is the light way to get vision chart patterns.

YOLOv8's ONNX head outputs [1, 4 + classes, anchors]: box centre/size in input pixels followed
by one score per class. We letterbox the chart like Ultralytics does, decode, and apply
per-class non-maximum suppression here.
"""

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .base import Integration, IntegrationUnavailable, hf_download
from .chart_patterns_yolo import LABELS
from .render import render_screen_chart

REPO, WEIGHTS = "JONNYVERSE/stockmarket-pattern-detection-yolov8-onnx", "onnx/model.onnx"
CLASSES = ["Head and shoulders bottom", "Head and shoulders top", "M_Head", "StockLine", "Triangle", "W_Bottom"]
_SESSIONS: Dict[str, object] = {}


def load_session():
    if REPO not in _SESSIONS:
        try:
            import onnxruntime as ort
        except ImportError:
            raise IntegrationUnavailable("needs onnxruntime (pip install onnxruntime)")
        _SESSIONS[REPO] = ort.InferenceSession(hf_download(REPO, WEIGHTS), providers=["CPUExecutionProvider"])
    return _SESSIONS[REPO]


def letterbox(image: np.ndarray, size: int) -> Tuple[np.ndarray, float, float, float]:
    """Resize keeping aspect ratio and pad to size x size with grey 114, as Ultralytics does"""
    h, w = image.shape[:2]
    scale = min(size / h, size / w)
    nh, nw = int(round(h * scale)), int(round(w * scale))
    try:
        from PIL import Image  # bilinear, like Ultralytics' cv2.INTER_LINEAR
        resized = np.asarray(Image.fromarray(image).resize((nw, nh), Image.BILINEAR))
    except ImportError:
        rows = np.clip((np.arange(nh) / scale).astype(int), 0, h - 1)
        cols = np.clip((np.arange(nw) / scale).astype(int), 0, w - 1)
        resized = image[rows][:, cols]
    pad_y, pad_x = (size - nh) / 2, (size - nw) / 2
    canvas = np.full((size, size, 3), 114, dtype=np.uint8)
    top, left = int(round(pad_y - 0.1)), int(round(pad_x - 0.1))
    canvas[top:top + nh, left:left + nw] = resized
    return canvas, scale, left, top


def nms(boxes: np.ndarray, scores: np.ndarray, iou: float = 0.45) -> List[int]:
    order, keep = scores.argsort()[::-1], []
    while order.size:
        i = order[0]
        keep.append(int(i))
        xx1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
        yy1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
        xx2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
        yy2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])
        inter = np.clip(xx2 - xx1, 0, None) * np.clip(yy2 - yy1, 0, None)
        area = lambda b: (b[..., 2] - b[..., 0]) * (b[..., 3] - b[..., 1])  # noqa: E731
        overlap = inter / (area(boxes[i]) + area(boxes[order[1:]]) - inter + 1e-9)
        order = order[1:][overlap <= iou]
    return keep


def decode(output: np.ndarray, conf: float, n_classes: int = len(CLASSES)) -> List[Tuple[int, float, np.ndarray]]:
    """[(class, score, xyxy in input pixels)] from a YOLOv8 head output"""
    pred = np.asarray(output)[0]
    if pred.shape[0] == 4 + n_classes and pred.shape[1] != 4 + n_classes:
        pred = pred.T
    scores = pred[:, 4:4 + n_classes]
    cls, best = scores.argmax(1), scores.max(1)
    keep = best >= conf
    cx, cy, w, h = (pred[keep, k] for k in range(4))
    boxes = np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 1)
    cls, best = cls[keep], best[keep]
    out = []
    for c in np.unique(cls):
        idx = np.where(cls == c)[0]
        for j in nms(boxes[idx], best[idx]):
            out.append((int(c), float(best[idx][j]), boxes[idx][j]))
    return out


def onnx_chart_patterns(prices: pd.DataFrame, bars: int = 120, conf: float = 0.25) -> Dict:
    window = prices.tail(bars)
    image, mapper = render_screen_chart(window)
    session = load_session()
    inp = session.get_inputs()[0]
    size = next((d for d in inp.shape[2:] if isinstance(d, int)), 640)
    boxed, scale, left, top = letterbox(image, size)
    tensor = np.ascontiguousarray(boxed.transpose(2, 0, 1)[None].astype(np.float32) / 255.0)
    output = session.run(None, {inp.name: tensor})[0]
    height, width = image.shape[:2]
    dates = [d.isoformat() if hasattr(d, "isoformat") else str(d) for d in window.index]
    found = []
    for c, score, (x1, _, x2, _) in decode(output, conf):
        xn1, xn2 = ((x - left) / scale / width for x in (x1, x2))
        i1 = int(max(0, min(len(dates) - 1, round(mapper.candle_at(xn1)))))
        i2 = int(max(0, min(len(dates) - 1, round(mapper.candle_at(xn2)))))
        label = CLASSES[c] if c < len(CLASSES) else str(c)
        name, direction = LABELS.get(label, (label.lower().replace(" ", "_"), "neutral"))
        found.append({"type": "vision", "name": name, "model_label": label, "direction": direction,
                      "confidence": round(score, 3), "start_date": dates[i1], "completed_date": dates[i2],
                      "recent": i2 >= len(dates) - 10})
    return {"model": REPO, "bars_rendered": len(window), "patterns": sorted(found, key=lambda p: -p["confidence"]),
            "note": "ONNX export of foduucom's detector (trained on screen captures); treat detections as hints."}


INTEGRATION = Integration(
    key="onnx_chart_patterns", title="Chart patterns, ONNX (no PyTorch)", hf_id=REPO, hf_kind="model",
    category="pattern_detector",
    description="The foduucom chart-pattern detector exported to ONNX: head & shoulders, double tops and bottoms, "
                "triangles and trend lines, running on onnxruntime without PyTorch.",
    requires=["onnxruntime", "mplfinance", "huggingface_hub"], pip=["onnxruntime", "mplfinance", "huggingface_hub"])
INTEGRATION.run = lambda prices=None, bars=120, conf=0.25, **_: onnx_chart_patterns(prices, bars=bars, conf=conf)
