"""
What a scan runs over: S&P 500 companies by GICS sector, themed lists, and custom tickers.

S&P 500 membership and sectors come from the open datasets/s-and-p-500-companies list
(snapshot in sp500.csv). Themed lists are hand-picked and may include tickers that later
change or delist; the runner reports those as missing rather than failing.
"""

import csv
import os
import re
from typing import Dict, List

HERE = os.path.dirname(__file__)
TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9.\-^=]{0,11}$")


def _load_sp500():
    with open(os.path.join(HERE, "sp500.csv"), newline="") as f:
        return list(csv.DictReader(f))


SP500 = _load_sp500()
SECTORS: Dict[str, List[str]] = {}
NAMES: Dict[str, str] = {}
SECTOR_OF: Dict[str, str] = {}
for row in SP500:
    SECTORS.setdefault(row["sector"], []).append(row["ticker"])
    NAMES[row["ticker"]] = row["name"]
    SECTOR_OF[row["ticker"]] = row["sector"]


def _seed_tickers():
    path = os.path.join(os.path.dirname(HERE), "seeds.csv")
    try:
        with open(path, newline="") as f:
            return sorted({(r.get("price_ticker") or r["ticker"]).strip().upper() for r in csv.DictReader(f)})
    except OSError:
        return []


LISTS: Dict[str, Dict] = {
    "meme": {"title": "Meme & retail favourites", "theme": "Retail momentum",
             "tickers": ["GME", "AMC", "KOSS", "BB", "NOK", "PLTR", "SOFI", "HOOD", "CLOV", "SPCE", "DJT", "RDDT", "LCID",
                         "RIVN", "NIO", "PLUG", "OPEN", "UPST", "AFRM", "SNAP", "RBLX", "CHWY", "BYND", "TLRY", "SNDL", "FUBO"]},
    "crypto": {"title": "Crypto miners & fintech", "theme": "Crypto",
               "tickers": ["COIN", "MSTR", "MARA", "RIOT", "CLSK", "HUT", "BITF", "CIFR", "WULF", "IREN", "HOOD", "SQ", "PYPL"]},
    "pump_history": {"title": "Historic pump stocks", "theme": "From the pump research list", "tickers": _seed_tickers()},
    "sector_etfs": {"title": "Sector ETFs", "theme": "ETF",
                    "tickers": ["XLK", "XLF", "XLV", "XLE", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "SMH", "XBI", "KRE"]},
    "index_etfs": {"title": "Index ETFs", "theme": "ETF", "tickers": ["SPY", "QQQ", "IWM", "DIA", "VTI", "ARKK"]},
}


def clean_tickers(text_or_list) -> List[str]:
    items = re.split(r"[\s,;]+", text_or_list) if isinstance(text_or_list, str) else list(text_or_list or [])
    out = []
    for t in items:
        t = str(t).strip().upper().replace("$", "")
        if t and TICKER_RE.match(t) and t not in out:
            out.append(t)
    return out


def expand_universe(universe: Dict, limit: int = 600) -> Dict:
    """{'sectors': [...], 'lists': [...], 'tickers': [...]} → ordered tickers and a sector for each"""
    universe = universe if isinstance(universe, dict) else {}
    tickers, sector_of = [], {}
    for s in universe.get("sectors") or []:
        for t in SECTORS.get(s, []):
            if t not in sector_of:
                tickers.append(t)
                sector_of[t] = s
    for key in universe.get("lists") or []:
        lst = LISTS.get(key)
        for t in (lst or {}).get("tickers", []):
            if t not in sector_of:
                tickers.append(t)
                sector_of[t] = SECTOR_OF.get(t, lst["theme"])
    for t in clean_tickers(universe.get("tickers") or []):
        if t not in sector_of:
            tickers.append(t)
            sector_of[t] = SECTOR_OF.get(t, "Custom")
    return {"tickers": tickers[:limit], "sector_of": sector_of, "truncated": len(tickers) > limit}


def describe() -> Dict:
    return {"sectors": [{"name": s, "count": len(t)} for s, t in sorted(SECTORS.items())],
            "lists": [{"key": k, "title": v["title"], "count": len(v["tickers"])} for k, v in LISTS.items()]}
