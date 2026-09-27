"""Web pages for the pump research toolkit: dashboard, per-event dossiers and a live ticker scan"""

import json
import os
import re

from flask import Blueprint, abort, jsonify, render_template, request
from flask_login import login_required

from pump_research.analysis import analyze
from pump_research.charts import price_chart, countdown_chart
from pump_research.config import Settings
from pump_research.model import analyze_ticker, load_model
from pump_research.sources import default_price_sources

pump_bp = Blueprint("pump_research", __name__)
TICKER_RE = re.compile(r"^[A-Z0-9.\-]{1,10}$")


def _settings():
    s = Settings()
    s.data_dir = os.environ.get("PUMP_DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "pump_data"))
    return s


def _load_records(settings):
    path = os.path.join(settings.data_dir, "pump_dataset.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _load_model(settings):
    try:
        return load_model(settings)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


@pump_bp.route("/pump-research")
@login_required
def dashboard():
    settings = _settings()
    records = _load_records(settings)
    if records is None:
        return render_template("pump_research/dashboard.html", records=None, settings=settings)
    result = analyze(records)
    return render_template("pump_research/dashboard.html", records=records, result=result, settings=settings,
                           model=_load_model(settings),
                           countdown_fig=countdown_chart(result["countdown"]) if result["countdown"] else None)


@pump_bp.route("/pump-research/event/<event_id>")
@login_required
def event(event_id):
    records = _load_records(_settings()) or []
    rec = next((r for r in records if r["id"] == event_id), None)
    if rec is None:
        abort(404)
    ev = rec.get("event") or {}
    fig = price_chart(rec.get("price_history", []), rec.get("technicals"), rec.get("window_dates"),
                      ev.get("pump_date"), f"{rec['seed']['ticker']} around the pump")
    return render_template("pump_research/event.html", rec=rec, ev=ev, fig=fig)


def _scan(ticker):
    settings = _settings()
    return analyze_ticker(ticker, settings, default_price_sources(settings), _load_model(settings))


@pump_bp.route("/pump-research/scan")
@login_required
def scan():
    ticker = (request.args.get("ticker") or "").strip().upper()
    if not ticker:
        return render_template("pump_research/scan.html", res=None, ticker="")
    if not TICKER_RE.match(ticker):
        return render_template("pump_research/scan.html", res={"ticker": ticker, "error": "invalid ticker", "sources": []}, ticker=ticker)
    res = _scan(ticker)
    fig = None if "error" in res else price_chart(res["prices"], res["technicals"], title=f"{ticker} — last 180 sessions")
    return render_template("pump_research/scan.html", res=res, ticker=ticker, fig=fig)


@pump_bp.route("/api/pump-research/scan/<ticker>")
@login_required
def api_scan(ticker):
    ticker = ticker.upper()
    if not TICKER_RE.match(ticker):
        return jsonify({"error": "invalid ticker"}), 400
    res = _scan(ticker)
    res.pop("prices", None)
    return jsonify(res), (502 if "error" in res else 200)
