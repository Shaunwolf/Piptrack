"""
Chart specs for the Pump Research pages: Plotly figures (plain dicts) and small
server-rendered SVGs (tremor strips, the pressure gauge, the masthead trace).

Colors follow a validated dark palette (see docs in pump_research/README.md):
one axis per panel, stacked panels instead of dual axes, direction never by color alone.
"""

import math
from html import escape
from typing import Dict, List, Optional

import pandas as pd

from .technicals import indicators as ind
from .technicals.composites import adaptive_kalman

# Tokens (keep in sync with static/css/pump.css)
INK = "#e8e6df"          # primary text
INK_2 = "#a9a79f"        # secondary text
INK_3 = "#6e6c66"        # muted text / hairlines on data
GRID = "#1f252d"
AMBER = "#c98500"        # data accent: the pre-pump build-up
BULL = "#3987e5"         # diverging pole: pre-pump side / bullish
BEAR = "#e66767"         # diverging pole: ordinary side / bearish
MA_STYLES = {"EMA 21": "#3987e5", "WMA 20": "#d95926", "HMA 20": "#199e70", "VWMA 20": "#c98500"}
KALMAN_COLOR = "#d55181"
# Fibonacci & Gann overlays: hidden until toggled in the legend (one or two at a time reads best)
OVERLAY_STYLES = {
    "Trend fib extension": {"color": AMBER, "dash": "dot"},
    "Fib channel": {"color": "#199e70", "dash": "solid"},
    "Fib speed fan": {"color": AMBER, "dash": "solid"},
    "Pitchfan": {"color": "#3987e5", "dash": "solid"},
    "Gann fan": {"color": "#9085e9", "dash": "solid"},
    "Gann box": {"color": "#9085e9", "dash": "dot"},
    "Fib circles": {"color": INK_2, "dash": "solid"},
    "Fib speed arcs": {"color": INK_2, "dash": "dot"},
    "Fib spiral": {"color": "#d95926", "dash": "solid"},
    "Fib time zones": {"color": INK_3, "dash": "dot"},
    "Trend fib time": {"color": "#199e70", "dash": "dot"},
}
DIRECTION = {"bullish": (BULL, "triangle-up"), "bearish": (BEAR, "triangle-down"), "neutral": (INK_3, "diamond")}
FONT = "JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, monospace"

BASE_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": INK_2, "family": FONT, "size": 11},
    "margin": {"l": 56, "r": 44, "t": 36, "b": 36}, "hovermode": "x unified",
    "hoverlabel": {"bgcolor": "#12161b", "bordercolor": "#2a323c", "font": {"color": INK, "family": FONT}},
    "legend": {"orientation": "h", "y": 1.0, "yanchor": "bottom", "x": 0, "font": {"size": 11}},
}


def _axis(**kw):
    return {"gridcolor": GRID, "zeroline": False, "linecolor": GRID, "tickfont": {"color": INK_3}, **kw}


# --- Plotly figures ------------------------------------------------------------

