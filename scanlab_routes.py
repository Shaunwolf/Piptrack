"""Scan Lab: the drag-and-drop scanner page, its JSON API, saved scans and alerts"""

import hmac
import logging
import os
from datetime import datetime
from urllib.parse import urlparse

import requests
from flask import Blueprint, abort, jsonify, render_template, request
from flask_login import current_user, login_required

from app import db
from models import SavedScan, ScanAlert
from pump_research.scanlab import PRESETS, catalog, expand_universe, normalize_spec, run_scan
from pump_research.scanlab.runner import TIMEFRAMES
from pump_research.scanlab.universe import clean_tickers, describe

scanlab_bp = Blueprint("scanlab", __name__)

MAX_BATCH = 60          # tickers per /run request (the page sends a large universe in batches)
MAX_UNIVERSE = 600
WEBHOOK_HOSTS = {"discord.com", "discordapp.com", "hooks.slack.com"}


def _check_csrf():
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(request.headers.get("X-CSRFToken") or (request.get_json(silent=True) or {}).get("csrf_token"))
    except Exception:
        abort(400, description="missing or invalid CSRF token")


def _bad(message, code=400):
    return jsonify({"error": message}), code


def _model_and_settings():
    """The trained pump model (for the Pump DNA block), if one has been collected"""
    try:
        from pump_routes import _load_model, _settings
        settings = _settings()
        return _load_model(settings), settings
    except Exception as e:  # the scanner works without it; Pump DNA then reports "not loaded"
        logging.info("pump model unavailable for Scan Lab: %s", e)
        return None, None


def _clean_universe(raw):
    raw = raw if isinstance(raw, dict) else {}
    return {"sectors": [s for s in (raw.get("sectors") or []) if isinstance(s, str)][:20],
            "lists": [s for s in (raw.get("lists") or []) if isinstance(s, str)][:10],
            "tickers": clean_tickers(raw.get("tickers") or [])[:200]}


def _timeframe(value):
    return value if value in TIMEFRAMES else "1d"


def _valid_webhook(url):
    if not url:
        return None
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in WEBHOOK_HOSTS:
        raise ValueError("webhooks must be Discord or Slack https URLs")
    return url.strip()[:300]


# --- Page -------------------------------------------------------------------------------------------

@scanlab_bp.route("/scan-lab")
@login_required
def page():
    return render_template("scanlab/index.html")


# --- Catalog and scanning ------------------------------------------------------------------------------

@scanlab_bp.route("/api/scan-lab/catalog")
@login_required
def api_catalog():
    return jsonify({**catalog(), "presets": [{"key": k, "title": p["title"], "tagline": p["tagline"], "style": p["style"],
                                              "spec": p["spec"], "universe": p["universe"]} for k, p in PRESETS.items()],
                    "universe": describe(), "timeframes": [{"key": "1d", "title": "Daily"}, {"key": "1wk", "title": "Weekly"},
                                                           {"key": "1h", "title": "Hourly"}]})


@scanlab_bp.route("/api/scan-lab/universe", methods=["POST"])
@login_required
def api_universe():
    _check_csrf()
    u = expand_universe(_clean_universe((request.get_json(silent=True) or {}).get("universe")), limit=MAX_UNIVERSE)
    return jsonify(u)


@scanlab_bp.route("/api/scan-lab/run", methods=["POST"])
@login_required
def api_run():
    _check_csrf()
    body = request.get_json(silent=True) or {}
    try:
        spec = normalize_spec(body.get("spec"))
    except ValueError as e:
        return _bad(str(e))
    if body.get("tickers"):
        tickers = clean_tickers(body["tickers"])[:MAX_BATCH]
        sector_of = {t: str((body.get("sector_of") or {}).get(t, ""))[:60] for t in tickers}
    else:
        u = expand_universe(_clean_universe(body.get("universe")), limit=MAX_BATCH)
        tickers, sector_of = u["tickers"], u["sector_of"]
    if not tickers:
        return _bad("pick at least one sector, list or ticker to scan")
    model, settings = _model_and_settings()
    out = run_scan(spec, tickers, sector_of, timeframe=_timeframe(body.get("timeframe")), model=model, settings=settings,
                   include_misses=body.get("include_misses", True) is not False)
    return jsonify(out)


# --- Saved scans -----------------------------------------------------------------------------------------

def _own_scan(scan_id):
    scan = db.session.get(SavedScan, scan_id)
    if scan is None or scan.user_id != current_user.id:
        abort(404)
    return scan


def _apply(scan, body):
    if "name" in body:
        scan.name = (str(body.get("name") or "").strip() or "Untitled scan")[:80]
    if "spec" in body:
        scan.spec = normalize_spec(body["spec"])
    if "universe" in body:
        scan.universe = _clean_universe(body["universe"])
    if "timeframe" in body:
        scan.timeframe = _timeframe(body["timeframe"])
    if "alert_enabled" in body:
        scan.alert_enabled = bool(body["alert_enabled"])
    if "alert_min_score" in body:
        scan.alert_min_score = max(0.0, min(100.0, float(body.get("alert_min_score") or 0)))
    if "alert_new_only" in body:
        scan.alert_new_only = bool(body["alert_new_only"])
    if "alert_webhook" in body:
        scan.alert_webhook = _valid_webhook(body.get("alert_webhook"))


