"""
Free squeeze data, all cached on disk:

- FINRA daily short volume (Reg SHO files). Consolidated CNMS file from Aug 2018; before that the
  Nasdaq (FNSQ) and NYSE (FNYX) facility files are summed. Off-exchange short volume is mostly market
  makers filling buy orders, so a high ratio is read as hidden buying pressure (the stock-level
  cousin of SqueezeMetrics' DIX) and is noisy on its own.
- Reg SHO threshold lists (securities with persistent fails-to-deliver). Nasdaq publishes a daily
  file; NYSE is tried too. Rule 203(b)(3) forces close-outs after 13 consecutive settlement days.
- FINRA consolidated short interest (twice a month, history via FINRA's public query API).
- ApeWisdom Reddit/StockTwits mention counts (now vs 24 hours ago): mention velocity.
- SEC fails-to-deliver (twice-monthly archives; SEC blocks most cloud traffic without a real contact).
- Yahoo: float, short % of float, days to cover, exchange and market cap.
"""

import io
import json
import logging
import zipfile
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional

import pandas as pd
import requests

from .cache import Missing, cached_json, fetch

FINRA = "https://cdn.finra.org/equity/regsho/daily"
CNMS_START = date(2018, 8, 1)
DAY = 86400


def _is_live(d: date) -> bool:
    return (date.today() - d).days <= 3


def _parse_pipe(text: str) -> pd.DataFrame:
    lines = [ln for ln in text.splitlines() if "|" in ln]
    if len(lines) < 2:
        return pd.DataFrame()
    return pd.read_csv(io.StringIO("\n".join(lines)), sep="|", dtype=str, keep_default_na=False)


# --- FINRA daily short volume -------------------------------------------------------------------------------

def short_volume_day(d: date) -> Dict[str, tuple]:
    """{ticker: (short_volume, total_volume)} for one trading day ({} if FINRA has no file)"""
    files = ["CNMS"] if d >= CNMS_START else ["FNSQ", "FNYX"]
    out: Dict[str, list] = {}
    for prefix in files:
        try:
            raw = fetch(f"{FINRA}/{prefix}shvol{d:%Y%m%d}.txt", max_age=DAY if _is_live(d) else None)
        except (Missing, PermissionError):
            continue
        df = _parse_pipe(raw.decode("utf-8", "replace"))
        if df.empty:
            continue
        for sym, sv, tv in zip(df["Symbol"], pd.to_numeric(df["ShortVolume"], errors="coerce"),
                               pd.to_numeric(df["TotalVolume"], errors="coerce")):
            cur = out.setdefault(sym, [0.0, 0.0])
            cur[0] += sv or 0
            cur[1] += tv or 0
    return {k: tuple(v) for k, v in out.items()}


def short_volume_ratios(tickers: Iterable[str], days: List[date]) -> Dict[str, List[Optional[float]]]:
    """Short-volume ratio per ticker for each day (None where FINRA has no row)"""
    tickers = list(tickers)
    out = {t: [] for t in tickers}
    for d in days:
        day = short_volume_day(d)
        for t in tickers:
            sv = day.get(t)
            out[t].append(sv[0] / sv[1] if sv and sv[1] > 0 else None)
    return out


# --- Reg SHO threshold lists ------------------------------------------------------------------------------------

def threshold_list(d: date) -> Optional[set]:
    """Tickers on a threshold list that day; None when no list was published (holiday, weekend, unavailable)"""
    found, any_file = set(), False
    urls = [f"https://www.nasdaqtrader.com/dynamic/symdir/regsho/nasdaqth{d:%Y%m%d}.txt",
            f"https://www.nyse.com/api/regulatory/threshold-securities/download?selectedDate={d:%d-%b-%Y}&market=NYSE"]
    for url in urls:
        try:
            raw = fetch(url, max_age=DAY if _is_live(d) else None)
        except (Missing, PermissionError, requests.RequestException):
            continue
        df = _parse_pipe(raw.decode("utf-8", "replace"))
        if "Symbol" not in df:
            continue
        any_file = any_file or "nasdaqtrader" in url
        flag = df.get("Reg SHO Threshold Flag")
        syms = df["Symbol"][flag == "Y"] if flag is not None else df["Symbol"]
        found |= {s.strip().upper() for s in syms if s.strip()}
    return found if any_file else None


