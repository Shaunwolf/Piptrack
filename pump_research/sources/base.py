"""Shared HTTP handling so every source reports network problems the same way"""

import time

import requests

from ..models import SourceResult, OK, NO_DATA, BLOCKED, ERROR, PARTIAL


class SourceBlocked(Exception):
    pass


DEFAULT_HEADERS = {"User-Agent": "PipSqueak-pump-research/1.0 (+https://github.com/Shaunwolf/Piptrack)",
                   "Accept": "application/json"}


RETRY_STATUSES = (429, 502, 503, 504)
MAX_RETRIES = 4


def http_get_json(url, params=None, headers=None, timeout=20, sleep=time.sleep):
    """GET a JSON endpoint, retrying rate limits, and raising SourceBlocked when the host can't be reached"""
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, headers={**DEFAULT_HEADERS, **(headers or {})}, timeout=timeout)
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError,
                requests.exceptions.SSLError, requests.exceptions.Timeout) as e:
            raise SourceBlocked(f"{url.split('/')[2]} unreachable: {type(e).__name__}")
        if resp.status_code not in RETRY_STATUSES or attempt == MAX_RETRIES:
            break
        retry_after = resp.headers.get("Retry-After", "")
        sleep(min(60, float(retry_after)) if retry_after.replace(".", "", 1).isdigit() else 2 ** (attempt + 1))
    if resp.status_code in (401, 403) and "proxy" in resp.text.lower():
        raise SourceBlocked(f"{url.split('/')[2]} blocked by network policy")
    if resp.status_code >= 400:
        # Include the start of the body: APIs usually explain refusals there
        snippet = " ".join(resp.text.split())[:200]
        raise requests.HTTPError(f"{resp.status_code} from {url.split('?')[0]}: {snippet}", response=resp)
    return resp.json()


class Partial(list):
    """Records returned by a source that stopped at a result cap"""

    def __init__(self, records, detail=""):
        super().__init__(records)
        self.detail = detail


class DataSource:
    """Base class: subclasses implement _fetch and return a list of records (or Partial when capped)"""
    name = "base"

    def __init__(self, settings):
        self.settings = settings

    def fetch(self, ticker, start, end, **kwargs):
        try:
            records = self._fetch(ticker, start, end, **kwargs)
        except SourceBlocked as e:
            return SourceResult(self.name, BLOCKED, detail=str(e))
        except Exception as e:
            return SourceResult(self.name, ERROR, detail=f"{type(e).__name__}: {e}")
        if isinstance(records, SourceResult):
            return records
        if isinstance(records, Partial):
            return SourceResult(self.name, PARTIAL, records=list(records), detail=records.detail)
        return SourceResult(self.name, OK if records else NO_DATA, records=records)

    def _fetch(self, ticker, start, end, **kwargs):
        raise NotImplementedError
