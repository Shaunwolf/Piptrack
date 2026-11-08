"""Serverless (Vercel) behaviour: writable paths, database URL, remote research data"""

import importlib
import io
import json
import os
import tarfile
import time

import pytest

import runtime_env
from pump_research import remote_data


def reload_env(monkeypatch, **env):
    for key in ("VERCEL", "APP_WRITABLE_DIR", "DATABASE_URL", "POSTGRES_URL", "DISABLE_BACKGROUND_SCANNER"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return importlib.reload(runtime_env)


def test_runtime_env_on_vercel(monkeypatch):
    env = reload_env(monkeypatch, VERCEL="1")
    assert env.WRITABLE_DIR == "/tmp"
    assert env.database_url() == "sqlite:////tmp/pipsqueak.db"
    assert not env.background_threads_allowed()
    env = reload_env(monkeypatch, VERCEL="1", POSTGRES_URL="postgres://u:p@host/db?sslmode=require")
    assert env.database_url() == "postgresql://u:p@host/db?sslmode=require"
    env = reload_env(monkeypatch)
    assert env.WRITABLE_DIR == "." and env.database_url() == "sqlite:///pipsqueak.db" and env.background_threads_allowed()
    reload_env(monkeypatch, DISABLE_BACKGROUND_SCANNER="1")


def make_tarball(files):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


class FakeResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


def test_remote_data_downloads_refreshes_and_rejects_escapes(tmp_path, monkeypatch):
    calls = []
    payload = make_tarball({"Piptrack-pump-data/pump_dataset.json": json.dumps([{"id": "A"}]),
                            "Piptrack-pump-data/events/A.json": "{}",
                            "Piptrack-pump-data/../../evil.txt": "x"})
    monkeypatch.setattr(remote_data.requests, "get", lambda url, timeout: calls.append(url) or FakeResponse(payload))
    data_dir = str(tmp_path / "pump_data")
    assert remote_data.ensure_remote_data(data_dir, "https://example.test/x.tar.gz")
    assert json.load(open(os.path.join(data_dir, "pump_dataset.json"))) == [{"id": "A"}]
    assert os.path.exists(os.path.join(data_dir, "events", "A.json"))
    assert not (tmp_path.parent / "evil.txt").exists() and not (tmp_path / "evil.txt").exists()
    # Fresh copy: no second download
    assert remote_data.ensure_remote_data(data_dir, "https://example.test/x.tar.gz") and len(calls) == 1
    # Stale copy: downloads again; a failed download keeps the old copy
    old = time.time() - 7200
    os.utime(os.path.join(data_dir, remote_data.MARKER), (old, old))

    def fail(url, timeout):
        raise remote_data.requests.ConnectionError("offline")
    monkeypatch.setattr(remote_data.requests, "get", fail)
    assert remote_data.ensure_remote_data(data_dir, "https://example.test/x.tar.gz")
    assert os.path.exists(os.path.join(data_dir, "pump_dataset.json"))


def test_remote_data_unavailable_without_a_copy(tmp_path, monkeypatch):
    def fail(url, timeout):
        raise remote_data.requests.ConnectionError("offline")
    monkeypatch.setattr(remote_data.requests, "get", fail)
    assert not remote_data.ensure_remote_data(str(tmp_path / "none"), "https://example.test/x.tar.gz")


def test_vercel_data_url_and_integration_config(monkeypatch, tmp_path):
    import pump_routes
    from pump_research.integrations import base
    monkeypatch.delenv("PUMP_DATA_URL", raising=False)
    monkeypatch.delenv(base.CONFIG_ENV, raising=False)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_GIT_REPO_OWNER", "someone")
    monkeypatch.setenv("VERCEL_GIT_REPO_SLUG", "fork")
    assert pump_routes._data_url() == "https://codeload.github.com/someone/fork/tar.gz/refs/heads/pump-data"
    assert base.config_path() == "/tmp/integrations.json"
    monkeypatch.delenv("VERCEL")
    assert pump_routes._data_url() == "" and base.config_path() == base.DEFAULT_CONFIG


def test_vercel_entrypoint_is_configured():
    tomllib = pytest.importorskip("tomllib")
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "pyproject.toml"), "rb") as f:
        config = tomllib.load(f)
    module, _, attr = config["tool"]["vercel"]["entrypoint"].partition(":")
    assert attr == "app" and os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), f"{module}.py"))
