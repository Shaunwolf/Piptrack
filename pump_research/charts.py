"""Plotly figure specs (plain dicts) for the web pages"""

import math
from typing import Dict, List, Optional

import pandas as pd

from .technicals import indicators as ind

MA_STYLES = {"EMA 21": "#60a5fa", "WMA 20": "#f59e0b", "HMA 20": "#a78bfa", "VWMA 20": "#34d399"}
PATTERN_COLORS = {"bullish": "#22c55e", "bearish": "#ef4444", "neutral": "#9ca3af"}
DARK_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)", "font": {"color": "#d1d5db"},
    "margin": {"l": 50, "r": 20, "t": 30, "b": 40}, "hovermode": "x unified",
    "legend": {"orientation": "h", "y": 1.08},
    "xaxis": {"rangeslider": {"visible": False}, "gridcolor": "#374151", "type": "category", "nticks": 12},
    "yaxis": {"gridcolor": "#374151", "title": "Price"},
    "yaxis2": {"overlaying": "y", "side": "right", "showgrid": False, "showticklabels": False},
}


def price_chart(rows: List[Dict], technicals: Optional[Dict] = None, window: Optional[List[str]] = None,
                pump_date: Optional[str] = None, title: str = "") -> Dict:
    if not rows:
        return {"data": [], "layout": DARK_LAYOUT}
    df = pd.DataFrame(rows)
    dates = df["date"].tolist()
    close = df["close"].astype(float)
    data = [
        {"type": "bar", "x": dates, "y": df["volume"].tolist(), "name": "Volume", "yaxis": "y2",
         "marker": {"color": "rgba(148,163,184,0.25)"}, "hoverinfo": "skip"},
        {"type": "candlestick", "x": dates, "open": df["open"].tolist(), "high": df["high"].tolist(),
         "low": df["low"].tolist(), "close": close.tolist(), "name": "Price",
         "increasing": {"line": {"color": "#22c55e"}}, "decreasing": {"line": {"color": "#ef4444"}}},
    ]
    mas = {"EMA 21": ind.ema(close, 21), "WMA 20": ind.wma(close, 20), "HMA 20": ind.hma(close, 20),
           "VWMA 20": ind.vwma(close, df["volume"].astype(float), 20)}
    for name, series in mas.items():
        data.append({"type": "scatter", "mode": "lines", "x": dates, "y": [None if pd.isna(v) else float(v) for v in series],
                     "name": name, "line": {"width": 1.3, "color": MA_STYLES[name]}})

    shapes, annotations = [], []
    if window:
        shapes.append({"type": "rect", "xref": "x", "yref": "paper", "x0": window[0], "x1": window[-1], "y0": 0, "y1": 1,
                       "fillcolor": "rgba(250,204,21,0.08)", "line": {"width": 0}, "layer": "below"})
        annotations.append({"x": window[0], "y": 1, "yref": "paper", "text": "pre-pump window", "showarrow": False,
                            "xanchor": "left", "font": {"size": 10, "color": "#facc15"}})
    if pump_date and pump_date in dates:
        shapes.append({"type": "line", "xref": "x", "yref": "paper", "x0": pump_date, "x1": pump_date, "y0": 0, "y1": 1,
                       "line": {"color": "#f472b6", "dash": "dot", "width": 1.5}})
        annotations.append({"x": pump_date, "y": 0.02, "yref": "paper", "text": "pump", "showarrow": False,
                            "font": {"color": "#f472b6", "size": 10}})

    if technicals:
        fib = technicals.get("fibonacci") or {}
        for level, price in (fib.get("levels") or {}).items():
            shapes.append({"type": "line", "xref": "paper", "x0": 0, "x1": 1, "y0": price, "y1": price,
                           "line": {"color": "rgba(250,204,21,0.35)", "width": 1, "dash": "dash"}})
            annotations.append({"xref": "paper", "x": 1, "y": price, "text": f"fib {level}", "showarrow": False,
                                "xanchor": "right", "font": {"size": 9, "color": "#facc15"}})
        levels = technicals.get("levels") or {}
        for key, color in (("support", "#22c55e"), ("resistance", "#ef4444")):
            lv = levels.get(key)
            if lv:
                shapes.append({"type": "line", "xref": "paper", "x0": 0, "x1": 1, "y0": lv["price"], "y1": lv["price"],
                               "line": {"color": color, "width": 1}})
        for p in technicals.get("patterns", []):
            color = PATTERN_COLORS[p["direction"]]
            if p["type"] == "harmonic":
                pts = [pt for pt in p["points"] if pt["date"] in dates]
                data.append({"type": "scatter", "mode": "lines+markers+text", "name": p["name"].replace("_", " ").title(),
                             "x": [pt["date"] for pt in pts], "y": [pt["price"] for pt in pts],
                             "text": [pt["label"] for pt in pts], "textposition": "top center",
                             "line": {"color": color, "width": 2}})
            else:
                d = p.get("completed_date") or p.get("date")
                if d in dates:
                    i = dates.index(d)
                    y = float(df["high"].iloc[i]) * 1.03 if p["direction"] != "bearish" else float(df["low"].iloc[i]) * 0.97
                    data.append({"type": "scatter", "mode": "markers", "x": [d], "y": [y], "showlegend": False,
                                 "name": p["name"].replace("_", " "), "hovertemplate": p["name"].replace("_", " ") + "<extra></extra>",
                                 "marker": {"symbol": "triangle-up" if p["direction"] != "bearish" else "triangle-down",
                                            "size": 9 if p["type"] == "chart" else 6, "color": color}})

    layout = {**DARK_LAYOUT, "shapes": shapes, "annotations": annotations, "title": {"text": title, "font": {"size": 14}}}
    # Keep volume in the bottom quarter, and use a log price scale when a pump would flatten everything else
    layout["yaxis2"] = {**DARK_LAYOUT["yaxis2"], "range": [0, float(df["volume"].max()) * 4 or 1]}
    if float(df["high"].max()) > 4 * float(df["low"].min()) > 0:
        layout["yaxis"] = {**DARK_LAYOUT["yaxis"], "type": "log", "title": "Price (log)"}
        # On log axes Plotly positions data-anchored annotations by log10(value); shapes keep raw values
        for a in annotations:
            if a.get("yref", "y") == "y" and a.get("y", 0) > 0:
                a["y"] = math.log10(a["y"])
    return {"data": data, "layout": layout}


def countdown_chart(countdown: List[Dict]) -> Dict:
    days = [c["offset"] for c in countdown]
    return {
        "data": [
            {"type": "bar", "x": days, "y": [c["median_volume_ratio"] for c in countdown], "name": "Median volume vs baseline",
             "marker": {"color": "#60a5fa"}},
            {"type": "scatter", "mode": "lines+markers", "x": days, "y": [c["median_return"] * 100 for c in countdown],
             "name": "Median daily return %", "yaxis": "y2", "line": {"color": "#f472b6"}},
        ],
        "layout": {**DARK_LAYOUT, "xaxis": {"title": "Trading days before pump", "gridcolor": "#374151"},
                   "yaxis": {"title": "Volume ×", "gridcolor": "#374151"},
                   "yaxis2": {"overlaying": "y", "side": "right", "title": "Return %", "showgrid": False}},
    }
