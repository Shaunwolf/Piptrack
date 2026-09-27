"""
Collect everything for each seed: price history, the located pump, and what was
happening in the pre-pump window. Writes one JSON file per event plus a combined
dataset (pump_dataset.json) and a one-row-per-event summary (pump_summary.csv).
"""

import csv
import json
import logging
import os
from datetime import date, timedelta
from typing import Dict, List

import pandas as pd

from .detection import locate_pump, qualifies
from .features import price_features, daily_profile, control_window_ends, context_features
from .technicals import technical_snapshot
from .technicals.fibonacci import extension_multiple
from .models import Seed, OK, NO_DATA, SKIPPED
from .sources.prices import records_to_frame

log = logging.getLogger(__name__)

# Calendar days of history fetched around each seed: enough for baseline + control windows
HISTORY_BEFORE_DAYS = 400
HISTORY_AFTER_DAYS = 30


def load_seeds(path) -> List[Seed]:
    seeds = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            seeds.append(Seed(
                ticker=row["ticker"].strip().upper(),
                approx_date=date.fromisoformat(row["approx_date"]),
                category=row.get("category", ""),
                reported_move=row.get("reported_move", ""),
                source_url=row.get("source_url", ""),
                notes=row.get("notes", ""),
                ipo_price=float(row["ipo_price"]) if row.get("ipo_price") else None,
            ))
    return seeds


def event_id(seed: Seed) -> str:
    return f"{seed.ticker}_{seed.approx_date.isoformat()}"


def fetch_prices(seed: Seed, price_sources):
    """Try each price source in order; return (DataFrame, results for every source tried)"""
    start = seed.approx_date - timedelta(days=HISTORY_BEFORE_DAYS)
    end = seed.approx_date + timedelta(days=HISTORY_AFTER_DAYS)
    tried = []
    for source in price_sources:
        result = source.fetch(seed.ticker, start, end)
        tried.append(result)
        if result.status == OK:
            return records_to_frame(result.records), tried
    return records_to_frame([]), tried


def collect_event(seed: Seed, settings, price_sources, context_sources) -> Dict:
    record = {
        "id": event_id(seed),
        "seed": {**seed.__dict__, "approx_date": seed.approx_date.isoformat()},
        "criterion": settings.criterion,
        "min_multiple": settings.min_multiple,
        "sources": {},
        "event": None,
        "qualifies": False,
        "detection": "",
        "price_features": None,
        "technicals": None,
        "daily_profile": [],
        "controls": [],
        "context": {},
        "context_features": None,
        "price_history": [],
    }

    prices, tried = fetch_prices(seed, price_sources)
    for result in tried:
        record["sources"][result.source] = {"status": result.status, "detail": result.detail, "records": len(result.records)}

    event = locate_pump(prices, seed.approx_date, settings, seed.ipo_price)
    if event is None:
        record["detection"] = "no price data around the seed date"
        # Context sources can still describe the approximate window
        window_end = seed.approx_date - timedelta(days=1)
        window_dates = [d.date() for d in pd.bdate_range(end=window_end, periods=settings.pre_window_days)]
    else:
        event.ticker = seed.ticker
        record["event"] = event.to_dict()
        record["qualifies"] = qualifies(event, settings)
        record["detection"] = "located"
        dates = list(prices.index)
        pump_idx = dates.index(event.pump_date)
        window_dates = dates[max(0, pump_idx - settings.pre_window_days):pump_idx]

        if pump_idx > settings.pre_window_days:
            snapshot = technical_snapshot(prices, pump_idx - 1, settings.pre_window_days)
            record["technicals"] = {k: v for k, v in snapshot.items() if k != "features"}
            record["price_features"] = price_features(prices, pump_idx - 1, settings, snapshot)
            # Where the pump peaked on the pre-pump swing's Fibonacci extension scale
            peak = float(prices["high"].iloc[pump_idx:pump_idx + max(1, event.run_days)].max())
            record["event"]["peak_fib_extension"] = extension_multiple(peak, snapshot["fibonacci"])
            record["daily_profile"] = daily_profile(prices, pump_idx, settings)
            for end_idx in control_window_ends(prices, pump_idx, settings):
                feats = price_features(prices, end_idx, settings)
                if feats:
                    record["controls"].append({"window_end": dates[end_idx].isoformat(), **feats})

        # Keep the price series from baseline start through a couple of weeks after the pump
        lo = max(0, pump_idx - settings.pre_window_days - settings.baseline_days)
        hi = min(len(dates), pump_idx + 11)
        record["price_history"] = [
            {"date": d.isoformat(), **{k: float(v) for k, v in prices.loc[d].items()}} for d in dates[lo:hi]
        ]

    if window_dates:
        start, end = window_dates[0], window_dates[-1]
        for source in context_sources:
            result = source.fetch(seed.ticker, start, end)
            record["sources"][result.source] = {"status": result.status, "detail": result.detail, "records": len(result.records)}
            record["context"][result.source] = result.records
        answered = [name for name, info in record["sources"].items() if info["status"] in (OK, NO_DATA)]
        record["context_features"] = context_features(record["context"], window_dates, answered)
        record["window_dates"] = [d.isoformat() for d in window_dates]
    else:
        for source in context_sources:
            record["sources"][source.name] = {"status": SKIPPED, "detail": "no pre-pump window (IPO debut)", "records": 0}

    return record


