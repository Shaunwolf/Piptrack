"""Tripler Lab: historical overlays, live-chart analogs, event charts with Fibonacci/Gann tools, 3D views"""

import os
import re

from flask import Blueprint, abort, jsonify, render_template, request
from flask_login import login_required

from pump_research.remote_data import ensure_remote_data, github_branch_tarball
from pump_research.triplers import overlay

tripler_bp = Blueprint("triplers", __name__)
TICKER_RE = re.compile(r"^[A-Z0-9.\-]{1,10}$")
TFS = ("1d", "4h", "1h")


def _tf(value):
    return value if value in TFS else "1d"


def data_dir():
    """tripler_data/ locally; on Vercel, the tripler-data branch downloaded into /tmp (refreshed hourly)"""
    default = "/tmp/tripler_data" if os.environ.get("VERCEL") else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "tripler_data")
    path = os.environ.get("TRIPLER_DATA_DIR", default)
    url = os.environ.get("TRIPLER_DATA_URL") or (github_branch_tarball(
        os.environ.get("VERCEL_GIT_REPO_OWNER") or "Shaunwolf", os.environ.get("VERCEL_GIT_REPO_SLUG") or "Piptrack",
        "tripler-data") if os.environ.get("VERCEL") else "")
    if url:
        ensure_remote_data(path, url, marker="dataset.json")
    return path


@tripler_bp.route("/pump-research/triplers")
@login_required
def page():
    data = overlay.load(data_dir())
    analysis = (data or {}).get("analysis") or {}
    top = [r for r in analysis.get("comparison", []) if r.get("q", 1) <= 0.10][:24]
    return render_template("triplers/index.html", data=data, meta=(data or {}).get("meta", {}), top=top,
                           learned=analysis.get("learned") or {}, multi=(analysis.get("multi_timeframe") or [])[:12],
                           matrix=overlay.lift_matrix(analysis))


@tripler_bp.route("/api/pump-research/triplers/overlay")
@login_required
def api_overlay():
    data = overlay.load(data_dir())
    if data is None:
        return jsonify({"error": "no tripler data collected yet"}), 404
    return jsonify(overlay.overlay_data(data, _tf(request.args.get("tf"))))


@tripler_bp.route("/api/pump-research/triplers/match/<ticker>")
@login_required
def api_match(ticker):
    ticker = ticker.upper()
    if not TICKER_RE.match(ticker):
        return jsonify({"error": "invalid ticker"}), 400
    tf = _tf(request.args.get("tf"))
    data = overlay.load(data_dir())
    if data is None:
        return jsonify({"error": "no tripler data collected yet"}), 404
    df = overlay.live_closes(ticker, tf)
    if df is None or len(df) < 30:
        return jsonify({"error": f"no {tf} prices for {ticker}"}), 502
    closes = [float(x) for x in df["close"].iloc[-80:]]
    res = overlay.analogs(data, closes, tf)
    last = closes[-1]
    res.update(ticker=ticker, as_of=str(df.index[-1])[:16],
               live={"offset": list(range(-len(closes) + 1, 1)), "close": [round(c / last, 4) for c in closes]})
    return jsonify(res)


@tripler_bp.route("/pump-research/triplers/event/<event_id>")
@login_required
def event(event_id):
    rec = overlay.load_event(data_dir(), event_id)
    if rec is None:
        abort(404)
    tf = _tf(request.args.get("tf"))
    tools = [t for t in request.args.getlist("tool") if t in overlay.TOOL_GROUPS] or ["spiral", "gann_fan"]
    chart = overlay.event_chart(rec, tf, tools)
    if chart is None and tf != "1d":
        tf, chart = "1d", overlay.event_chart(rec, "1d", tools)
    return render_template("triplers/event.html", rec=rec, tf=tf, tools=tools, chart=chart,
                           tool_names=list(overlay.TOOL_GROUPS), available=rec.get("timeframes") or ["1d"])
