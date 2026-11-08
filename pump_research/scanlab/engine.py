"""
Scan Lab engine: configurable indicator blocks combined into one scan.

A scan spec is plain JSON, so the drag-and-drop builder, saved scans and alerts all share it:

    {"match": "all",                      # every group must pass ("any": one group is enough)
     "groups": [{"name": "Setup", "logic": "all", "min": 2, "weight": 1,
                 "blocks": [{"type": "rsi", "params": {"length": 14, ...}, "weight": 1, "negate": false}]}]}

Each block returns `hit` (its condition holds) and `strength` (0..1, how strongly it holds, so near
misses can still rank). A group passes on ALL / ANY / AT LEAST n hits; the blend score is the weighted
strength of every block, 0..100.
"""

import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from ..technicals import indicators as ind
from ..technicals.candles import detect_candles
from ..technicals.composites import adaptive_kalman
from ..technicals.pivots import adaptive_pct, zigzag
from ..toolkit import _Context as ToolContext, normalize_prices

MAX_BLOCKS = 40
MAX_GROUPS = 8


# --- Parameters -------------------------------------------------------------------------------

@dataclass
class Param:
    key: str
    label: str
    kind: str                       # select | multi | number | toggle | text
    default: Any
    options: Optional[List] = None  # [[value, label], ...] for select/multi
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    unit: str = ""
    help: str = ""

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None and v != ""}

    def coerce(self, value):
        """Validate user input against the schema; fall back to the default"""
        if value is None:
            return self.default
        try:
            if self.kind == "number":
                v = float(value)
                if not math.isfinite(v):
                    return self.default
                if self.min is not None:
                    v = max(self.min, v)
                if self.max is not None:
                    v = min(self.max, v)
                step = self.step if self.step is not None else 1
                return int(round(v)) if float(step).is_integer() else round(v, 4)
            if self.kind == "toggle":
                return bool(value) if not isinstance(value, str) else value.lower() in ("1", "true", "yes", "on")
            allowed = [str(o[0]) for o in self.options or []]
            if self.kind == "select":
                return str(value) if str(value) in allowed else self.default
            if self.kind == "multi":
                vals = value if isinstance(value, (list, tuple)) else [value]
                picked = [str(v) for v in vals if str(v) in allowed]
                return picked or list(self.default)
            if self.kind == "text":
                return str(value)[:200]
        except (TypeError, ValueError):
            return self.default
        return self.default


def opts(*pairs):
    return [[v, label] for v, label in pairs]


def select(key, label, options, default, **kw):
    return Param(key, label, "select", default, options=options, **kw)


def multi(key, label, options, default, **kw):
    return Param(key, label, "multi", list(default), options=options, **kw)


def number(key, label, default, lo, hi, step=1, unit="", **kw):
    return Param(key, label, "number", default, min=lo, max=hi, step=step, unit=unit, **kw)


def toggle(key, label, default=False, **kw):
    return Param(key, label, "toggle", default, **kw)


SWING = select("swing", "Swing sensitivity", opts(("auto", "Auto (fits the stock's volatility)"), ("3", "3% tight"),
                                                   ("5", "5%"), ("8", "8%"), ("12", "12%"), ("20", "20% wide")), "auto",
               help="How big a move counts as a swing when finding pivots for patterns and levels")


def within(default=3, hi=60, label="Within the last"):
    return number("within", label, default, 1, hi, 1, "bars")


MA_KINDS = opts(("sma", "SMA"), ("ema", "EMA"), ("wma", "Weighted (WMA)"), ("hma", "Hull (HMA)"),
                ("vwma", "Volume-weighted (VWMA)"), ("kalman", "Adaptive Kalman"))


# --- Blocks -------------------------------------------------------------------------------------

@dataclass
class Family:
    id: str
    title: str
    blurb: str


@dataclass
class Block:
    id: str
    family: str
    title: str
    summary: str
    params: List[Param]
    fn: Callable
    styles: tuple = ()
    needs: tuple = ()          # live data feeds the runner must fetch first (see scanlab.feeds)

    def to_dict(self):
        return {"id": self.id, "family": self.family, "title": self.title, "summary": self.summary,
                "params": [p.to_dict() for p in self.params], "styles": list(self.styles), "needs": list(self.needs)}

    def clean_params(self, raw: Optional[Dict]) -> Dict:
        raw = raw if isinstance(raw, dict) else {}
        return {p.key: p.coerce(raw.get(p.key)) for p in self.params}


FAMILIES: Dict[str, Family] = {}
BLOCKS: Dict[str, Block] = {}


def family(id, title, blurb):
    FAMILIES[id] = Family(id, title, blurb)


