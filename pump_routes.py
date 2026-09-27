"""Web pages for the pump research toolkit: dashboard, per-event dossiers and a live ticker scan"""

import json
import os
import re

from flask import Blueprint, abort, jsonify, render_template, request
from flask_login import login_required

from pump_research.analysis import analyze
from pump_research.charts import (price_chart, countdown_chart, tremor_scale, tremor_strip, gauge, seismograph, tells,
                                  pump_volume_ratio)
from pump_research.labels import feature_label, signal_label
from pump_research.config import Settings
from pump_research.model import analyze_ticker, load_model
from pump_research.sources import default_price_sources

pump_bp = Blueprint("pump_research", __name__)
pump_bp.add_app_template_global(feature_label)
pump_bp.add_app_template_global(signal_label)
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
    scale = tremor_scale(records)
    # Strongest pumps first; events without price data last
    ordered = sorted(records, key=lambda r: (r.get("event") is None, not r.get("qualifies"),
                                             -((r.get("event") or {}).get("high_multiple") or 0)))
    strips = {r["id"]: tremor_strip(r, scale) for r in records}
    pump_ratios = sorted(v for v in (pump_volume_ratio(r) for r in records) if v)
    return render_template("pump_research/dashboard.html", records=ordered, result=result, settings=settings,
                           model=_load_model(settings), strips=strips, tells=tells(result["feature_comparison"]),
                           bool_tells=[{**b, "label": feature_label(b["feature"])} for b in result.get("boolean_comparison", [])[:12]],
                           seismo=seismograph(result["countdown"], pump_ratios[len(pump_ratios) // 2] if pump_ratios else None),
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
    strip = tremor_strip(rec, tremor_scale([rec]), width=520, height=90)
    return render_template("pump_research/event.html", rec=rec, ev=ev, fig=fig, strip=strip)


def _scan(ticker):
    settings = _settings()
    return analyze_ticker(ticker, settings, default_price_sources(settings), _load_model(settings))


@pump_bp.route("/pump-research/scan")
@login_required
def scan():
    ticker = (request.args.get("ticker") or "").strip().upper()
    if not ticker:
        return render_template("pump_research/scan.html", res=None, ticker="", dial=gauge(None))
    if not TICKER_RE.match(ticker):
        return render_template("pump_research/scan.html", res={"ticker": ticker, "error": "invalid ticker", "sources": []},
                               ticker=ticker, dial=gauge(None))
    res = _scan(ticker)
    fig = None if "error" in res else price_chart(res["prices"], res["technicals"], title=f"{ticker} · last 180 sessions")
    score = (res.get("score") or {}).get("score")
    return render_template("pump_research/scan.html", res=res, ticker=ticker, fig=fig, dial=gauge(score))


@pump_bp.route("/api/pump-research/tools")
@login_required
def api_tools_list():
    from pump_research.toolkit import list_tools
    return jsonify(list_tools())


@pump_bp.route("/api/pump-research/tools/<ticker>")
@login_required
def api_tools(ticker):
    """Every tool (or ?tool=name, repeatable) on the ticker's latest prices"""
    from datetime import date, timedelta
    from pump_research.sources.prices import records_to_frame
    from pump_research.toolkit import run_all_tools, TOOLS, ALIASES
    ticker = ticker.upper()
    if not TICKER_RE.match(ticker):
        return jsonify({"error": "invalid ticker"}), 400
    wanted = request.args.getlist("tool") or None
    if wanted and any(ALIASES.get(t, t) not in TOOLS for t in wanted):
        return jsonify({"error": "unknown tool", "tools": sorted(TOOLS)}), 400
    settings = _settings()
    statuses = []
    for source in default_price_sources(settings):
        result = source.fetch(ticker, date.today() - timedelta(days=500), date.today())
        statuses.append({"source": result.source, "status": result.status, "detail": result.detail})
        if result.status == "ok":
            return jsonify({"ticker": ticker, **run_all_tools(records_to_frame(result.records), wanted)})
    return jsonify({"ticker": ticker, "error": "no price data", "sources": statuses}), 502


@pump_bp.route("/pump-research/integrations", methods=["GET", "POST"])
@login_required
def integrations_page():
    from flask import flash, redirect, url_for
    from flask_wtf.csrf import validate_csrf
    from pump_research.integrations import list_integrations, set_enabled
    if request.method == "POST":
        try:
            validate_csrf(request.form.get("csrf_token"))
        except Exception:
            abort(400)
        key = request.form.get("key", "")
        try:
            set_enabled(key, request.form.get("enabled") == "1")
        except KeyError:
            abort(404)
        flash(f"{key} {'enabled' if request.form.get('enabled') == '1' else 'disabled'}", "success")
        return redirect(url_for("pump_research.integrations_page"))
    return render_template("pump_research/integrations.html", integrations=list_integrations())


@pump_bp.route("/api/pump-research/integrations", methods=["GET"])
@login_required
def api_integrations():
    from pump_research.integrations import list_integrations
    return jsonify(list_integrations())


@pump_bp.route("/api/pump-research/integrations/<key>", methods=["POST"])
@login_required
def api_toggle_integration(key):
    from flask_wtf.csrf import validate_csrf
    from pump_research.integrations import set_enabled
    try:
        validate_csrf(request.headers.get("X-CSRFToken") or (request.get_json(silent=True) or {}).get("csrf_token"))
    except Exception:
        return jsonify({"error": "missing or invalid CSRF token"}), 400
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(set_enabled(key, bool(body.get("enabled"))))
    except KeyError:
        return jsonify({"error": "unknown integration"}), 404


@pump_bp.route("/api/pump-research/scan/<ticker>")
@login_required
def api_scan(ticker):
    ticker = ticker.upper()
    if not TICKER_RE.match(ticker):
        return jsonify({"error": "invalid ticker"}), 400
    res = _scan(ticker)
    res.pop("prices", None)
    return jsonify(res), (502 if "error" in res else 200)
