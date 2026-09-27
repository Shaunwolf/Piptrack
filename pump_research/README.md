# pump_research

This toolkit researches what was happening to a stock in the **one to two weeks before an extreme price spike**. For each event it collects:

- price and volume
- SEC filings
- news
- Reddit chatter

It then analyzes what those pre-pump windows have in common, compared with ordinary periods for the same stocks.

## Quick start

```bash
uv sync
uv run python -m pump_research check        # which data sources can this machine reach?
uv run python -m pump_research collect      # research every candidate in seeds.csv
open pump_data/pump_report.md               # the readable report
```

```bash
uv run python -m pump_research train        # fit the pre-pump similarity model on the collected data
uv run python -m pump_research score GME    # full technical picture + similarity score for today's prices
```

Useful options: `--criterion strict|broad`, `--min-multiple 5`, `--window 10` (trading days before the pump), `--tickers GME,PHUN`, `--qualifying-only`.

### In the web app (the Pump Observatory)

The **Pump Research** item in the main nav (`/pump-research`) reads the same `pump_data/` folder (override it with `PUMP_DATA_DIR`):

- **Design**: a seismograph theme (pumps are eruptions, the pre-pump window is the tremor). Styles live in the self-contained `static/css/pump.css`, which doesn't depend on Tailwind. Chart colors come from a validated colorblind-safe dark palette, each panel has one axis, and direction is never shown by color alone.
- **Dashboard**: a masthead seismograph drawn from the real median countdown, and a "tremor strip" for every pump (volume vs normal for each day before it, on one shared log scale). Below that, what gives a pump away, event table, which numeric and yes/no technical features separate pre-pump windows from ordinary ones, and source coverage.
- **Event dossier** (`/pump-research/event/<id>`): candlestick chart with EMA 21, WMA 20, Hull 20 and VWMA 20, Fibonacci levels, support/resistance, harmonic XABCD outlines, pattern markers and the shaded pre-pump window. Also the full technical panel, the day-by-day countdown, and the filings, news and Reddit posts from the window.
- **Live scan** (`/pump-research/scan?ticker=XYZ`, JSON at `/api/pump-research/scan/XYZ`): the same technical picture for the latest sessions, plus warning signs and the similarity score with the features driving it.

The old Backtest / Pump Analysis URLs redirect here.

## Technical analysis engine (`technicals/`)

Everything runs on daily OHLCV data up to the bar being analyzed (never later; a test checks this):

| Area | What it computes |
|---|---|
| Moving averages | EMA 8/21/50/200, **linearly weighted** WMA 10/20/50, Hull 20, **volume-weighted** VWMA 20, SMA 50/200. Close vs each; EMA and WMA bull/bear stacks; ribbon width; EMA8×EMA21, close×WMA20, close×Hull20 and golden crosses inside the window; EMA21 slope |
| Momentum | RSI 14 (and its window low), stochastic %K/%D, MACD histogram + bullish cross, ADX with +DI/−DI spread, bullish RSI divergence on swing lows |
| Volatility | ATR %, Bollinger %B, bandwidth and **squeeze** (bandwidth in the lowest 20% of 120 bars), range expansion |
| Volume / flow | OBV slope and accumulation divergence, MFI 14, Chaikin money flow, close vs rolling VWAP |
| Fibonacci | Dominant swing, retracement or bounce level, nearest level, golden pocket, extension targets (1.272 → 4.236), and where each pump **peaked on the extension scale** |
| Swings & structure | Volatility-scaled zigzag pivots, higher highs/lows, up/down/range structure, break of structure, clustered support/resistance with touch counts |
| Harmonic patterns | Gartley, Bat, Alt Bat, Butterfly, Crab, Deep Crab, Shark, Cypher, AB=CD, with fit scores and bullish/bearish direction |
| Chart patterns | Double bottom/top (with neckline breakout), head & shoulders and inverse, ascending/descending/symmetrical triangles, rising/falling wedges, bull flag, cup & handle, consolidation, range breakout/breakdown on volume |
| Candlesticks | Hammer, inverted hammer, shooting star, hanging man, doji (plain/dragonfly/gravestone), marubozu, engulfing, piercing line, dark cloud, morning/evening star, three white soldiers/black crows, inside/outside bars, gaps |

`technical_snapshot(prices, end_idx, window_days)` returns flat `ta_*` features (80+) for statistics, plus the detected patterns, Fibonacci levels, moving averages, levels and pivots for display.

## Similarity model (`model.py`)

The model is trained on pre-pump windows (label 1) versus ordinary windows from the same stocks (label 0), using price and technical features, which both groups have.

