"""
Command line interface.

  python -m pump_research check                  # which data sources are reachable
  python -m pump_research collect                # research every seed in seeds.csv
  python -m pump_research collect --tickers GME,PHUN
  python -m pump_research report                 # re-run analysis + report on collected data
  python -m pump_research discover --tickers-file universe.txt --start 2016-01-01
  python -m pump_research train                  # fit the pre-pump similarity model
  python -m pump_research score AAPL TSLA        # technicals + pre-pump score for current prices
  python -m pump_research scan --preset harmonic_hunter --sector Financials   # a Scan Lab scan on live prices
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
                # The fetch starts a few days early for a previous close; only report dates in range
                for d in (d for d in discover(records_to_frame(result.records), s) if start <= d <= end):
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


def cmd_train(args):
    from .model import train
    s = _settings(args)
    model = train(load_dataset(s), s)
    auc = model["logistic"]["cv_auc"] if model["logistic"] else None
    print(f"Trained on {model['n_events']} pre-pump windows vs {model['n_controls']} ordinary windows; "
          f"{len(model['profile'])} profile features" + (f"; logistic cross-validated AUC {auc:.2f}" if auc else
          f" (logistic model needs {8} or more events)"))


def cmd_score(args):
    from .model import analyze_ticker, load_model
    s = _settings(args)
    try:
        model = load_model(s)
    except FileNotFoundError:
        model = None
        print("No model yet (run collect + train); showing technicals only.")
    for ticker in args.tickers:
        res = analyze_ticker(ticker.upper(), s, default_price_sources(s), model)
        if "error" in res:
            print(f"{ticker}: {res['error']} ({', '.join(x['source'] + '=' + x['status'] for x in res['sources'])})")
            continue
        score = res.get("score", {}).get("score")
        fired = [k for k, v in res["signals"].items() if v]
        pats = sorted({p["name"] for p in res["technicals"]["patterns"] if p["type"] != "candle"})
        print(f"{res['ticker']} {res['as_of']} close ${res['close']:.2f}"
              + (f"  pre-pump score {score:.0f}/100" if score is not None else ""))
        print(f"  signals: {', '.join(fired) or 'none'}")
        print(f"  patterns: {', '.join(pats) or 'none'}")


def cmd_tools(args):
    """List every tool, or run them on a ticker's latest prices"""
    from .toolkit import list_tools, run_all_tools
    if not args.ticker:
        for t in list_tools():
            print(f"{t['name']:32} {t['category']:13} {t['description']}")
        return
    s = _settings(args)
    end = date.today()
    for source in default_price_sources(s):
        result = source.fetch(args.ticker.upper(), end - timedelta(days=500), end)
        if result.status == OK:
            out = run_all_tools(records_to_frame(result.records), args.tool or None)
            print(json.dumps(out, indent=2, default=str))
            return
    print(f"No price data for {args.ticker} ({result.status}: {result.detail})")


def cmd_integrations(args):
    """List, enable, disable or run the Hugging Face integrations"""
    from .integrations import REGISTRY, list_integrations, run_integration, set_enabled
    if args.action == "list":
        for i in list_integrations():
            state = "ON " if i["enabled"] else "off"
            ready = "ready" if i["ready"] else f"needs: pip install {i['install']}"
            print(f"[{state}] {i['key']:22} {i['title']:48} {ready}")
        return
    if args.action in ("enable", "disable"):
        for key in args.keys:
            status = set_enabled(key, args.action == "enable")
            print(f"{key}: {'enabled' if status['enabled'] else 'disabled'}"
                  + ("" if status["ready"] else f" (install first: pip install {status['install']})"))
        return
    # run KEY TICKER
    key, ticker = args.keys[0], (args.keys[1] if len(args.keys) > 1 else "")
    if key not in REGISTRY:
        raise SystemExit(f"unknown integration {key}")
    s = _settings(args)
    prices = None
    if ticker:
        end = date.today()
        for source in default_price_sources(s):
            result = source.fetch(ticker.upper(), end - timedelta(days=500), end)
            if result.status == OK:
                prices = records_to_frame(result.records)
                break
    kwargs = {"start": date.today() - timedelta(days=90), "end": date.today()} if key == "ohlcv_1m_prices" else {}
    print(json.dumps(run_integration(key, prices, ticker=ticker.upper(), **kwargs), indent=2, default=str))


def cmd_scan(args):
    """Run a Scan Lab starter scan (or a spec file) over sectors, lists or tickers with live prices"""
    from .model import load_model
    from .scanlab import expand_universe, preset, run_scan
    from .scanlab.presets import all_presets as _all
    PRESETS = _all()
    if args.list:
        for key, p in PRESETS.items():
            print(f"{key:20} {p['title']:22} {p['tagline']}")
        return
    if args.spec:
        with open(args.spec) as f:
            spec, universe = json.load(f), {}
    else:
        chosen = preset(args.preset)
        spec, universe = chosen["spec"], chosen["universe"]
    if args.sector or args.lists or args.tickers:
        universe = {"sectors": args.sector or [], "lists": args.lists or [], "tickers": args.tickers or []}
    u = expand_universe(universe, limit=args.limit)
    settings = _settings(args)
    try:
        model = load_model(settings)
    except Exception:
        model = None
    out = run_scan(spec, u["tickers"], u["sector_of"], timeframe=args.timeframe, model=model, settings=settings,
                   include_misses=args.all)
    if args.json:
        print(json.dumps(out, indent=2, default=str))
        return
    print(f"{out['matched']} match(es) out of {out['scanned']} scanned ({len(out['missing'])} without data) in {out['seconds']} s")
    for r in out["results"][:args.top]:
        mark = "MATCH" if r["matched"] else "     "
        print(f"{mark} {r['ticker']:7} {r['score']:5.1f}  {r['price']:>10.2f}  {r['sector'][:22]:22}  {', '.join(r['fired'][:5])}")
    if out["missing"]:
        print("no data:", ", ".join(out["missing"][:30]) + (" …" if len(out["missing"]) > 30 else ""))


