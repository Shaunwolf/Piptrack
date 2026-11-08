"""Every US-listed common stock, from Nasdaq Trader's symbol directory (Nasdaq, NYSE, NYSE American, Arca, Cboe)"""

import csv
import io
import logging
import re
from typing import List

from ..squeeze.cache import cached_json, fetch

NASDAQ_LISTED = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
# Plain common-stock symbols only: units, warrants, rights and preferreds carry suffixes (ABCDW, ABC.U, ABC$A)
COMMON = re.compile(r"^[A-Z]{1,5}$")
NOT_COMMON = re.compile(r"\b(warrants?|units?|rights?|preferred|notes due|debentures)\b", re.I)


def parse_directory(text: str, symbol_field: str) -> List[str]:
    rows = csv.DictReader(io.StringIO(text), delimiter="|")
    out = []
    for r in rows:
        sym = (r.get(symbol_field) or "").strip()
        if not sym or sym.startswith("File Creation Time"):
            continue
        if (r.get("ETF") or "N").strip() == "Y" or (r.get("Test Issue") or "N").strip() == "Y":
            continue
        if not COMMON.match(sym) or NOT_COMMON.search(r.get("Security Name") or ""):
            continue
        out.append(sym)
    return out


def listed_tickers(max_age: float = 86400) -> List[str]:
    """Today's listed common stocks (about 5–6 thousand). Delisted stocks are not included (survivorship bias)."""
    def produce():
        out = set()
        for url, field in ((NASDAQ_LISTED, "Symbol"), (OTHER_LISTED, "ACT Symbol")):
            try:
                out.update(parse_directory(fetch(url, max_age=max_age, timeout=30).decode("utf-8", "replace"), field))
            except Exception as e:  # one exchange file failing still leaves the other
                logging.warning("symbol directory %s unavailable: %s", url, e)
        return sorted(out)
    return cached_json("listed_tickers", max_age, produce)
