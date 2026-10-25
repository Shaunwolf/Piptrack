"""
Download the published research data (the repo's `pump-data` branch) at runtime.

Hosts that deploy only the code, such as Vercel, don't have pump_data/ in their checkout.
The collection workflow publishes results to the pump-data branch; this fetches that branch
as a tarball into a writable folder and refreshes it at most once per `max_age` seconds, so
a new collection shows up without redeploying.
"""

import io
import logging
import os
import shutil
import tarfile
import tempfile
import threading
import time

import requests

MARKER = ".fetched_at"
_LOCK = threading.Lock()


def github_branch_tarball(owner: str, repo: str, branch: str = "pump-data") -> str:
    return f"https://codeload.github.com/{owner}/{repo}/tar.gz/refs/heads/{branch}"


def _fresh(data_dir: str, max_age: float) -> bool:
    try:
        return time.time() - os.path.getmtime(os.path.join(data_dir, MARKER)) < max_age
    except OSError:
        return False


def _extract(content: bytes, dest: str):
    """Extract a GitHub tarball (one top-level folder) into dest, refusing paths that escape it"""
    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as tar:
        for member in tar.getmembers():
            parts = member.name.split("/", 1)
            if len(parts) < 2 or not parts[1] or not (member.isfile() or member.isdir()):
                continue
            rel = os.path.normpath(parts[1])
            if rel.startswith("..") or os.path.isabs(rel):
                continue
            target = os.path.join(dest, rel)
            if member.isdir():
                os.makedirs(target, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with tar.extractfile(member) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)


def ensure_remote_data(data_dir: str, url: str, max_age: float = 3600, timeout: float = 20) -> bool:
    """Make sure data_dir holds a recent copy of the data at url. Returns whether data is available."""
    if _fresh(data_dir, max_age):
        return True
    with _LOCK:
        if _fresh(data_dir, max_age):
            return True
        have_old = os.path.exists(os.path.join(data_dir, "pump_dataset.json"))
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
        except (requests.RequestException, OSError) as e:  # network or TLS setup failures
            logging.warning("Could not download pump data from %s: %s", url, e)
            return have_old
        parent = os.path.dirname(os.path.abspath(data_dir))
        os.makedirs(parent, exist_ok=True)
        staging = tempfile.mkdtemp(dir=parent, prefix=".pump_data_")
        try:
            _extract(response.content, staging)
            open(os.path.join(staging, MARKER), "w").close()
            old = data_dir + ".old"
            shutil.rmtree(old, ignore_errors=True)
            if os.path.exists(data_dir):
                os.rename(data_dir, old)
            os.rename(staging, data_dir)
            shutil.rmtree(old, ignore_errors=True)
        except (OSError, tarfile.TarError) as e:
            logging.warning("Could not unpack pump data from %s: %s", url, e)
            shutil.rmtree(staging, ignore_errors=True)
            return have_old
        return True
