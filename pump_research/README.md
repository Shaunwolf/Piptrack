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

Useful options: `--criterion strict|broad`, `--min-multiple 5`, `--window 10` (trading days before the pump), `--tickers GME,PHUN`, `--qualifying-only`.

## What it produces (in `pump_data/`)

| File | Contents |
|---|---|
| `pump_dataset.json` | Everything in one file: each event's measured pump, source statuses, price history (baseline → 10 days after), pre-window features, comparison windows, and every filing, article and Reddit post found |
| `events/<TICKER>_<date>.json` | The same data, one file per event |
| `pump_summary.csv` | One row per event with the key numbers (opens in Excel) |
| `pump_report.md` | Coverage, event table, what separates pre-pump windows from ordinary ones, warning-sign rates, day-by-day countdown, and a dossier per event |
| `analysis.json` | Raw analysis output (written by `report`) |

## How it works

1. **Seeds** (`seeds.csv`): candidate events with an approximate date, a reported move and a source link. Nothing in this file counts as verified.
2. **Detection** (`detection.py`): searches ±10 trading days around the seed date for the real spike. It measures:
   - the same-day close multiple
   - the intraday-high multiple
   - the best run of up to 5 days

   It then classifies the event as `single_day`, `multi_day_run` (the window ends before the run *starts*) or `ipo_debut` (measured against the IPO price; there's no pre-pump trading history).
   - `strict`: the close is ≥ 5x the previous close on the same day.
   - `broad` (default): the intraday high is ≥ 5x, or a run of up to 5 days reaches 5x.

   Famous squeezes below the bar (GME, AMC…) are still collected and marked `qualifies: false`, so you can compare them.
3. **Collection** (`collector.py`, `sources/`): fetches the pre-pump window from each source. Every source reports `ok`, `no_data`, `blocked`, `needs_key`, `skipped` or `error`. A source that didn't answer shows up as **unknown** (`?`), never as zero.
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

`uv run python -m pytest tests/test_pump_research.py` runs the whole pipeline offline on synthetic data.
