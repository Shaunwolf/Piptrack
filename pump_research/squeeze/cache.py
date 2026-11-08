"""Small on-disk cache for downloaded files (historical files never change; live ones expire)"""

import hashlib
import logging
import os
import time
from typing import Optional

import requests

USER_AGENT = os.environ.get("SEC_USER_AGENT") or "PipSqueak research (set SEC_USER_AGENT to 'Name email')"


def cache_dir() -> str:
    base = os.environ.get("APP_WRITABLE_DIR") or ("/tmp" if os.environ.get("VERCEL") else ".cache")
    path = os.path.join(base, "squeeze")
    os.makedirs(path, exist_ok=True)
    return path


class Missing(Exception):
    """The file does not exist (holiday, not published yet, or before the archive starts)"""


def fetch(url: str, max_age: Optional[float] = None, timeout: float = 30, headers: Optional[dict] = None) -> bytes:
    """GET with a disk cache. max_age=None keeps the file forever (historical data); 404s are cached for a day."""
    key = hashlib.sha1(url.encode()).hexdigest()
    path = os.path.join(cache_dir(), key)
    miss = path + ".missing"
    now = time.time()
    if os.path.exists(path) and (max_age is None or now - os.path.getmtime(path) < max_age):
        with open(path, "rb") as f:
            return f.read()
    if os.path.exists(miss) and now - os.path.getmtime(miss) < 86400:
        raise Missing(url)
    r = requests.get(url, headers={"User-Agent": USER_AGENT, **(headers or {})}, timeout=timeout)
    if r.status_code in (403, 404):
        if r.status_code == 404:
            open(miss, "w").close()
            raise Missing(url)
        raise PermissionError(f"403 from {url}")
    r.raise_for_status()
    try:
        with open(path, "wb") as f:
            f.write(r.content)
    except OSError as e:
        logging.info("could not cache %s: %s", url, e)
    return r.content


def cached_json(key: str, max_age: Optional[float], produce):
    """Return the cached JSON value for key, or call produce() and cache what it returns"""
    import json
    path = os.path.join(cache_dir(), hashlib.sha1(key.encode()).hexdigest() + ".json")
    if os.path.exists(path) and (max_age is None or time.time() - os.path.getmtime(path) < max_age):
        try:
            with open(path) as f:
                return json.load(f)
        except (OSError, ValueError):
            pass
    value = produce()
    try:
        with open(path, "w") as f:
            json.dump(value, f, default=str)
    except OSError:
        pass
    return value