SUMMARY_FIELDS = [
    "id", "ticker", "category", "event_type", "pump_date", "qualifies", "meets_strict", "meets_broad",
    "close_multiple", "high_multiple", "run_multiple", "run_days", "prev_close", "day_high",
    "window_return", "avg_volume_ratio", "max_volume_ratio", "volatility_ratio", "rsi_14", "last_close",
    "filings_total", "filings_offering", "news_articles", "reddit_mentions", "reddit_mention_acceleration",
    "reddit_avg_sentiment", "source_statuses", "reported_move", "source_url",
]


def summary_row(rec: Dict) -> Dict:
    ev = rec.get("event") or {}
    pf = rec.get("price_features") or {}
    cf = rec.get("context_features") or {}
    seed = rec["seed"]
    row = {
        "id": rec["id"], "ticker": seed["ticker"], "category": seed["category"],
        "qualifies": rec["qualifies"], "reported_move": seed["reported_move"], "source_url": seed["source_url"],
        "source_statuses": "; ".join(f"{k}={v['status']}" for k, v in rec["sources"].items()),
    }
    for k in SUMMARY_FIELDS:
        if k not in row:
            row[k] = ev.get(k, pf.get(k, cf.get(k)))
    return row


def collect_all(seeds: List[Seed], settings, price_sources, context_sources) -> List[Dict]:
    events_dir = os.path.join(settings.data_dir, "events")
    os.makedirs(events_dir, exist_ok=True)
    records = []
    for seed in seeds:
        log.info("Collecting %s around %s", seed.ticker, seed.approx_date)
        rec = collect_event(seed, settings, price_sources, context_sources)
        with open(os.path.join(events_dir, f"{rec['id']}.json"), "w") as f:
            json.dump(rec, f, indent=2, default=str)
        records.append(rec)
    write_dataset(records, settings)
    return records


def write_dataset(records: List[Dict], settings):
    os.makedirs(settings.data_dir, exist_ok=True)
    with open(os.path.join(settings.data_dir, "pump_dataset.json"), "w") as f:
        json.dump(records, f, indent=2, default=str)
    with open(os.path.join(settings.data_dir, "pump_summary.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for rec in records:
            writer.writerow(summary_row(rec))


def load_dataset(settings) -> List[Dict]:
    with open(os.path.join(settings.data_dir, "pump_dataset.json")) as f:
        return json.load(f)
