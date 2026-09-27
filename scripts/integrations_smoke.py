"""Run every Hugging Face integration for real (needs internet); writes integrations_smoke/results.json"""

import json
import os
import time
import traceback
from datetime import date, timedelta

from pump_research.config import Settings
from pump_research.integrations import REGISTRY, run_integration
from pump_research.integrations.ohlcv_minute import daily_prices
from pump_research.model import recent_headlines
from pump_research.sources.prices import YahooPrices, records_to_frame

OUT = "integrations_smoke"


def yahoo(ticker, days=500):
    end = date.today()
    res = YahooPrices(Settings()).fetch(ticker, end - timedelta(days=days), end)
    return records_to_frame(res.records) if res.status == "ok" else None


def timed(fn):
    t = time.time()
    try:
        out = fn()
    except Exception as e:
        out = {"error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]}
    return {"seconds": round(time.time() - t, 1), "result": out}


def main():
    os.makedirs(OUT, exist_ok=True)
    results = {"packages": {k: REGISTRY[k].missing_packages() for k in REGISTRY}}
    prices = {t: yahoo(t) for t in ("SPY", "GME")}
    for ticker, df in prices.items():
        if df is None:
            results[ticker] = {"error": "no Yahoo prices"}
            continue
        headlines = recent_headlines(ticker)
        for key in ("yolo_chart_patterns", "yolo_candlesticks", "multisignal_trader", "candlefusion", "wsb_corpus",
                    "reddit_money_corpus"):
            results[f"{ticker}:{key}"] = timed(lambda: run_integration(key, df, ticker=ticker, headlines=headlines))
    results["candlestick_benchmark"] = timed(lambda: run_integration("candlestick_benchmark", limit=300))
    # Delisted pump stocks Yahoo no longer serves
    for ticker, start, end in (("LFIN", date(2017, 11, 1), date(2018, 1, 31)), ("BBBY", date(2020, 12, 1), date(2021, 2, 28)),
                               ("EXPR", date(2020, 12, 1), date(2021, 2, 28)), ("IRNT", date(2021, 8, 1), date(2021, 10, 15))):
        def fetch(t=ticker, s=start, e=end):
            df = daily_prices(t, s, e)
            return {"days": len(df), "first": str(df.index[0]) if len(df) else None, "last": str(df.index[-1]) if len(df) else None,
                    "max_close": float(df["close"].max()) if len(df) else None}
        results[f"ohlcv_1m:{ticker}"] = timed(fetch)
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    for k, v in results.items():
        if k != "packages":
            r = v.get("result", v)
            print(f"{k:40} {v.get('seconds', '')}s  {'ERROR ' + str(r.get('error'))[:120] if isinstance(r, dict) and r.get('error') else 'ok'}")


if __name__ == "__main__":
    main()