@scanlab_bp.route("/api/scan-lab/scans", methods=["GET", "POST"])
@login_required
def api_scans():
    if request.method == "GET":
        scans = SavedScan.query.filter_by(user_id=current_user.id).order_by(SavedScan.updated_at.desc()).all()
        return jsonify({"scans": [s.to_dict() for s in scans]})
    _check_csrf()
    body = request.get_json(silent=True) or {}
    if SavedScan.query.filter_by(user_id=current_user.id).count() >= 50:
        return _bad("you can keep up to 50 saved scans; delete one first")
    scan = SavedScan(user_id=current_user.id, name="Untitled scan", spec={}, universe={})
    try:
        _apply(scan, {"name": "Untitled scan", **body})
        if not scan.spec:
            return _bad("add at least one block to scan")
    except (ValueError, TypeError) as e:
        return _bad(str(e))
    db.session.add(scan)
    db.session.commit()
    return jsonify(scan.to_dict()), 201


@scanlab_bp.route("/api/scan-lab/scans/<int:scan_id>", methods=["PUT", "DELETE"])
@login_required
def api_scan(scan_id):
    _check_csrf()
    scan = _own_scan(scan_id)
    if request.method == "DELETE":
        db.session.delete(scan)
        db.session.commit()
        return jsonify({"deleted": scan_id})
    try:
        _apply(scan, request.get_json(silent=True) or {})
    except (ValueError, TypeError) as e:
        return _bad(str(e))
    db.session.commit()
    return jsonify(scan.to_dict())


# --- Alerts ------------------------------------------------------------------------------------------------

def _notify(scan, new_alerts):
    if not scan.alert_webhook or not new_alerts:
        return
    lines = [f"**{a.ticker}** {a.score:.0f}/100 · {', '.join((a.fired or [])[:4])}" for a in new_alerts[:15]]
    text = f"Scan Lab alert · {scan.name}: {len(new_alerts)} match{'es' if len(new_alerts) != 1 else ''}\n" + "\n".join(lines)
    payload = {"text": text.replace("**", "*")} if "slack.com" in scan.alert_webhook else {"content": text[:1900]}
    try:
        requests.post(scan.alert_webhook, json=payload, timeout=10)
    except requests.RequestException as e:
        logging.warning("alert webhook failed for scan %s: %s", scan.id, e)


def check_scan(scan, model=None, settings=None):
    """Run a saved scan and record alerts for its matches; returns the new alerts"""
    u = expand_universe(scan.universe or {}, limit=MAX_UNIVERSE)
    out = run_scan(scan.spec, u["tickers"], u["sector_of"], timeframe=scan.timeframe or "1d", model=model, settings=settings,
                   include_misses=False)
    hits = [r for r in out["results"] if r["matched"] and r["score"] >= (scan.alert_min_score or 0)]
    previous = set(scan.last_matches or [])
    fresh = [r for r in hits if r["ticker"] not in previous] if scan.alert_new_only else hits
    alerts = [ScanAlert(user_id=scan.user_id, scan_id=scan.id, ticker=r["ticker"], sector=r["sector"], score=r["score"],
                        price=r["price"], fired=r["fired"][:12]) for r in fresh]
    db.session.add_all(alerts)
    scan.last_matches = [r["ticker"] for r in hits]
    scan.last_run_at = datetime.utcnow()
    db.session.commit()
    _notify(scan, alerts)
    return alerts, out


@scanlab_bp.route("/api/scan-lab/scans/<int:scan_id>/check", methods=["POST"])
@login_required
def api_check(scan_id):
    _check_csrf()
    scan = _own_scan(scan_id)
    model, settings = _model_and_settings()
    alerts, out = check_scan(scan, model, settings)
    return jsonify({"new_alerts": [a.to_dict() for a in alerts], "matched": out["matched"], "scanned": out["scanned"],
                    "missing": out["missing"]})


@scanlab_bp.route("/api/scan-lab/alerts")
@login_required
def api_alerts():
    q = ScanAlert.query.filter_by(user_id=current_user.id)
    items = q.order_by(ScanAlert.created_at.desc()).limit(100).all()
    return jsonify({"alerts": [a.to_dict() for a in items], "unseen": q.filter_by(seen=False).count()})


@scanlab_bp.route("/api/scan-lab/alerts/seen", methods=["POST"])
@login_required
def api_alerts_seen():
    _check_csrf()
    ScanAlert.query.filter_by(user_id=current_user.id, seen=False).update({"seen": True})
    db.session.commit()
    return jsonify({"unseen": 0})


@scanlab_bp.route("/api/scan-lab/alerts/run-all", methods=["GET", "POST"])
def api_run_all():
    """Called by a scheduler (Vercel Cron sends 'Authorization: Bearer $CRON_SECRET')"""
    secret = os.environ.get("CRON_SECRET")
    given = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not secret or not hmac.compare_digest(given, secret):
        abort(403)
    model, settings = _model_and_settings()
    summary = []
    for scan in SavedScan.query.filter_by(alert_enabled=True).all():
        try:
            alerts, out = check_scan(scan, model, settings)
            summary.append({"scan": scan.id, "new_alerts": len(alerts), "matched": out["matched"]})
        except Exception as e:
            db.session.rollback()
            logging.exception("alert run failed for scan %s", scan.id)
            summary.append({"scan": scan.id, "error": type(e).__name__})
    return jsonify({"ran": len(summary), "scans": summary})
