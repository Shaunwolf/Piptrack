"""
Pre-pump similarity model.

Trained on pre-pump windows (label 1) vs ordinary windows from the same stocks
(label 0), using price and technical features only, since those are available
for both groups. Two layers:

- profile: for each feature, where a value falls in the ordinary-window
  distribution, oriented toward the pre-pump side. Works with a handful of events.
- logistic: a regularized logistic regression, fitted once there are enough
  events, with a cross-validated AUC so you can see whether it beats chance.

This is a research tool built on a small, hand-picked sample. It is not a trading signal.
"""

import json
import os
from datetime import date, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd

from .analysis import SIGNALS, _missing, compare_features, event_frame, control_frame, numeric_features, _is_bool_column
from .features import price_features
from .technicals import technical_snapshot

MIN_EVENTS_FOR_LOGISTIC = 8
PROFILE_TOP_FEATURES = 12
EXCLUDED = {"id", "category", "qualifies", "window_end", "window_days", "baseline_days"}


def _training_frames(records):
    events = event_frame(records)
    controls = control_frame(records)
    if events.empty or controls.empty:
        return None, None, []
    events = events[[c for c in events.columns if c in controls.columns or c in ("id",)]]
    cols = [c for c in numeric_features(events, controls)]
    cols += sorted(c for c in events.columns if c.startswith("ta_") and _is_bool_column(events[c]) and c in controls)
    cols = [c for c in cols if c not in EXCLUDED]
    return events, controls, cols


def _matrix(frame, cols, medians=None):
    X = frame.reindex(columns=cols).apply(pd.to_numeric, errors="coerce").astype(float)
    medians = X.median() if medians is None else medians
    return X.fillna(medians).fillna(0.0), medians


def train(records: List[Dict], settings) -> Dict:
    events, controls, cols = _training_frames(records)
    if events is None or len(events) < 3:
        raise ValueError("Need at least 3 events with a pre-pump window to train")

    ranked = compare_features(events, controls)
    # Keep features where at least ~70% of rows have data
    both = pd.concat([events.reindex(columns=cols), controls.reindex(columns=cols)])
    cols = [c for c in cols if both[c].notna().mean() >= 0.7]

    profile = []
    for r in ranked[:PROFILE_TOP_FEATURES]:
        if r["feature"] not in cols:
            continue
        values = pd.to_numeric(controls[r["feature"]], errors="coerce").dropna()
        profile.append({
            "feature": r["feature"],
            "direction": 1 if r["prob_event_higher"] >= 0.5 else -1,
            "strength": abs(r["prob_event_higher"] - 0.5) * 2,
            "control_quantiles": [float(q) for q in values.quantile(np.linspace(0, 1, 21))],
        })

    model = {"trained_on": date.today().isoformat(), "n_events": int(len(events)), "n_controls": int(len(controls)),
             "features": cols, "profile": profile, "logistic": None}

    if len(events) >= MIN_EVENTS_FOR_LOGISTIC and len(controls) >= MIN_EVENTS_FOR_LOGISTIC:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import GroupKFold, cross_val_predict
        from sklearn.metrics import roc_auc_score

        X_e, med = _matrix(pd.concat([events, controls]), cols)
        y = np.r_[np.ones(len(events)), np.zeros(len(controls))]
        mean, std = X_e.mean(), X_e.std().replace(0, 1)
        Xs = ((X_e - mean) / std).to_numpy()
        clf = LogisticRegression(C=0.3, class_weight="balanced", max_iter=2000)
        # Group folds by event so a stock's own ordinary windows never leak into its test fold
        groups = np.r_[events["id"].to_numpy(), controls["id"].to_numpy()]
        folds = min(5, len(set(events["id"])))
        probs = cross_val_predict(clf, Xs, y, cv=GroupKFold(folds), groups=groups, method="predict_proba")[:, 1]
        clf.fit(Xs, y)
        model["logistic"] = {
            "intercept": float(clf.intercept_[0]),
            "coef": {c: float(w) for c, w in zip(cols, clf.coef_[0])},
            "mean": {c: float(mean[c]) for c in cols}, "std": {c: float(std[c]) for c in cols},
            "median": {c: float(med[c]) if not pd.isna(med[c]) else 0.0 for c in cols},
            "cv_auc": float(roc_auc_score(y, probs)),
        }

    os.makedirs(settings.data_dir, exist_ok=True)
    with open(os.path.join(settings.data_dir, "model.json"), "w") as f:
        json.dump(model, f, indent=2)
    return model