def threshold_streaks(asof: date, lookback: int = 30) -> Dict[str, int]:
    """Consecutive published trading days each ticker has been on the threshold list, ending at `asof`"""
    lists = []
    d = asof
    while len(lists) < lookback and (asof - d).days < lookback * 2:
        if d.weekday() < 5:
            lst = threshold_list(d)
            if lst is not None:
                lists.append(lst)
        d -= timedelta(days=1)
    if not lists:
        return {}
    streak = {}
    for t in lists[0]:
        n = 0
        for lst in lists:
            if t not in lst:
                break
            n += 1
        streak[t] = n
    return streak


# --- FINRA short interest --------------------------------------------------------------------------------------

def short_interest_history(ticker: str) -> List[Dict]:
    """Twice-monthly short interest from FINRA's public query API, oldest first"""
    def produce():
        r = requests.post("https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest",
                          json={"limit": 5000, "compareFilters": [{"compareType": "EQUAL", "fieldName": "symbolCode",
                                                                   "fieldValue": ticker.upper()}]},
                          headers={"Accept": "application/json"}, timeout=30)
        r.raise_for_status()
        rows = [{"date": x["settlementDate"], "short": float(x.get("currentShortPositionQuantity") or 0),
                 "days_to_cover": float(x.get("daysToCoverQuantity") or 0),
                 "avg_volume": float(x.get("averageDailyVolumeQuantity") or 0),
                 "change_pct": float(x.get("changePercent") or 0)} for x in (r.json() or [])]
        return sorted(rows, key=lambda x: x["date"])
    return cached_json(f"finra_si_{ticker.upper()}", DAY, produce)


def short_interest_asof(history: List[Dict], asof: date) -> Optional[Dict]:
    """The latest report settled on or before `asof` (FINRA publishes ~7 business days after settlement)"""
    cutoff = (asof - timedelta(days=9)).isoformat()
    prior = [h for h in history if h["date"] <= cutoff]
    return prior[-1] if prior else None


# --- Social mention velocity -----------------------------------------------------------------------------------------

def mention_velocity(pages: int = 3) -> Dict[str, Dict]:
    """{ticker: {mentions, mentions_24h_ago, rank, rank_24h_ago, upvotes}} from ApeWisdom (Reddit + StockTwits)"""
    out = {}
    for page in range(1, pages + 1):
        try:
            raw = fetch(f"https://apewisdom.io/api/v1.0/filter/all-stocks/page/{page}", max_age=3600)
        except Exception as e:
            logging.info("ApeWisdom unavailable: %s", e)
            break
        data = json.loads(raw)
        for r in data.get("results", []):
            out[r["ticker"].upper()] = {k: (float(r[k]) if r.get(k) not in (None, "") else None)
                                        for k in ("mentions", "mentions_24h_ago", "rank", "rank_24h_ago", "upvotes")}
        if page >= int(data.get("pages") or 1):
            break
    return out


# --- SEC fails-to-deliver -------------------------------------------------------------------------------------------------

def ftd_month_half(year: int, month: int, half: str) -> Dict[str, Dict[str, float]]:
    """{ticker: {settlement_date: fails}} from one SEC archive (half 'a' = 1st-15th, 'b' = rest)"""
    raw = fetch(f"https://www.sec.gov/files/data/fails-deliver-data/cnsfails{year}{month:02d}{half}.zip")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        text = z.read(z.namelist()[0]).decode("latin-1")
    df = _parse_pipe(text)
    out: Dict[str, Dict[str, float]] = {}
    for d, sym, q in zip(df.get("SETTLEMENT DATE", []), df.get("SYMBOL", []), pd.to_numeric(df.get("QUANTITY (FAILS)", []), errors="coerce")):
        out.setdefault(sym.strip().upper(), {})[f"{d[:4]}-{d[4:6]}-{d[6:]}"] = float(q or 0)
    return out


# --- Yahoo fundamentals for squeezes -------------------------------------------------------------------------------------------

def float_and_short(ticker: str) -> Dict:
    """Float, short % of float, days to cover, exchange and size from Yahoo (cached for a day)"""
    def produce():
        import yfinance as yf
        info = yf.Ticker(ticker).info or {}
        return {k: info.get(k) for k in ("sharesShort", "shortPercentOfFloat", "shortRatio", "floatShares", "sharesOutstanding",
                                         "sharesShortPriorMonth", "exchange", "quoteType", "marketCap", "averageVolume")}
    return cached_json(f"yfinfo_{ticker.upper()}", DAY, produce)
