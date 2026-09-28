"""SEC EDGAR filings made during the window (offerings, 8-Ks, insider trades, ownership changes)"""

from datetime import date

from .base import DataSource, http_get_json
from ..models import SourceResult, SKIPPED

# What each form type tells us about pre-pump activity
FORM_GROUPS = {
    "offering": ("S-1", "S-1/A", "F-1", "F-1/A", "S-3", "S-3/A", "F-3", "424B1", "424B3", "424B4", "424B5", "EFFECT"),
    "material_event": ("8-K", "8-K/A", "6-K"),
    "insider": ("3", "4", "5"),
    "ownership": ("SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"),
    "periodic": ("10-K", "10-Q", "20-F", "10-K/A", "10-Q/A"),
}


def form_group(form):
    for group, forms in FORM_GROUPS.items():
        if form in forms:
            return group
    return "other"


class SecEdgarFilings(DataSource):
    name = "sec_filings"
    _ticker_map = None

    def _headers(self):
        return {"User-Agent": self.settings.sec_user_agent}

    def _cik(self, ticker):
        # company_tickers.json only lists currently registered tickers
        if SecEdgarFilings._ticker_map is None:
            data = http_get_json("https://www.sec.gov/files/company_tickers.json",
                                 headers=self._headers(), timeout=self.settings.request_timeout)
            SecEdgarFilings._ticker_map = {v["ticker"].upper(): v["cik_str"] for v in data.values()}
        return SecEdgarFilings._ticker_map.get(ticker.upper())

    def _fetch(self, ticker, start, end, cik=None, **kwargs):
        cik = cik or self._cik(ticker)
        if not cik:
            # Delisted/renamed tickers drop out of SEC's current list: that's unknown, not "no filings"
            return SourceResult(self.name, SKIPPED,
                                detail=f"{ticker} isn't in SEC's current ticker list; add its CIK to seeds.csv")
        data = http_get_json(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json",
                             headers=self._headers(), timeout=self.settings.request_timeout)
        filings = data.get("filings", {})
        pages = [filings.get("recent", {})]
        # The main response only holds the most recent ~1,000 filings; older ones live in extra files
        for extra in filings.get("files", []):
            if extra.get("filingFrom", "9999") <= end.isoformat() and extra.get("filingTo", "0000") >= start.isoformat():
                pages.append(http_get_json(f"https://data.sec.gov/submissions/{extra['name']}",
                                           headers=self._headers(), timeout=self.settings.request_timeout))
        records = []
        for page in pages:
            for form, filed, acc, doc, desc in zip(page.get("form", []), page.get("filingDate", []),
                                                   page.get("accessionNumber", []),
                                                   page.get("primaryDocument", []),
                                                   page.get("primaryDocDescription", [])):
                if start <= date.fromisoformat(filed) <= end:
                    records.append({
                        "date": filed, "form": form, "group": form_group(form), "description": desc,
                        "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{doc}",
                    })
        return sorted(records, key=lambda r: r["date"])