def load_model(settings) -> Dict:
    with open(os.path.join(settings.data_dir, "model.json")) as f:
        return json.load(f)


def _percentile(value, quantiles):
    return float(np.interp(value, quantiles, np.linspace(0, 1, len(quantiles))))


def score_features(features: Dict, model: Dict) -> Dict:
    """0-100 similarity to pre-pump windows, with the features that drove it"""
    contributions = []
    total_w = 0.0
    profile_score = 0.0
    for p in model["profile"]:
        v = features.get(p["feature"])
        if _missing(v):
            continue
        pct = _percentile(float(v), p["control_quantiles"])
        oriented = pct if p["direction"] > 0 else 1 - pct
        profile_score += oriented * p["strength"]
        total_w += p["strength"]
        contributions.append({"feature": p["feature"], "value": float(v), "percentile_vs_ordinary": round(pct, 3),
                              "leans_pre_pump": oriented > 0.5, "weight": round(p["strength"], 3)})
    result = {"profile_score": round(100 * profile_score / total_w, 1) if total_w else None,
              "logistic_score": None, "cv_auc": None}

    lg = model.get("logistic")
    if lg:
        z = lg["intercept"]
        for c, w in lg["coef"].items():
            v = features.get(c)
            v = lg["median"][c] if _missing(v) else float(v)
            z += w * (v - lg["mean"][c]) / lg["std"][c]
        result["logistic_score"] = round(100 / (1 + np.exp(-z)), 1)
        result["cv_auc"] = round(lg["cv_auc"], 3)

    result["score"] = result["logistic_score"] if result["logistic_score"] is not None else result["profile_score"]
    result["contributions"] = sorted(contributions, key=lambda c: -c["weight"])
    return result


def fired_signals(features: Dict) -> Dict[str, bool]:
    out = {}
    for name, (cols, test) in SIGNALS.items():
        if all(c in features and not _missing(features[c]) for c in cols):
            out[name] = bool(test(features))
    return out


def analyze_ticker(ticker: str, settings, price_sources, model: Dict = None) -> Dict:
    """Run the full technical picture and (if a model exists) the pre-pump score on the latest bars"""
    end = date.today()
    start = end - timedelta(days=500)
    prices, status = None, []
    for source in price_sources:
        result = source.fetch(ticker, start, end)
        status.append({"source": result.source, "status": result.status, "detail": result.detail})
        if result.status == "ok":
            from .sources.prices import records_to_frame
            prices = records_to_frame(result.records)
            break
    if prices is None or len(prices) < 30:
        return {"ticker": ticker, "error": "no price data", "sources": status}
    return analyze_prices(ticker, prices, settings, model, status)


def analyze_prices(ticker, prices: pd.DataFrame, settings, model=None, status=None) -> Dict:
    last = len(prices) - 1
    snapshot = technical_snapshot(prices, last, settings.pre_window_days)
    feats = price_features(prices, last, settings, snapshot) or dict(snapshot["features"])
    out = {
        "ticker": ticker, "as_of": prices.index[-1].isoformat(), "close": float(prices["close"].iloc[-1]),
        "features": feats, "signals": fired_signals(feats), "technicals": {k: v for k, v in snapshot.items() if k != "features"},
        "prices": [{"date": d.isoformat(), **{k: float(v) for k, v in row.items()}} for d, row in prices.tail(180).iterrows()],
        "sources": status or [],
    }
    if model:
        out["score"] = score_features(feats, model)
    return out