def block(id, family_id, title, summary, params, styles=(), needs=()):
    def register(fn):
        BLOCKS[id] = Block(id, family_id, title, summary, params, fn, styles, needs)
        return fn
    return register


def result(hit, strength=None, detail="", direction=None, date=None, **evidence):
    s = (1.0 if hit else 0.0) if strength is None else float(np.clip(strength, 0, 1))
    if not math.isfinite(s):
        s = 0.0
    return {"hit": bool(hit), "strength": round(s, 3), "detail": detail, "direction": direction, "date": date,
            **({"evidence": evidence} if evidence else {})}


def ramp(x, start, full):
    """0 at `start`, 1 at `full` (either direction), clipped"""
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return 0.0
    if full == start:
        return 1.0 if x >= full else 0.0
    return float(np.clip((x - start) / (full - start), 0, 1))


def last(series):
    if series is None or not len(series):
        return None
    v = series.iloc[-1]
    return None if pd.isna(v) else float(v)


# --- Per-ticker context ---------------------------------------------------------------------------

class ScanContext:
    """One ticker's prices plus everything blocks share, computed once and cached"""

    def __init__(self, prices: pd.DataFrame, ticker: str = "", benchmark: Optional[pd.DataFrame] = None,
                 model: Optional[Dict] = None, settings=None, meta: Optional[Dict] = None):
        self.df = normalize_prices(prices).dropna()
        self.ticker, self.benchmark, self.model, self.settings, self.meta = ticker, benchmark, model, settings, meta or {}
        self.end = len(self.df) - 1
        self.o, self.h, self.l, self.c, self.v = (self.df[k] for k in ("open", "high", "low", "close", "volume"))
        self.close = float(self.c.iloc[-1])
        self._cache: Dict = {}

    def external(self, kind):
        """Live data the runner fetched for this ticker (short interest, options, ...); None if unavailable"""
        return (self.meta.get("feeds") or {}).get(kind)

    def memo(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def date(self, idx):
        idx = int(np.clip(idx, 0, self.end))
        d = self.df.index[idx]
        return d.isoformat()[:10] if hasattr(d, "isoformat") else str(d)

    def pivots(self, sens="auto"):
        def calc():
            pct = adaptive_pct(self.df) if sens in (None, "auto") else float(sens) / 100
            return zigzag(self.df, pct)
        return self.memo(("pivots", sens), calc)

    def tools(self, sens="auto"):
        """The drawing-tool context (Fibonacci/Gann) anchored on the chosen swing sensitivity"""
        def calc():
            t = ToolContext(self.df)
            t._pivots = self.pivots(sens)
            return t
        return self.memo(("tools", sens), calc)

    def ma(self, kind, n):
        n = int(n)

        def calc():
            if kind == "ema":
                return ind.ema(self.c, n)
            if kind == "wma":
                return ind.wma(self.c, n)
            if kind == "hma":
                return ind.hma(self.c, n)
            if kind == "vwma":
                return ind.vwma(self.c, self.v, n)
            if kind == "kalman":
                return self.kalman()["kalman"]
            return ind.sma(self.c, n)
        return self.memo(("ma", kind, n), calc)

    def kalman(self):
        return self.memo("kalman", lambda: adaptive_kalman(self.c))

    def atr(self, n=14):
        return self.memo(("atr", n), lambda: ind.atr(self.df, int(n)))

    def avg_volume(self, n=20):
        return self.memo(("avgvol", n), lambda: self.v.rolling(int(n), min_periods=max(3, int(n) // 2)).mean().shift(1))

    def candles(self, lookback):
        lookback = int(lookback)
        return self.memo(("candles", lookback), lambda: detect_candles(self.df, max(1, self.end - lookback + 1), self.end))

    def recent(self, series: pd.Series, n: int):
        """Indices (positions) in the last n bars where a boolean series is true"""
        arr = series.fillna(False).to_numpy(bool)[-int(n):]
        start = self.end - len(arr) + 1
        return [start + i for i, flag in enumerate(arr) if flag]


# --- Spec evaluation -------------------------------------------------------------------------------

def normalize_spec(spec: Dict) -> Dict:
    """Validate a user-supplied spec: known blocks only, params coerced to their schema, limits applied"""
    if not isinstance(spec, dict):
        raise ValueError("scan spec must be an object")
    groups = spec.get("groups") or []
    if not isinstance(groups, list) or not groups:
        raise ValueError("add at least one block to scan")
    out_groups, total = [], 0
    for g in groups[:MAX_GROUPS]:
        if not isinstance(g, dict):
            continue
        blocks = []
        for b in (g.get("blocks") or [])[:MAX_BLOCKS]:
            if not isinstance(b, dict) or b.get("type") not in BLOCKS:
                continue
            total += 1
            if total > MAX_BLOCKS:
                break
            spec_block = BLOCKS[b["type"]]
            blocks.append({"type": b["type"], "uid": str(b.get("uid") or f"b{total}")[:40],
                           "params": spec_block.clean_params(b.get("params")),
                           "weight": float(np.clip(_num(b.get("weight"), 1), 0, 10)),
                           "negate": bool(b.get("negate")), "enabled": b.get("enabled", True) is not False})
        logic = g.get("logic") if g.get("logic") in ("all", "any", "atleast") else "all"
        out_groups.append({"name": str(g.get("name") or "Group")[:60], "logic": logic,
                           "min": int(np.clip(_num(g.get("min"), 1), 1, MAX_BLOCKS)),
                           "weight": float(np.clip(_num(g.get("weight"), 1), 0, 10)), "blocks": blocks})
    if not any(b["enabled"] for g in out_groups for b in g["blocks"]):
        raise ValueError("add at least one block to scan")
    return {"match": "any" if spec.get("match") == "any" else "all", "groups": out_groups,
            "min_score": float(np.clip(_num(spec.get("min_score"), 0), 0, 100)),
            "mode": "ranked" if spec.get("mode") == "ranked" else "strict"}


def _num(v, default):
    try:
        f = float(v)
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


def evaluate(spec: Dict, ctx: ScanContext, normalized: bool = False) -> Dict:
    """Run every block in the spec on one ticker; returns match, blend score and per-block evidence"""
    spec = spec if normalized else normalize_spec(spec)
    groups_out, weighted, weights, bull, bear = [], 0.0, 0.0, 0, 0
    for g in spec["groups"]:
        rows, hits, g_w, g_s = [], 0, 0.0, 0.0
        for b in g["blocks"]:
            if not b["enabled"]:
                continue
            blk = BLOCKS[b["type"]]
            try:
                r = blk.fn(ctx, b["params"])
            except Exception as e:  # one broken block never sinks the scan
                r = result(False, 0, f"could not evaluate: {type(e).__name__}")
            if b["negate"]:
                r = {**r, "hit": not r["hit"], "strength": round(1 - r["strength"], 3), "detail": "NOT · " + r["detail"]}
            hits += r["hit"]
            g_w += b["weight"]
            g_s += b["weight"] * r["strength"]
            if r["hit"] and r.get("direction") == "bullish":
                bull += 1
            elif r["hit"] and r.get("direction") == "bearish":
                bear += 1
            rows.append({"uid": b["uid"], "type": b["type"], "title": blk.title, "family": blk.family, **r})
        n = len(rows)
        passed = n > 0 and (hits == n if g["logic"] == "all" else hits >= 1 if g["logic"] == "any" else hits >= min(g["min"], n))
        strength = g_s / g_w if g_w else 0.0
        groups_out.append({"name": g["name"], "logic": g["logic"], "min": g["min"], "passed": passed, "hits": hits,
                           "blocks": rows, "score": round(100 * strength, 1)})
        if n:
            weighted += g["weight"] * strength
            weights += g["weight"]
    active = [g for g in groups_out if g["blocks"]]
    matched = bool(active) and (all(g["passed"] for g in active) if spec["match"] == "all" else any(g["passed"] for g in active))
    score = round(100 * weighted / weights, 1) if weights else 0.0
    # Strict: the group logic decides; ranked: anything at or above the minimum blend score counts
    matched = (matched if spec["mode"] == "strict" else True) and score >= spec["min_score"]
    return {"matched": matched, "score": score, "groups": groups_out,
            "fired": [b["title"] for g in groups_out for b in g["blocks"] if b["hit"]],
            "bias": "bullish" if bull > bear else "bearish" if bear > bull else "neutral"}


FAMILY_ORDER = ["squeeze", "candles", "harmonics", "chart", "fibgann", "trend", "momentum", "volatility", "volume",
                "structure", "filters", "composite"]


def needed_feeds(spec: Dict) -> List[str]:
    """Live data feeds a (normalized) spec's enabled blocks need"""
    return sorted({n for g in spec["groups"] for b in g["blocks"] if b["enabled"] for n in BLOCKS[b["type"]].needs})


def catalog() -> Dict:
    order = {f: i for i, f in enumerate(FAMILY_ORDER)}
    fams = sorted(FAMILIES.values(), key=lambda f: order.get(f.id, len(order)))
    return {"families": [f.__dict__ for f in fams],
            "blocks": [b.to_dict() for b in BLOCKS.values()]}