def price_chart(rows: List[Dict], technicals: Optional[Dict] = None, window: Optional[List[str]] = None,
                pump_date: Optional[str] = None, title: str = "") -> Dict:
    """Candles + moving averages + levels + patterns on top, volume in its own panel underneath"""
    if not rows:
        return {"data": [], "layout": BASE_LAYOUT}
    df = pd.DataFrame(rows)
    dates = df["date"].tolist()
    close = df["close"].astype(float)
    log_scale = float(df["high"].max()) > 4 * float(df["low"].min()) > 0

    data = [{"type": "candlestick", "x": dates, "open": df["open"].tolist(), "high": df["high"].tolist(),
             "low": df["low"].tolist(), "close": close.tolist(), "name": "Price", "yaxis": "y",
             "increasing": {"line": {"color": INK, "width": 1}, "fillcolor": "rgba(0,0,0,0)"},
             "decreasing": {"line": {"color": INK_3, "width": 1}, "fillcolor": INK_3}}]
    mas = {"EMA 21": ind.ema(close, 21), "WMA 20": ind.wma(close, 20), "HMA 20": ind.hma(close, 20),
           "VWMA 20": ind.vwma(close, df["volume"].astype(float), 20)}
    for name, series in mas.items():
        data.append({"type": "scatter", "mode": "lines", "x": dates, "yaxis": "y", "name": name,
                     "y": [None if pd.isna(v) else float(v) for v in series],
                     "line": {"width": 1.6, "color": MA_STYLES[name]}})
    kal = adaptive_kalman(close)["kalman"]
    data.append({"type": "scatter", "mode": "lines", "x": dates, "yaxis": "y", "name": "Kalman",
                 "y": [None if pd.isna(v) else float(v) for v in kal], "line": {"width": 2, "color": KALMAN_COLOR, "dash": "dash"}})
    in_window = set(window or [])
    data.append({"type": "bar", "x": dates, "y": df["volume"].tolist(), "name": "Volume", "yaxis": "y2",
                 "showlegend": False, "hovertemplate": "%{y:,.0f} shares<extra>Volume</extra>",
                 "marker": {"color": [AMBER if d in in_window else ("#e8e6df" if d == pump_date else "#3a414b")
                                      for d in dates]}})

    shapes, annotations = [], []
    if window:
        shapes.append({"type": "rect", "xref": "x", "yref": "paper", "x0": window[0], "x1": window[-1], "y0": 0, "y1": 1,
                       "fillcolor": "rgba(201,133,0,0.07)", "line": {"width": 0}, "layer": "below"})
        annotations.append({"x": window[0], "y": 1.0, "yref": "paper", "text": "PRE-PUMP WINDOW", "showarrow": False,
                            "xanchor": "left", "yanchor": "bottom", "font": {"size": 10, "color": AMBER}})
    if pump_date and pump_date in dates:
        shapes.append({"type": "line", "xref": "x", "yref": "paper", "x0": pump_date, "x1": pump_date, "y0": 0, "y1": 1,
                       "line": {"color": INK, "dash": "dot", "width": 1}})
        annotations.append({"x": pump_date, "y": 1.0, "yref": "paper", "text": "PUMP", "showarrow": False,
                            "xanchor": "left", "yanchor": "bottom", "font": {"color": INK, "size": 10}})

    if technicals:
        fib = technicals.get("fibonacci") or {}
        span = math.log10(float(df["high"].max()) / max(float(df["low"].min()), 1e-9)) if log_scale else \
            float(df["high"].max() - df["low"].min()) or 1
        last_labelled = None
        for level, price in sorted((fib.get("levels") or {}).items(), key=lambda kv: kv[1]):
            shapes.append({"type": "line", "xref": "paper", "yref": "y", "x0": 0, "x1": 1, "y0": price, "y1": price,
                           "line": {"color": "rgba(201,133,0,0.45)", "width": 1, "dash": "dot"}})
            pos = math.log10(price) if log_scale and price > 0 else price
            # Only label levels far enough apart to read (about 4% of the visible range)
            if last_labelled is None or abs(pos - last_labelled) > 0.04 * span:
                annotations.append({"xref": "paper", "yref": "y", "x": 1, "y": price, "text": f"{level}", "showarrow": False,
                                    "xanchor": "left", "font": {"size": 9, "color": INK_3}})
                last_labelled = pos
        levels = technicals.get("levels") or {}
        for key, dash in (("support", "solid"), ("resistance", "dash")):
            lv = levels.get(key)
            if lv:
                shapes.append({"type": "line", "xref": "paper", "yref": "y", "x0": 0, "x1": 1, "y0": lv["price"],
                               "y1": lv["price"], "line": {"color": INK_2, "width": 1, "dash": dash}})
        for p in technicals.get("patterns", []):
            color, symbol = DIRECTION[p["direction"]]
            label = p["name"].replace("_", " ")
            if p["type"] == "harmonic":
                pts = [pt for pt in p["points"] if pt["date"] in dates]
                data.append({"type": "scatter", "mode": "lines+markers+text", "yaxis": "y", "name": label.title(),
                             "x": [pt["date"] for pt in pts], "y": [pt["price"] for pt in pts],
                             "text": [pt["label"] for pt in pts], "textposition": "top center",
                             "textfont": {"color": color}, "marker": {"size": 8, "color": color},
                             "line": {"color": color, "width": 2}})
            else:
                d = p.get("completed_date") or p.get("date")
                if d in dates:
                    i = dates.index(d)
                    y = float(df["high"].iloc[i]) * 1.04 if p["direction"] != "bearish" else float(df["low"].iloc[i]) * 0.96
                    data.append({"type": "scatter", "mode": "markers", "x": [d], "y": [y], "yaxis": "y", "showlegend": False,
                                 "name": label, "hovertemplate": f"{label} ({p['direction']})<extra></extra>",
                                 "marker": {"symbol": symbol, "size": 10 if p["type"] == "chart" else 8, "color": color,
                                            "line": {"color": "#0e1116", "width": 2}}})

    vol = df["volume"].astype(float)
    spiky_volume = vol.max() > 20 * max(vol.median(), 1)
    if technicals and technicals.get("fib_gann"):
        data.extend(fib_gann_traces(technicals["fib_gann"], float(df["low"].min()), float(df["high"].max())))
    layout = {**BASE_LAYOUT, "shapes": shapes, "annotations": annotations, "meta": {"title": title},
              "xaxis": _axis(type="category", nticks=10, rangeslider={"visible": False}, anchor="y2"),
              "yaxis": _axis(domain=[0.28, 1], title={"text": "Price (log)" if log_scale else "Price", "font": {"size": 10}},
                             type="log" if log_scale else "linear"),
              "yaxis2": _axis(domain=[0, 0.2], title={"text": "Volume (log)" if spiky_volume else "Volume", "font": {"size": 10}},
                              showticklabels=False, type="log" if spiky_volume else "linear")}
    if log_scale:
        # On log axes Plotly positions data-anchored annotations by log10(value); shapes keep raw values
        for a in annotations:
            if a.get("yref") == "y" and a.get("y", 0) > 0:
                a["y"] = math.log10(a["y"])
    return {"data": data, "layout": layout}


