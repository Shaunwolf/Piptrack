"""
Candlestick price-action patterns.

Doji, hammer, hanging man, shooting star, inverted hammer, harami and the morning/evening (doji) stars
follow TA-Lib's CDLxxx definitions with its default candle settings, where "short", "long" and "near"
are judged against the average of the preceding candles (10 for bodies and ranges, 5 for "near").
The benchmark against a TA-Lib-labelled dataset (integrations/candle_benchmark.py) checks the match.
"""

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
    body_top, body_bot = np.maximum(o, c), np.minimum(o, c)
    # TA-Lib candle averages: mean over the preceding candles (not including the candle itself)
    avg_body = pd.Series(body).rolling(10, min_periods=3).mean().shift(1).to_numpy()
    avg_hl = pd.Series(h - l).rolling(10, min_periods=3).mean().shift(1).to_numpy()
    avg_near = 0.2 * pd.Series(h - l).rolling(5, min_periods=3).mean().shift(1).to_numpy()
    body_short = np.nan_to_num(avg_body, nan=np.inf)          # BodyShort: body below the average body
    body_long = np.nan_to_num(avg_body, nan=np.inf)           # BodyLong: body above the average body
    doji_max = np.nan_to_num(0.1 * avg_hl, nan=-1.0)          # BodyDoji: body within 10% of the average range
    very_short = np.nan_to_num(0.1 * avg_hl, nan=-1.0)        # ShadowVeryShort
    white = c >= o                                            # TA-Lib colours a flat candle white
    found = []

    def add(i, name):
        found.append({"type": "candle", "name": name, "idx": int(i),
                      "direction": "bullish" if name in BULLISH else "bearish" if name in BEARISH else "neutral"})

    for i in range(max(1, start_idx), end_idx + 1):
        if np.isnan(rng[i]):
            continue
        downtrend = c[i - 1] < trend[i - 1] if not np.isnan(trend[i - 1]) else False
        uptrend = c[i - 1] > trend[i - 1] if not np.isnan(trend[i - 1]) else False
        if body[i] <= doji_max[i]:
            if lower[i] >= 0.6 * rng[i]:
                add(i, "dragonfly_doji")
            elif upper[i] >= 0.6 * rng[i]:
                add(i, "gravestone_doji")
            else:
                add(i, "doji")
        small = body[i] < body_short[i]
        near_prev = avg_near[i - 1] if not np.isnan(avg_near[i - 1]) else 0.0
        if small and lower[i] > body[i] and upper[i] < very_short[i]:
            # Hammer sits at or below the prior candle's low; a hanging man at or above its high
            if body_bot[i] <= l[i - 1] + near_prev:
                add(i, "hammer")
            if body_bot[i] >= h[i - 1] - near_prev:
                add(i, "hanging_man")
        if small and upper[i] > body[i] and lower[i] < very_short[i]:
            # Shooting star gaps up from the prior body; an inverted hammer gaps down
            if body_bot[i] > body_top[i - 1]:
                add(i, "shooting_star")
            if body_top[i] < body_bot[i - 1]:
                add(i, "inverted_hammer")

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
        # Harami: a short body held inside the previous long body
        if body[i - 1] > body_long[i - 1] and body[i] <= body_short[i] \
                and body_top[i] <= body_top[i - 1] and body_bot[i] >= body_bot[i - 1] \
                and (body_top[i] < body_top[i - 1] or body_bot[i] > body_bot[i - 1]):
            add(i, "bearish_harami" if white[i - 1] else "bullish_harami")
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
            # Morning/evening star: long body, a short body gapping away from it, then a real reversal
            # candle that closes 30% or more back into the first body
            long_first = body[i - 2] > body_long[i - 2]
            third_real = body[i] > body_short[i]
            star = body[i - 1] <= body_short[i - 1]
            doji_star = body[i - 1] <= doji_max[i - 1]
            gap_down = body_top[i - 1] < body_bot[i - 2]
            gap_up = body_bot[i - 1] > body_top[i - 2]
            bull_close = white[i] and c[i] > c[i - 2] + 0.3 * body[i - 2]
            bear_close = not white[i] and c[i] < c[i - 2] - 0.3 * body[i - 2]
            if long_first and not white[i - 2] and gap_down and third_real and bull_close:
                if star:
                    add(i, "morning_star")
                if doji_star:
                    add(i, "morning_doji_star")
            if long_first and white[i - 2] and gap_up and third_real and bear_close:
                if star:
                    add(i, "evening_star")
                if doji_star:
                    add(i, "evening_doji_star")
            if all(green[i - k] for k in range(3)) and c[i] > c[i - 1] > c[i - 2] \
                    and o[i - 1] >= o[i - 2] and o[i] >= o[i - 1]:
                add(i, "three_white_soldiers")
            if all(red[i - k] for k in range(3)) and c[i] < c[i - 1] < c[i - 2] \
                    and o[i - 1] <= o[i - 2] and o[i] <= o[i - 1]:
                add(i, "three_black_crows")
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
