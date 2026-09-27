"""Shared HTTP handling so every source reports network problems the same way"""

import requests

from ..models import SourceResult, OK, NO_DATA, BLOCKED, ERROR


class SourceBlocked(Exception):
    pass


def http_get_json(url, params=None, headers=None, timeout=20):
    """GET a JSON endpoint, raising SourceBlocked when the host can't be reached"""
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
    except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError,
            requests.exceptions.SSLError, requests.exceptions.Timeout) as e:
        raise SourceBlocked(f"{url.split('/')[2]} unreachable: {type(e).__name__}")
    if resp.status_code in (401, 403) and "proxy" in resp.text.lower():
        raise SourceBlocked(f"{url.split('/')[2]} blocked by network policy")
    resp.raise_for_status()
    return resp.json()


class DataSource:
    """Base class: subclasses implement _fetch and return a list of records"""
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
        return SourceResult(self.name, OK if records else NO_DATA, records=records)

    def _fetch(self, ticker, start, end, **kwargs):
        raise NotImplementedError