def fib_gann_traces(fg: Dict, lo: float, hi: float) -> List[Dict]:
    """One legend entry per tool (legendgroup); every line of that tool toggles together"""
    traces, shown = [], set()

    def trace(group, name, xs, ys):
        style = OVERLAY_STYLES.get(group, {"color": INK_3, "dash": "dot"})
        traces.append({"type": "scatter", "mode": "lines", "x": xs, "y": ys, "yaxis": "y", "name": group,
                       "legendgroup": group, "showlegend": group not in shown, "visible": "legendonly",
                       "hovertemplate": f"{group} {name}<extra></extra>",
                       "line": {"color": style["color"], "dash": style["dash"], "width": 1.2}})
        shown.add(group)

    for ov in fg.get("overlays", []):
        trace(ov["group"], ov["name"], [p[0] for p in ov["points"]], [max(lo * 0.5, min(hi * 2, p[1])) for p in ov["points"]])
    for group, days in (fg.get("time_lines") or {}).items():
        for d in days:
            trace(group, d, [d, d], [lo, hi])
    return traces


def countdown_chart(countdown: List[Dict]) -> Dict:
    """Two stacked panels sharing the day axis: median volume vs baseline, then median daily return"""
    days = [c["offset"] for c in countdown]
    return {
        "data": [
            {"type": "bar", "x": days, "y": [c["median_volume_ratio"] for c in countdown], "name": "Volume vs baseline",
             "yaxis": "y", "marker": {"color": AMBER}, "hovertemplate": "Day %{x}: %{y:.1f}× normal volume<extra></extra>"},
            {"type": "scatter", "mode": "lines+markers", "x": days, "y": [c["median_return"] * 100 for c in countdown],
             "name": "Daily return", "yaxis": "y2", "line": {"color": INK_2, "width": 2}, "marker": {"size": 8, "color": INK_2},
             "hovertemplate": "Day %{x}: %{y:+.1f}%<extra></extra>"},
        ],
        "layout": {**BASE_LAYOUT, "showlegend": False, "margin": {"l": 56, "r": 16, "t": 12, "b": 36},
                   "xaxis": _axis(title={"text": "Trading days before the pump", "font": {"size": 10}}, anchor="y2", dtick=1),
                   "yaxis": _axis(domain=[0.45, 1], title={"text": "Volume ×", "font": {"size": 10}}, rangemode="tozero"),
                   "yaxis2": _axis(domain=[0, 0.35], title={"text": "Return %", "font": {"size": 10}},
                                   zeroline=True, zerolinecolor=INK_3)},
    }


