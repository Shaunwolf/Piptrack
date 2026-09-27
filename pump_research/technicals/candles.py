"""Candlestick price-action patterns"""

from typing import List

import numpy as np
import pandas as pd

BULLISH = {"hammer", "inverted_hammer", "bullish_engulfing", "bullish_marubozu", "morning_star",
           "three_white_soldiers", "piercing_line", "gap_up", "dragonfly_doji", "bullish_harami",
           "tweezer_bottom", "bullish_kicker", "three_inside_up", "three_outside_up", "rising_three_methods",
           "bullish_belt_hold", "morning_doji_star"}
BEARISH = {"shooting_star", "hanging_man", "bearish_engulfing", "bearish_marubozu", "evening_star",
           "three_black_crows", "dark_cloud_cover", "gap_down", "gravestone_doji", "bearish_harami",
           "tweezer_top", "bearish_kicker", "three_inside_down", "three_outside_down", "falling_three_methods",
           "bearish_belt_hold", "evening_doji_star"}


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
        if body[i] <= 0.35 * rng[i] and upper[i] >= body[i] and lower[i] >= body[i] and body[i] > 0.1 * rng[i]:
            add(i, "spinning_top")
        # Harami: small body inside the previous large body
        if body[i - 1] > 0 and max(o[i], c[i]) <= max(o[i - 1], c[i - 1]) and min(o[i], c[i]) >= min(o[i - 1], c[i - 1]) \
                and body[i] <= 0.5 * body[i - 1]:
            if red[i - 1] and green[i]:
                add(i, "bullish_harami")
            elif green[i - 1] and red[i]:
                add(i, "bearish_harami")
        tweezer_tol = 0.002 * c[i]
        if downtrend and red[i - 1] and green[i] and abs(l[i] - l[i - 1]) <= tweezer_tol:
            add(i, "tweezer_bottom")
        if uptrend and green[i - 1] and red[i] and abs(h[i] - h[i - 1]) <= tweezer_tol:
            add(i, "tweezer_top")
        # Kicker: direction flips with a gap between opens
        if red[i - 1] and green[i] and o[i] > o[i - 1] and body[i] >= 0.6 * rng[i]:
            add(i, "bullish_kicker")
        if green[i - 1] and red[i] and o[i] < o[i - 1] and body[i] >= 0.6 * rng[i]:
            add(i, "bearish_kicker")
        # Belt hold: opens at the extreme and runs the other way
        if downtrend and green[i] and lower[i] <= 0.03 * rng[i] and body[i] >= 0.6 * rng[i]:
            add(i, "bullish_belt_hold")
        if uptrend and red[i] and upper[i] <= 0.03 * rng[i] and body[i] >= 0.6 * rng[i]:
            add(i, "bearish_belt_hold")
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
            doji_mid = body[i - 1] <= 0.1 * (h[i - 1] - l[i - 1] or 1)
            if big_prev and doji_mid and red[i - 2] and green[i] and c[i] > (o[i - 2] + c[i - 2]) / 2:
                add(i, "morning_doji_star")
            if big_prev and doji_mid and green[i - 2] and red[i] and c[i] < (o[i - 2] + c[i - 2]) / 2:
                add(i, "evening_doji_star")
            # Three inside: harami then confirmation beyond the first candle's open
            inside_prev = max(o[i - 1], c[i - 1]) <= max(o[i - 2], c[i - 2]) and min(o[i - 1], c[i - 1]) >= min(o[i - 2], c[i - 2])
            if inside_prev and red[i - 2] and green[i - 1] and green[i] and c[i] > o[i - 2]:
                add(i, "three_inside_up")
            if inside_prev and green[i - 2] and red[i - 1] and red[i] and c[i] < o[i - 2]:
                add(i, "three_inside_down")
            # Three outside: engulfing then confirmation
            if red[i - 2] and green[i - 1] and o[i - 1] <= c[i - 2] and c[i - 1] >= o[i - 2] and green[i] and c[i] > c[i - 1]:
                add(i, "three_outside_up")
            if green[i - 2] and red[i - 1] and o[i - 1] >= c[i - 2] and c[i - 1] <= o[i - 2] and red[i] and c[i] < c[i - 1]:
                add(i, "three_outside_down")
        if i >= 4:
            # Rising/falling three methods: long candle, three small counter candles inside it, long continuation
            first_big = body[i - 4] >= 0.6 * (h[i - 4] - l[i - 4] or 1)
            inner = range(i - 3, i)
            contained = all(h[k] <= h[i - 4] and l[k] >= l[i - 4] and body[k] <= 0.5 * body[i - 4] for k in inner)
            if first_big and contained and green[i - 4] and green[i] and c[i] > c[i - 4]:
                add(i, "rising_three_methods")
            if first_big and contained and red[i - 4] and red[i] and c[i] < c[i - 4]:
                add(i, "falling_three_methods")
    return found
