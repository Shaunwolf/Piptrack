"""
Everything that was true before each tripler launched, on 1-hour, 4-hour and daily charts:
every Scan Lab block's reading (candles, harmonics, Fibonacci and Gann tools, indicators, structure,
volume), the full technical snapshot, the price path, short-side data, news, filings and Reddit posts.
The same readings are taken on ordinary windows from the same price bands, so each one can be
measured against the base rate.

Writes to out_dir:
  events/<id>.json   one file per tripler: meta, readings, context and the bars needed to redraw it
  dataset.json       slim records (meta, context summary, price paths) for every tripler and control
  readings.csv.gz    one row per window and timeframe: every block hit/strength and every ta_* feature
"""

import json
import logging
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from ..scanlab.engine import BLOCKS, ScanContext
from ..technicals import technical_snapshot
from .discover import HORIZON, PRE_WINDOW, control_windows, discover

TIMEFRAMES = ("1h", "4h", "1d")
BARS_PER_DAY = {"1h": 7, "4h": 2, "1d": 1}
HOURLY_REACH_DAYS = 728            # Yahoo serves hourly bars for the last 730 days
SKIP_BLOCKS = {"pump_dna"}          # needs the trained pump model, not a chart reading
PATH_BEFORE_DAYS, PATH_AFTER_DAYS = 40, HORIZON
ROWS_BEFORE_DAYS, ROWS_AFTER_DAYS = 250, 20
HOURLY_ROWS_BEFORE_DAYS = 30


# --- Prices ---------------------------------------------------------------------------------------

def load_hourly(tickers: List[str], batch: int = 25) -> Dict[str, pd.DataFrame]:
    """Two years of hourly bars per ticker (Yahoo's limit), cached for the day"""
    from ..scanlab.runner import _frame, cache_dir
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    folder, out, missing = cache_dir(), {}, []
    for t in tickers:
        path = os.path.join(folder, f"h730_{stamp}_{t}.pkl")
        if os.path.exists(path):
            try:
                out[t] = pd.read_pickle(path)
                continue
            except Exception:
                pass
        missing.append(t)
    if not missing:
        return out
    import yfinance as yf
    for i in range(0, len(missing), batch):
        chunk = missing[i:i + batch]
        try:
            raw = yf.download(chunk, period="730d", interval="60m", group_by="ticker", auto_adjust=True,
                              threads=True, progress=False)
        except Exception as e:
            logging.warning("hourly download failed for %d tickers: %s", len(chunk), e)
            continue
        for t in chunk:
            try:
                part = raw[t] if isinstance(raw.columns, pd.MultiIndex) and t in raw.columns.get_level_values(0) else (
                    raw if len(chunk) == 1 else None)
            except KeyError:
                part = None
            df = _frame(part)
            if df is not None:
                out[t] = df
                try:
                    df.to_pickle(os.path.join(folder, f"h730_{stamp}_{t}.pkl"))
                except OSError:
                    pass
    return out