# --- Server-rendered SVG -----------------------------------------------------------

def tremor_scale(records: List[Dict]) -> float:
    """Shared log scale for every tremor strip so the small multiples are comparable"""
    peak = 1.0
    for rec in records:
        for p in rec.get("daily_profile", []):
            peak = max(peak, p.get("volume_ratio") or 0)
        peak = max(peak, pump_volume_ratio(rec) or 0)
    return math.log10(1 + min(peak, 500))


def pump_volume_ratio(rec: Dict) -> Optional[float]:
    ev, prof = rec.get("event") or {}, rec.get("daily_profile") or []
    if not ev or not prof:
        return None
    base = [p["volume"] / p["volume_ratio"] for p in prof if p.get("volume_ratio")]
    return ev["day_volume"] / (sum(base) / len(base)) if base and ev.get("day_volume") else None


def tremor_strip(rec: Dict, scale: float, width: int = 260, height: int = 64) -> str:
    """Ten bars of volume vs baseline before the pump, then the pump day as an outlined bar"""
    prof = rec.get("daily_profile") or []
    if not prof:
        return ""
    n = len(prof) + 1
    gap = 3
    bar_w = (width - gap * (n - 1)) / n
    base_y = height - 1

    def h(ratio):
        return 0 if not ratio else max(2, (height - 6) * math.log10(1 + min(ratio, 500)) / scale)

    parts = [f'<svg class="tremor" viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img" '
             f'aria-label="Volume versus baseline for the {len(prof)} days before the pump">']
    normal_y = base_y - h(1)
    parts.append(f'<line x1="0" x2="{width}" y1="{normal_y:.1f}" y2="{normal_y:.1f}" class="tremor-normal"/>')
    for i, p in enumerate(prof):
        bh = h(p.get("volume_ratio"))
        x = i * (bar_w + gap)
        tip = f"Day {p['offset']} ({p['date']}): {p['volume_ratio']:.1f}× normal volume, {p['return'] * 100:+.1f}% price" \
            if p.get("volume_ratio") is not None else f"Day {p['offset']}: no baseline"
        parts.append(f'<g class="tremor-day"><title>{escape(tip)}</title>'
                     f'<rect x="{x:.1f}" y="0" width="{bar_w:.1f}" height="{height}" class="hit"/>'
                     f'<rect x="{x:.1f}" y="{base_y - bh:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="2" class="bar"/></g>')
    ratio = pump_volume_ratio(rec)
    x = (n - 1) * (bar_w + gap)
    bh = h(ratio) if ratio else height - 6
    tip = f"Pump day: {ratio:.0f}× normal volume" if ratio else "Pump day"
    parts.append(f'<g class="tremor-day"><title>{escape(tip)}</title>'
                 f'<rect x="{x:.1f}" y="{base_y - bh:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="2" class="pump"/></g>')
    parts.append("</svg>")
    return "".join(parts)