- **Profile score** (works from 3 events): for the strongest separating features, it works out where today's value falls in the ordinary-window distribution, pointed toward the pre-pump side.
- **Logistic regression** (from 8 events): regularized and class-balanced. It reports a cross-validated AUC, with folds grouped by stock so a stock's ordinary windows never leak into its own test fold.

The score is a research aid built on a small, hand-picked sample. It is not a prediction or a trading signal.

## What it produces (in `pump_data/`)

| File | Contents |
|---|---|
| `pump_dataset.json` | Everything in one file: each event's measured pump, source statuses, price history (baseline → 10 days after), pre-window features, comparison windows, and every filing, article and Reddit post found |
| `events/<TICKER>_<date>.json` | The same data, one file per event |
| `pump_summary.csv` | One row per event with the key numbers (opens in Excel) |
| `pump_report.md` | Coverage, event table, what separates pre-pump windows from ordinary ones, warning-sign rates, day-by-day countdown, and a dossier per event |
| `analysis.json` | Raw analysis output (written by `report`) |
| `model.json` | The trained similarity model (written by `train`) |

## How it works

1. **Seeds** (`seeds.csv`): candidate events with an approximate date, a reported move and a source link. Nothing in this file counts as verified. The optional `cik` column (the SEC company number) lets filings be found for delisted or renamed tickers.
2. **Detection** (`detection.py`): searches ±10 trading days around the seed date for the real spike. It measures:
   - the same-day close multiple
   - the intraday-high multiple
   - the best run of up to 5 days

   It then classifies the event as `single_day`, `multi_day_run` (the window ends before the run *starts*) or `ipo_debut` (measured against the IPO price; there's no pre-pump trading history).
   - `strict`: the close is ≥ 5x the previous close on the same day.
   - `broad` (default): the intraday high is ≥ 5x, or a run of up to 5 days reaches 5x.

   Famous squeezes below the bar (GME, AMC…) are still collected and marked `qualifies: false`, so you can compare them.
3. **Collection** (`collector.py`, `sources/`): fetches the pre-pump window from each source. Every source reports `ok`, `no_data`, `partial` (hit a result cap, so its counts are lower bounds, shown as `≥N`), `blocked`, `needs_key`, `skipped` or `error`. A source that didn't answer shows up as **unknown** (`?`), never as zero.
4. **Features** (`features.py`):
   - Price: window return, volatility, and average, peak and last-3-day volume versus the prior 60-day baseline; volume trend, gap-ups, RSI, price level, dollar volume.
   - Context: counts of offering, 8-K, insider and ownership filings; news count; Reddit mentions, unique authors, acceleration into the pump, and sentiment (VADER).
5. **Analysis** (`analysis.py`): compares pre-pump windows against up to 4 ordinary windows per stock, taken ≥ 30 trading days before its pump. It ranks features by how well they separate the two groups (Mann-Whitney test), checks a list of warning signs, and builds a median day-by-day countdown.
6. **Discovery** (`discover` command): scans a list of tickers for every day that clears the threshold and writes them out as new seeds. Use it to go beyond the hand-picked list.

## Data sources and their limits

| Source | Gives | Needs | Limits |
|---|---|---|---|
| Yahoo Finance (`yfinance`) | Daily prices | Network access to `query1/query2.finance.yahoo.com`, `fc.yahoo.com` | Missing most **delisted** tickers, and many pump stocks were delisted |
| Polygon.io | Daily prices + news | `POLYGON_API_KEY` (paid plans cover delisted tickers and long history) | Paid |
| SEC EDGAR | Filings in the window | `www.sec.gov`, `data.sec.gov`; set `SEC_USER_AGENT="Your Name you@email"` | Ticker lookup only knows currently registered tickers |
| Pullpush (Reddit archive) | Posts + comments | `api.pullpush.io` | Archive completeness varies; StockTwits isn't available (their API is closed to new developers) |
| GDELT | News | `api.gdeltproject.org` | Only about the last 3 months, so it's skipped for older windows |

To add a source, subclass `sources.base.DataSource`, implement `_fetch(ticker, start, end)` to return a list of dicts, and add it to `default_context_sources`.

## Tests

`uv run python -m pytest tests` runs everything offline on synthetic data:
- `test_technicals.py` checks each tool on hand-built price paths (known Gartley/Bat ratios, a 0.618 pullback, double bottoms, flags, candles, and no lookahead).
- `test_pump_research.py` covers detection, collection, analysis, the report and the model.
- `test_pump_web.py` renders the web pages through Flask's test client.
