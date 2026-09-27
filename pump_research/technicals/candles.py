"""Candlestick price-action patterns"""

from typing import List

import numpy as np
import pandas as pd

BULLISH = {"hammer", "inverted_hammer", "bullish_engulfing", "bullish_marubozu", "morning_star",
           "three_white_soldiers", "piercing_line", "gap_up", "dragonfly_doji"}
BEARISH = {"shooting_star", "hanging_man", "bearish_engulfing", "bearish_marubozu", "evening_star",
           "three_black_crows", "dark_cloud_cover", "gap_down", "gravestone_doji"}


def detect_candles(df: pd.DataFrame, start_idx: int, end_idx: int) -> List[dict]:
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    body = np.abs(c - o)
    rng = np.where(h - l == 0, np.nan, h - l)
    upper = h - np.maximum(o, c)
    lower = np.minimum(o, c) - l
    green, red = c > o, c < o
    trend = pd.Series(c).rolling(5, min_periods=3).mean().to_numpy()
    found = []

    def add(i, name):
        found.append({"type": "candle", "name": name, "idx": int(i),
                      "direction": "bullish" if name in BULLISH else "bearish" if name in BEARISH else "neutral"})

    for i in range(max(1, start_idx), end_idx + 1):
        if np.isnan(rng[i]):
            continue
        downtrend = c[i - 1] < trend[i - 1] if not np.isnan(trend[i - 1]) else False
        uptrend = c[i - 1] > trend[i - 1] if not np.isnan(trend[i - 1]) else False
        small_body = body[i] <= 0.35 * rng[i]

        if body[i] <= 0.1 * rng[i]:
            if lower[i] >= 0.6 * rng[i]:
                add(i, "dragonfly_doji")
            elif upper[i] >= 0.6 * rng[i]:
                add(i, "gravestone_doji")
            else:
                add(i, "doji")
        elif small_body and lower[i] >= 2 * body[i] and upper[i] <= 0.5 * body[i] + 0.1 * rng[i]:
            add(i, "hammer" if downtrend else "hanging_man" if uptrend else "doji")
        elif small_body and upper[i] >= 2 * body[i] and lower[i] <= 0.5 * body[i] + 0.1 * rng[i]:
            add(i, "inverted_hammer" if downtrend else "shooting_star" if uptrend else "doji")

        if body[i] >= 0.9 * rng[i]:
            add(i, "bullish_marubozu" if green[i] else "bearish_marubozu")

        if red[i - 1] and green[i] and o[i] <= c[i - 1] and c[i] >= o[i - 1] and body[i] > body[i - 1]:
            add(i, "bullish_engulfing")
        if green[i - 1] and red[i] and o[i] >= c[i - 1] and c[i] <= o[i - 1] and body[i] > body[i - 1]:
            add(i, "bearish_engulfing")
        mid_prev = (o[i - 1] + c[i - 1]) / 2
        if red[i - 1] and green[i] and o[i] < l[i - 1] and mid_prev < c[i] < o[i - 1]:
            add(i, "piercing_line")
        if green[i - 1] and red[i] and o[i] > h[i - 1] and o[i - 1] < c[i] < mid_prev:
            add(i, "dark_cloud_cover")
        if h[i] < h[i - 1] and l[i] > l[i - 1]:
            add(i, "inside_bar")
        if h[i] > h[i - 1] and l[i] < l[i - 1]:
            add(i, "outside_bar")
        if l[i] > h[i - 1]:
            add(i, "gap_up")
        if h[i] < l[i - 1]:
            add(i, "gap_down")

        if i >= 2:
            big_prev = body[i - 2] >= 0.6 * (h[i - 2] - l[i - 2])
            star = body[i - 1] <= 0.3 * body[i - 2]
            if big_prev and star and red[i - 2] and green[i] and c[i] > (o[i - 2] + c[i - 2]) / 2:
                add(i, "morning_star")
            if big_prev and star and green[i - 2] and red[i] and c[i] < (o[i - 2] + c[i - 2]) / 2:
                add(i, "evening_star")
            if all(green[i - k] for k in range(3)) and c[i] > c[i - 1] > c[i - 2] \
                    and o[i - 1] >= o[i - 2] and o[i] >= o[i - 1]:
                add(i, "three_white_soldiers")
            if all(red[i - k] for k in range(3)) and c[i] < c[i - 1] < c[i - 2] \
                    and o[i - 1] <= o[i - 2] and o[i] <= o[i - 1]:
                add(i, "three_black_crows")
    return found