def gauge(score: Optional[float], size: int = 220) -> str:
    """Semicircular 0-100 dial with a needle; value printed large in the middle"""
    r, cx, cy, stroke = size * 0.42, size / 2, size * 0.52, size * 0.07

    def point(frac, radius):
        a = math.pi * (1 - frac)
        return cx + radius * math.cos(a), cy - radius * math.sin(a)

    x0, y0 = point(0, r)
    x1, y1 = point(1, r)
    track = f'<path d="M{x0:.1f},{y0:.1f} A{r:.1f},{r:.1f} 0 0 1 {x1:.1f},{y1:.1f}" class="gauge-track" stroke-width="{stroke:.1f}"/>'
    ticks = []
    for t in range(0, 101, 10):
        ax, ay = point(t / 100, r + stroke * 0.9)
        bx, by = point(t / 100, r + stroke * (1.4 if t % 50 == 0 else 1.15))
        ticks.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" class="gauge-tick"/>')
    body = ""
    if score is not None:
        f = max(0.0, min(1.0, score / 100))
        fx, fy = point(f, r)
        large = 1 if f > 0.5 else 0
        body = (f'<path d="M{x0:.1f},{y0:.1f} A{r:.1f},{r:.1f} 0 {large} 1 {fx:.1f},{fy:.1f}" class="gauge-fill" '
                f'stroke-width="{stroke:.1f}"/>')
        nx, ny = point(f, r * 0.78)
        body += f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{nx:.1f}" y2="{ny:.1f}" class="gauge-needle"/>' \
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{stroke * 0.45:.1f}" class="gauge-hub"/>'
        label = f"{score:.0f}"
    else:
        label = "–"
    text = f'<text x="{cx:.1f}" y="{cy + size * 0.3:.1f}" class="gauge-value">{label}</text>'
    return (f'<svg class="gauge" viewBox="0 0 {size} {size * 0.88:.0f}" width="100%" role="img" '
            f'aria-label="Pre-pump similarity {label} out of 100">{track}{"".join(ticks)}{body}{text}</svg>')


def seismograph(countdown: List[Dict], pump_ratio: Optional[float] = None, width: int = 1200, height: int = 120) -> str:
    """Masthead trace drawn from the real median countdown: calm, tremors, then the eruption"""
    values = [c["median_volume_ratio"] or 1 for c in countdown] if countdown else [1] * 10
    values = values + [pump_ratio or max(values) * 3]
    lead = 6  # quiet baseline before day -10
    series = [0.6] * lead + values
    top = math.log10(1 + max(series))
    aftershocks = [values[-1] * f for f in (0.12, 0.05, 0.02, 0.01)]
    series = series + aftershocks
    step = width / (len(series) - 1)
    eruption = lead + len(values) - 1
    pts = []
    for i, v in enumerate(series):
        # Power < 1 lifts small tremors so the build-up is visible next to the eruption
        amp = (height * 0.47) * (math.log10(1 + v) / top) ** 0.8
        # The pen swings above and below the centre line; the eruption always goes up
        up = (i - eruption) % 2 == 0
        y = height / 2 - amp if up else height / 2 + amp * 0.55
        pts.append(f"{i * step:.1f},{y:.1f}")
    return (f'<svg class="seismo" viewBox="0 0 {width} {height}" preserveAspectRatio="none" aria-hidden="true">'
            f'<line x1="0" x2="{width}" y1="{height / 2}" y2="{height / 2}" class="seismo-axis"/>'
            f'<polyline points="{" ".join(pts)}" class="seismo-trace"/></svg>')


def tells(comparison: List[Dict], limit: int = 10) -> List[Dict]:
    """Top separating features as rows for a diverging bar around 0.5 (no difference)"""
    from .labels import feature_label
    rows = []
    for r in comparison[:limit]:
        p = r["prob_event_higher"]
        rows.append({**r, "label": feature_label(r["feature"]), "side": "higher" if p >= 0.5 else "lower",
                     "strength": abs(p - 0.5) * 2})
    return rows