def to_4h(h1: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Two 4-hour bars per session, as most charting platforms draw them: 9:30–13:30 and 13:30–16:00"""
    if h1 is None or h1.empty:
        return None
    idx = h1.index
    second = (idx.hour * 60 + idx.minute) >= 13 * 60 + 30
    key = idx.normalize() + pd.to_timedelta(np.where(second, 13.5, 9.5), unit="h")
    g = h1.groupby(key)
    out = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                        "close": g["close"].last(), "volume": g["volume"].sum()})
    out.index.name = None
    return out.dropna(subset=["close"])


def end_position(df: Optional[pd.DataFrame], day: str, intraday: bool) -> Optional[int]:
    """Position of the last bar of `day` (the launch close); None if that day has no bars"""
    if df is None or df.empty:
        return None
    days = np.array([d.isoformat()[:10] for d in df.index])
    hits = np.nonzero(days == day)[0]
    if len(hits):
        return int(hits[-1])
    if intraday:
        return None
    before = np.nonzero(days <= day)[0]
    return int(before[-1]) if len(before) else None


# --- Readings ------------------------------------------------------------------------------------

def block_readings(ctx: ScanContext) -> Dict[str, Dict]:
    out = {}
    for bid, blk in BLOCKS.items():
        if blk.needs or bid in SKIP_BLOCKS:
            continue
        try:
            r = blk.fn(ctx, blk.clean_params({}))
        except Exception as e:
            r = {"hit": False, "strength": 0.0, "detail": f"could not evaluate: {type(e).__name__}", "direction": None}
        out[bid] = {"hit": bool(r["hit"]), "strength": float(r["strength"]), "detail": str(r.get("detail", ""))[:160],
                    "direction": r.get("direction")}
    return out


def readings(df: pd.DataFrame, end_pos: int, window_bars: int, full: bool = False) -> Dict:
    """Every block and the technical snapshot as of bar end_pos (nothing after it is used)"""
    part = df.iloc[:end_pos + 1]
    ctx = ScanContext(part)
    snap = technical_snapshot(part, len(part) - 1, window_bars)
    fg = snap.get("fib_gann") or {}
    out = {"bars": len(part), "as_of": part.index[-1].isoformat(), "close": float(part["close"].iloc[-1]),
           "blocks": block_readings(ctx), "features": snap.get("features") or {},
           "fib_gann": {"price_confluence": fg.get("price_confluence") or [], "time_confluence": fg.get("time_confluence") or [],
                        "summary": fg.get("summary") or {}},
           "patterns": [{"name": p.get("name") or p.get("pattern"), "date": p.get("completed_date") or p.get("date")}
                        for p in snap.get("patterns") or []][:20]}
    if full:
        out["fibonacci"] = snap.get("fibonacci")
        out["levels"] = snap.get("levels")
        out["structure"] = snap.get("structure")
    return out


def price_path(df: pd.DataFrame, end_pos: int, bars_before: int, bars_after: int) -> Dict:
    """Closes relative to the launch close, and volume relative to the average before the window"""
    lo, hi = max(0, end_pos - bars_before), min(len(df), end_pos + bars_after + 1)
    c, v = df["close"].to_numpy(float), df["volume"].to_numpy(float)
    base = c[end_pos]
    vol_base = np.nanmean(v[max(0, end_pos - bars_before - 60):max(1, end_pos - bars_before)]) if end_pos > bars_before else np.nanmean(v[lo:end_pos + 1])
    vol_base = vol_base if vol_base and np.isfinite(vol_base) else np.nan
    return {"offset": list(range(lo - end_pos, hi - end_pos)),
            "close": [round(float(x / base), 4) for x in c[lo:hi]],
            "high": [round(float(x / base), 4) for x in df["high"].to_numpy(float)[lo:hi]],
            "low": [round(float(x / base), 4) for x in df["low"].to_numpy(float)[lo:hi]],
            "volume": [None if not np.isfinite(vol_base) else round(float(x / vol_base), 3) for x in v[lo:hi]]}


def rows(df: pd.DataFrame, lo: int, hi: int) -> List[Dict]:
    part = df.iloc[max(0, lo):min(len(df), hi)]
    return [{"date": d.isoformat()[:19] if d.hour or d.minute else d.isoformat()[:10],
             **{k: round(float(x), 6) for k, x in r.items()}} for d, r in zip(part.index, part.to_dict("records"))]


def window_readings(win: Dict, daily: pd.DataFrame, hourly: Optional[pd.DataFrame], keep_rows: bool) -> Dict:
    """Readings and price paths on all three timeframes for one window (tripler or control)"""
    frames = {"1d": daily, "1h": hourly, "4h": to_4h(hourly)}
    out = {"readings": {}, "paths": {}, "timeframes": []}
    for tf in TIMEFRAMES:
        df = frames[tf]
        pos = end_position(df, win["launch_date"], tf != "1d")
        if pos is None or pos < 40:
            continue
        per = BARS_PER_DAY[tf]
        try:
            out["readings"][tf] = readings(df, pos, PRE_WINDOW * per, full=keep_rows and tf == "1d")
        except Exception as e:
            logging.warning("readings failed for %s %s: %s", win["id"], tf, e)
            continue
        out["paths"][tf] = price_path(df, pos, PATH_BEFORE_DAYS * per if tf == "1d" else PRE_WINDOW * per, PATH_AFTER_DAYS * per)
        out["timeframes"].append(tf)
        if keep_rows and tf == "1d":
            out["rows_1d"] = rows(df, pos - ROWS_BEFORE_DAYS, pos + ROWS_AFTER_DAYS + 1)
        if keep_rows and tf == "1h":
            out["rows_1h"] = rows(df, pos - HOURLY_ROWS_BEFORE_DAYS * per, pos + PATH_AFTER_DAYS * per + 1)
    return out


# --- Context: news, filings, Reddit, short-side data -------------------------------------------------

def context_for(win: Dict, settings, sources, social: bool) -> Dict:
    from ..features import context_features
    days = [date.fromisoformat(d) for d in win["window_dates"]]
    start, end = days[0], days[-1]
    statuses, context = {}, {}
    for src in sources:
        if src.name.startswith("reddit") and not social:
            statuses[src.name] = {"status": "skipped", "detail": "Reddit search budget used up", "records": 0}
            continue
        res = src.fetch(win["ticker"], start, end)
        statuses[src.name] = {"status": res.status, "detail": res.detail, "records": len(res.records)}
        context[src.name] = res.records
    reddit = [p for n in list(context) if n.startswith("reddit") for p in context.pop(n)]
    answered = [n for n, s in statuses.items() if s["status"] in ("ok", "no_data") or (s["status"] == "partial" and s["records"])]
    partial = [n for n, s in statuses.items() if s["status"] == "partial"]
    if any(n.startswith("reddit") for n in statuses):
        context["reddit"] = sorted({(p.get("url") or p.get("text", "")[:80]): p for p in reddit}.values(), key=lambda p: p["date"])
        if any(n.startswith("reddit") for n in answered):
            answered.append("reddit")
        if any(n.startswith("reddit") for n in partial):
            partial.append("reddit")
    feats = context_features(context, days, answered, partial)
    if getattr(settings, "squeeze_data", False):
        try:
            from ..squeeze import squeeze_features
            feats.update(squeeze_features(win["ticker"], days))
            statuses["squeeze"] = {"status": "ok", "detail": "", "records": 1}
        except Exception as e:
            statuses["squeeze"] = {"status": "error", "detail": f"{type(e).__name__}: {e}", "records": 0}
    return {"context_features": feats, "sources": statuses,
            "news": [{k: n.get(k) for k in ("date", "title", "publisher", "url")} for n in
                     context.get("google_news", []) + context.get("polygon_news", []) + context.get("gdelt_news", [])][:60],
            "filings": context.get("sec_filings", [])[:40],
            "reddit": [{k: p.get(k) for k in ("date", "subreddit", "title", "text", "score", "url", "sentiment")}
                       for p in context.get("reddit", [])][:60]}


def tripler_sources(settings):
    """News, filings and Reddit; the Reddit archive is searched only in the most active trading subreddits"""
    from ..sources import ArcticShiftReddit, GoogleNews, PolygonNews, SecEdgarFilings
    reddit = ArcticShiftReddit(settings)
    reddit.subreddits = ("wallstreetbets", "pennystocks", "Shortsqueeze", "smallstreetbets", "RobinHoodPennyStocks")
    reddit.max_pages = 2
    return [SecEdgarFilings(settings), PolygonNews(settings), GoogleNews(settings), reddit]


# --- Flat table ----------------------------------------------------------------------------------------

def flat_rows(rec: Dict) -> List[Dict]:
    out = []
    for tf, rd in (rec.get("readings") or {}).items():
        row = {"id": rec["id"], "ticker": rec["ticker"], "launch_date": rec["launch_date"], "timeframe": tf,
               "tripler": not rec.get("control"), "price_band": rec["price_band"]}
        for bid, b in rd["blocks"].items():
            row[f"blk_{bid}"] = int(b["hit"])
            row[f"str_{bid}"] = round(b["strength"], 3)
        for k, v in rd["features"].items():
            if isinstance(v, bool):
                row[k] = int(v)
            elif isinstance(v, (int, float)) and v is not None and np.isfinite(v):
                row[k] = round(float(v), 5)
        if tf == "1d":
            for k, v in (rec.get("context_features") or {}).items():
                if isinstance(v, bool):
                    row[f"ctx_{k}"] = int(v)
                elif isinstance(v, (int, float)) and v is not None:
                    row[f"ctx_{k}"] = v
        out.append(row)
    return out


def slim(rec: Dict) -> Dict:
    keep = ("id", "ticker", "control", "launch_date", "base_close", "price_band", "window_dates", "triple_date",
            "days_to_triple", "peak_date", "peak_close", "peak_multiple", "peak_high_multiple", "forward_multiple",
            "window_dollar_volume", "timeframes", "context_features")
    out = {k: rec[k] for k in keep if k in rec}
    out["paths"] = {tf: {k: p[k] for k in ("offset", "close", "volume")} for tf, p in (rec.get("paths") or {}).items()}
    out["fired"] = {tf: sorted(b for b, x in rd["blocks"].items() if x["hit"]) for tf, rd in (rec.get("readings") or {}).items()}
    return out


# --- Orchestration ----------------------------------------------------------------------------------------

def collect(tickers: List[str], out_dir: str, settings=None, daily_loader: Optional[Callable] = None,
            hourly_loader: Callable = load_hourly, sources=None, controls_per_event: int = 3, max_events: int = 0,
            social_budget_minutes: float = 60, today: Optional[date] = None) -> Dict:
    from ..config import Settings
    settings = settings or Settings()
    today = today or date.today()
    started = time.time()
    found = discover(tickers, loader=daily_loader)
    events, prices = found["events"], found["prices"]
    if max_events and len(events) > max_events:
        events = events[-max_events:]          # the most recent ones have hourly history
    controls = control_windows(prices, events, per_event=controls_per_event)
    reach = (today - timedelta(days=HOURLY_REACH_DAYS)).isoformat()
    hourly_tickers = sorted({w["ticker"] for w in events + controls if w["launch_date"] >= reach})
    logging.info("%d triplers and %d ordinary windows in %d stocks; hourly bars for %d tickers",
                 len(events), len(controls), found["scanned"], len(hourly_tickers))
    hourly = hourly_loader(hourly_tickers) if hourly_tickers else {}
    sources = tripler_sources(settings) if sources is None else sources
    social_deadline = time.time() + social_budget_minutes * 60
    os.makedirs(os.path.join(out_dir, "events"), exist_ok=True)

    slim_records, table = [], []
    # Interleave triplers and controls so a Reddit budget that runs out still leaves both groups comparable
    order = []
    ctl_iter = iter(controls)
    for e in events:
        order.append(e)
        order.extend(c for _, c in zip(range(controls_per_event), ctl_iter))
    order.extend(ctl_iter)
    for n, win in enumerate(order):
        is_event = not win.get("control")
        rec = dict(win)
        rec.update(window_readings(win, prices[win["ticker"]], hourly.get(win["ticker"]), keep_rows=is_event))
        rec.update(context_for(win, settings, sources, social=time.time() < social_deadline))
        table.extend(flat_rows(rec))
        slim_records.append(slim(rec))
        if is_event:
            with open(os.path.join(out_dir, "events", f"{rec['id']}.json"), "w") as f:
                json.dump(rec, f, default=str)
        if n % 50 == 0:
            logging.info("collected %d of %d windows", n + 1, len(order))

    meta = {"collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "stocks_requested": len(tickers),
            "stocks_with_prices": found["scanned"], "triplers": len(events), "controls": len(controls),
            "multiple": 3.0, "horizon_days": HORIZON, "pre_window_days": PRE_WINDOW, "hourly_reach_from": reach,
            "minutes": round((time.time() - started) / 60, 1)}
    with open(os.path.join(out_dir, "dataset.json"), "w") as f:
        json.dump({"meta": meta, "records": slim_records}, f, default=str)
    pd.DataFrame(table).to_csv(os.path.join(out_dir, "readings.csv.gz"), index=False, compression="gzip")
    return meta
