# Tripler Lab

Every listed US stock that **tripled within three weeks** (a close at least 3× a prior close within 15
trading days), and everything that was true in the window before it launched. The data trains the scanner.

## What is collected

For each tripler, the launch point is the lowest close before the run, and the pre-launch window is the 10
trading days ending there. For each window:

| Data | Detail |
|---|---|
| Price action | 1-hour bars (Yahoo, last ~730 days), 4-hour bars (two per session: 9:30–13:30, 13:30–16:00), daily bars; price and volume paths from 40 days before to 15 days after launch |
| Indicator readings | Every Scan Lab block on each timeframe, as of the launch bar: candlesticks, harmonics, chart patterns, Fibonacci and Gann tools, trend, momentum, volatility, volume and structure |
| Technical snapshot | 120+ `ta_*` readings per timeframe (moving averages, oscillators, Bollinger, OBV, Fibonacci levels, Gann fan, box and square, the full Fib/Gann confluence suite) |
| News | Google News search by date (free, years back); Polygon when `POLYGON_API_KEY` is set |
| Filings | SEC EDGAR (blocked from GitHub's servers today; reported as such) |
| Social | Reddit posts in the main trading subreddits (Arctic Shift archive, time-budgeted) |
| Short side | FINRA short volume, Reg SHO threshold-list streak, FINRA short interest |

Ordinary windows from stocks in the **same price band** (under $1, $1–3, $3–10, $10+) that did not
triple are read the same way, three per tripler, so cheap-stock noise isn't mistaken for a signal.

## What is learned

- Every reading is compared between triplers and ordinary windows per timeframe (Fisher exact for
  hits, Mann-Whitney for numbers), with a Benjamini-Hochberg correction for the hundreds of tests.
- Readings that fire on two or more timeframes at once are tested separately.
- **Tripler DNA** scans (daily, 4-hour, 1-hour) are built from the blocks with the best lift on the
  earlier 70% of launches, and their lift is reported on the later 30%, which the learning never saw.
  `triplers analyze --install` saves them as Scan Lab starter scans. The daily one joins the daily
  radar, which keeps grading it on live picks.

## The page

`/pump-research/triplers` has five parts:

- **Historical overlay.** Every tripler lined up on its launch bar, with the median and middle-half
  band compared against ordinary windows. Type a ticker to lay its current chart on top. The analog
  match finds the 30 most similar historical run-ups and reports how many tripled, against the base rate.
- **Three dimensions.**
  - *Launch landscape* is a surface with one ridge per tripler.
  - *Phase space* traces each stock's path through distance-from-high × volume × momentum before
    launch, triplers in amber and ordinary windows in grey.
- **Readings heatmap.** Lift of every block on each timeframe.
- **Learned scans.** The Tripler DNA scans, with their out-of-sample results.
- **Event pages.** The chart on 1-hour, 4-hour or daily bars. Fibonacci retracement, Fib spiral,
  Gann fan, speed fans, circles, arcs, pitchfan, channel, Gann box and time zones are all anchored on
  the swings before launch. The page also lists what fired on each chart, plus the news and Reddit
  posts from the window.

## Running it

Add the `collect-triplers` label to the pull request (`collect-triplers-sample` for a quick 400-ticker
check), or run the **Collect triplers** workflow. Results are published to the `tripler-data` branch,
which the deployed app reads. To run it locally:

    uv run python -m pump_research triplers collect --out tripler_data
    uv run python -m pump_research triplers analyze --out tripler_data --install

Caveats:
- Today's exchange lists leave out stocks delisted since, so failed pumps are under-counted.
- Hourly history only reaches about two years back.

Nothing here is investment advice.
