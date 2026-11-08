"""Shared Ultralytics YOLO loading (cached) and prediction"""

from typing import Dict, List

import numpy as np

from .base import IntegrationUnavailable, hf_download

_MODELS: Dict[str, object] = {}


def load_yolo(repo_id: str, filename: str):
    key = f"{repo_id}/{filename}"
    if key not in _MODELS:
        try:
            from ultralytics import YOLO
        except ImportError:
            raise IntegrationUnavailable("needs ultralytics (pip install ultralytics)")
        _MODELS[key] = YOLO(hf_download(repo_id, filename))
    return _MODELS[key]


def predict(model, bgr_image: np.ndarray, conf: float = 0.25) -> List[Dict]:
    """[{label, confidence, xyxyn}] for one image"""
    results = model.predict(bgr_image, conf=conf, verbose=False)
    out = []
    for res in results:
        boxes = getattr(res, "boxes", None)
        if boxes is None or len(boxes) == 0:
            continue
        names = getattr(res, "names", None) or getattr(model, "names", {})
        xyxyn = np.asarray(boxes.xyxyn.cpu() if hasattr(boxes.xyxyn, "cpu") else boxes.xyxyn)
        cls = np.asarray(boxes.cls.cpu() if hasattr(boxes.cls, "cpu") else boxes.cls).astype(int)
        confs = np.asarray(boxes.conf.cpu() if hasattr(boxes.conf, "cpu") else boxes.conf)
        for box, c, p in zip(xyxyn, cls, confs):
            out.append({"label": names.get(int(c), str(c)) if isinstance(names, dict) else names[int(c)],
                        "confidence": float(p), "xyxyn": [float(v) for v in box]})
    return out
