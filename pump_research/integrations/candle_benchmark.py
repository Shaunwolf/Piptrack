"""
#26 rohanjain2312/candlestick-pattern-recognition-system-data — benchmark our candlestick rules.

The dataset's labels are TA-Lib's candlestick rules on 20-candle SPY windows
(test split: after 2018). We read the label files (not the images), rebuild each
window from daily prices, run PipSqueak's detector on the same bars and report,
per pattern, how often we agree with TA-Lib.
"""

import io
import tarfile
from collections import defaultdict
from datetime import datetime
from typing import Callable, Dict, Optional

import pandas as pd

from ..technicals.candles import detect_candles
from .base import Integration, hf_download

REPO = "rohanjain2312/candlestick-pattern-recognition-system-data"
CLASSES = ["Hammer", "ShootingStar", "BullishEngulfing", "BearishEngulfing", "MorningStar", "EveningStar", "Doji", "Harami"]
OURS_TO_THEIRS = {
    "hammer": "Hammer", "shooting_star": "ShootingStar", "bullish_engulfing": "BullishEngulfing",
    "bearish_engulfing": "BearishEngulfing", "morning_star": "MorningStar", "morning_doji_star": "MorningStar",
    "evening_star": "EveningStar", "evening_doji_star": "EveningStar", "doji": "Doji", "dragonfly_doji": "Doji",
    "gravestone_doji": "Doji", "bullish_harami": "Harami", "bearish_harami": "Harami",
}
WINDOW, X_MARGIN = 20, 0.8


def _candle_index(x_norm: float) -> int:
    """Invert the renderer's x mapping: x_norm = (i + margin) / (window - 1 + 2*margin)"""
    return int(round(x_norm * (WINDOW - 1 + 2 * X_MARGIN) - X_MARGIN))


def read_labels(split: str = "test", limit: Optional[int] = None) -> Dict[tuple, set]:
    """{(ticker, end_date): {(class_name, completion_candle_index)}} from the split's YOLO label files"""
    path = hf_download(REPO, f"{split}.tar.gz", repo_type="dataset")
    labels = {}
    with tarfile.open(path, "r:gz") as tar:
        for member in tar:
            if not (member.isfile() and member.name.endswith(".txt") and "/labels/" in f"/{member.name}"):
                continue
            stem = member.name.rsplit("/", 1)[-1][:-4]
            ticker, day = stem.rsplit("_", 1)
            boxes = set()
            for line in io.TextIOWrapper(tar.extractfile(member)).read().splitlines():
                parts = line.split()
                if len(parts) == 5:
                    cls, cx, _, w, _ = int(parts[0]), *map(float, parts[1:])
                    boxes.add((CLASSES[cls], _candle_index(cx + w / 2 - 0.31 / (WINDOW - 1 + 2 * X_MARGIN))))
            labels[(ticker, datetime.strptime(day, "%Y%m%d").date())] = boxes
            if limit and len(labels) >= limit:
                break
    return labels


def candlestick_benchmark(price_loader: Callable[[str, object, object], pd.DataFrame], limit: int = 400,
                          split: str = "test", labels: Optional[Dict] = None) -> Dict:
    """Per-pattern agreement of PipSqueak's candle rules with the dataset's TA-Lib labels"""
    labels = labels if labels is not None else read_labels(split, limit)
    tickers = sorted({t for t, _ in labels})
    prices = {}
    for t in tickers:
        days = [d for tk, d in labels if tk == t]
        prices[t] = price_loader(t, min(days), max(days))
    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    charts = 0
    for (ticker, end), theirs in labels.items():
        df = prices.get(ticker)
        if df is None or df.empty:
            continue
        idx = [i for i, d in enumerate(df.index) if (d.date() if hasattr(d, "date") else d) <= end]
        if len(idx) < WINDOW:
            continue
        window = df.iloc[idx[-1] - WINDOW + 1: idx[-1] + 1]
        ours = {(OURS_TO_THEIRS[c["name"]], c["idx"]) for c in detect_candles(window, 1, WINDOW - 1)
                if c["name"] in OURS_TO_THEIRS}
        charts += 1
        for cls in CLASSES:
            a = {i for n, i in ours if n == cls}
            b = {i for n, i in theirs if n == cls and i > 0}
            tp[cls] += len(a & b)
            fp[cls] += len(a - b)
            fn[cls] += len(b - a)
    per_class = {}
    for cls in CLASSES:
        p = tp[cls] / (tp[cls] + fp[cls]) if tp[cls] + fp[cls] else None
        r = tp[cls] / (tp[cls] + fn[cls]) if tp[cls] + fn[cls] else None
        per_class[cls] = {"agree": tp[cls], "only_ours": fp[cls], "only_talib": fn[cls],
                          "precision_vs_talib": p, "recall_vs_talib": r}
    return {"dataset": REPO, "split": split, "charts_compared": charts, "per_pattern": per_class,
            "note": "Agreement with TA-Lib's rules, not correctness: both are heuristics."}


def _default_loader(ticker, start, end):
    from datetime import timedelta
    from ..config import Settings
    from ..sources import default_price_sources
    from ..sources.prices import records_to_frame
    for source in default_price_sources(Settings()):
        result = source.fetch(ticker, start - timedelta(days=45), end)
        if result.status == "ok":
            return records_to_frame(result.records)
    return pd.DataFrame()


INTEGRATION = Integration(
    key="candlestick_benchmark", title="Candlestick rule benchmark (rohanjain2312 dataset)", hf_id=REPO, hf_kind="dataset",
    category="validation",
    description="Scores PipSqueak's candlestick detector against TA-Lib-labelled 20-candle SPY charts (test split after 2018).",
    requires=["huggingface_hub"], pip=["huggingface_hub"])
INTEGRATION.run = lambda prices=None, limit=400, **kw: candlestick_benchmark(kw.get("price_loader") or _default_loader, limit=limit)
