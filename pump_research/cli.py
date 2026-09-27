"""
Command line interface.

  python -m pump_research check                  # which data sources are reachable
  python -m pump_research collect                # research every seed in seeds.csv
  python -m pump_research collect --tickers GME,PHUN
  python -m pump_research report                 # re-run analysis + report on collected data
  python -m pump_research discover --tickers-file universe.txt --start 2016-01-01
"""

import argparse
import csv
import json
import logging
import os
from datetime import date, timedelta

from .analysis import analyze
from .collector import load_seeds, collect_all, load_dataset
from .config import Settings
from .detection import discover
from .report import write_report
from .sources import default_price_sources, default_context_sources
from .sources.prices import records_to_frame
from .models import OK


def _settings(args) -> Settings:
    s = Settings()
    for attr in ("criterion", "min_multiple", "pre_window_days", "data_dir"):
        val = getattr(args, attr, None)
        if val is not None:
            setattr(s, attr, val)
    if getattr(args, "seeds", None):
        s.seeds_file = args.seeds
    return s


def cmd_check(args):
    """Probe each source with a small, known window (GME in January 2021)"""
    s = _settings(args)
    start, end = date(2021, 1, 11), date(2021, 1, 22)
    for source in default_price_sources(s) + default_context_sources(s):
        result = source.fetch("GME", start, end)
        print(f"{source.name:16} {result.status:10} {len(result.records):5} records  {result.detail[:90]}")


def cmd_collect(args):
    s = _settings(args)
    seeds = load_seeds(s.seeds_file)
    if args.tickers:
        wanted = {t.strip().upper() for t in args.tickers.split(",")}
        seeds = [x for x in seeds if x.ticker in wanted]
    records = collect_all(seeds, s, default_price_sources(s), default_context_sources(s))
    result = analyze(records, qualifying_only=args.qualifying_only)
    path = write_report(records, result, s)
    print(f"Collected {len(records)} events ({result['n_qualifying']} qualify). Dataset and report in {s.data_dir}/ ({path})")


def cmd_report(args):
    s = _settings(args)
    records = load_dataset(s)
    result = analyze(records, qualifying_only=args.qualifying_only)
    with open(os.path.join(s.data_dir, "analysis.json"), "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"Report written to {write_report(records, result, s)}")


def cmd_discover(args):
    """Scan a list of tickers for days clearing the threshold and write them as new seeds"""
    s = _settings(args)
    with open(args.tickers_file) as f:
        tickers = [t.strip().upper() for t in f if t.strip() and not t.startswith("#")]
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end) if args.end else date.today()
    sources = default_price_sources(s)
    found = []
    for ticker in tickers:
        for source in sources:
            result = source.fetch(ticker, start - timedelta(days=5), end)
            if result.status == OK:
                for d in discover(records_to_frame(result.records), s):
                    found.append({"ticker": ticker, "approx_date": d.isoformat(), "category": "discovered",
                                  "reported_move": "", "source_url": "", "ipo_price": "", "notes": f"found via {source.name}"})
                break
        else:
            print(f"{ticker}: no price data ({result.status})")
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ticker", "approx_date", "category", "reported_move", "source_url", "ipo_price", "notes"])
        writer.writeheader()
        writer.writerows(found)
    print(f"{len(found)} events found; written to {args.out}. Append them to seeds.csv to research them.")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pump_research", description="Research what happened before extreme stock pumps")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p):
        p.add_argument("--criterion", choices=["broad", "strict"])
        p.add_argument("--min-multiple", type=float, dest="min_multiple")
        p.add_argument("--window", type=int, dest="pre_window_days", help="pre-pump trading days (default 10)")
        p.add_argument("--data-dir", dest="data_dir")
        p.add_argument("--qualifying-only", action="store_true", help="analyze only events that clear the criterion")

    p = sub.add_parser("check", help="test which data sources are reachable"); common(p); p.set_defaults(func=cmd_check)
    p = sub.add_parser("collect", help="collect data for seeds"); common(p)
    p.add_argument("--seeds"); p.add_argument("--tickers", help="comma-separated subset of seed tickers")
    p.set_defaults(func=cmd_collect)
    p = sub.add_parser("report", help="analyze collected data and write the report"); common(p); p.set_defaults(func=cmd_report)
    p = sub.add_parser("discover", help="scan tickers for new pump events"); common(p)
    p.add_argument("--tickers-file", required=True); p.add_argument("--start", default="2016-01-01")
    p.add_argument("--end"); p.add_argument("--out", default="discovered_seeds.csv")
    p.set_defaults(func=cmd_discover)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    if not args.verbose:
        logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    args.func(args)