def cmd_radar(args):
    """Daily radar: store today's picks, or grade past picks against what happened next"""
    from .radar import grade, render_report, run_radar
    if args.action == "run":
        settings = _settings(args)
        try:
            from .model import load_model
            model = load_model(settings)
        except Exception:
            model = None
        snap = run_radar(args.dir, model=model, settings=settings)
        for key, s in snap["scans"].items():
            print(f"{key}: {len(s['picks'])} picks out of {len(s['scanned'])} scanned: "
                  + ", ".join(p["ticker"] for p in s["picks"][:15]))
    else:
        print(render_report(grade(args.dir)))


def cmd_triplers(args):
    """Find every listed stock that tripled within 3 weeks and collect its pre-launch readings, or analyze them"""
    import json
    if args.action == "collect":
        from .config import Settings
        from .triplers import listed_tickers
        from .triplers.collect import collect
        tickers = [t.strip().upper() for t in args.tickers.split(",")] if args.tickers else listed_tickers()
        if args.limit:
            tickers = tickers[:args.limit]
        meta = collect(tickers, args.out, Settings(), controls_per_event=args.controls, max_events=args.max_events,
                       social_budget_minutes=args.social_minutes)
        print(json.dumps(meta, indent=1))
    else:
        from .triplers.analyze import analyze
        res = analyze(args.out)
        print(open(os.path.join(args.out, "report.md")).read())
        if args.install:
            from .scanlab.presets import LEARNED_DIR
            os.makedirs(LEARNED_DIR, exist_ok=True)
            for tf, p in res["presets"].items():
                with open(os.path.join(LEARNED_DIR, f"tripler_dna_{tf}.json"), "w") as f:
                    json.dump(p, f, indent=1)
                print(f"installed Scan Lab preset tripler_dna_{tf}")


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

    p = sub.add_parser("train", help="fit the pre-pump similarity model on collected data"); common(p)
    p.set_defaults(func=cmd_train)
    p = sub.add_parser("score", help="technical picture + pre-pump score for tickers today"); common(p)
    p.add_argument("tickers", nargs="+"); p.set_defaults(func=cmd_score)

    p = sub.add_parser("tools", help="list every technical tool, or run them on a ticker"); common(p)
    p.add_argument("ticker", nargs="?"); p.add_argument("--tool", action="append", help="run only this tool (repeatable)")
    p.set_defaults(func=cmd_tools)

    p = sub.add_parser("integrations", help="list / enable / disable / run the Hugging Face integrations"); common(p)
    p.add_argument("action", choices=["list", "enable", "disable", "run"])
    p.add_argument("keys", nargs="*", help="integration keys (for run: KEY TICKER)")
    p.set_defaults(func=cmd_integrations)

    p = sub.add_parser("scan", help="run a Scan Lab scan over sectors, lists or tickers"); common(p)
    p.add_argument("--preset", default="momentum_breakout", help="starter scan key (see --list)")
    p.add_argument("--spec", help="JSON file with a scan spec instead of a preset")
    p.add_argument("--sector", action="append", help="GICS sector name (repeatable)")
    p.add_argument("--lists", action="append", help="themed list key, e.g. meme (repeatable)")
    p.add_argument("--tickers", nargs="*")
    p.add_argument("--timeframe", choices=["1d", "1wk", "4h", "1h"], default="1d")
    p.add_argument("--limit", type=int, default=600)
    p.add_argument("--top", type=int, default=25)
    p.add_argument("--all", action="store_true", help="also list near misses")
    p.add_argument("--json", action="store_true")
    p.add_argument("--list", action="store_true", help="list the starter scans")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("radar", help="daily radar: run today's scans, or grade past picks"); common(p)
    p.add_argument("action", choices=["run", "grade"])
    p.add_argument("--dir", default="radar")
    p.set_defaults(func=cmd_radar)

    p = sub.add_parser("triplers", help="stocks that tripled within 3 weeks: collect pre-launch readings, or analyze them")
    p.add_argument("action", choices=["collect", "analyze"])
    p.add_argument("--out", default="tripler_data")
    p.add_argument("--tickers", help="comma-separated tickers (default: every listed common stock)")
    p.add_argument("--limit", type=int, default=0, help="only the first N tickers (testing)")
    p.add_argument("--controls", type=int, default=3, help="ordinary windows per tripler")
    p.add_argument("--max-events", type=int, default=0, help="keep only the N most recent triplers")
    p.add_argument("--social-minutes", type=float, default=60, help="time budget for Reddit archive searches")
    p.add_argument("--install", action="store_true", help="save the learned scans as Scan Lab starter scans")
    p.set_defaults(func=cmd_triplers)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    if not args.verbose:
        logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    args.func(args)
