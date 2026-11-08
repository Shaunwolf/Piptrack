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

## First full collection (November 8, 2026)

541 triplers in 5,894 listed stocks over two years, against 1,500 ordinary windows from stocks at the same
price. The median tripler took 8 trading days to reach 3×, peaked at 4.1×, and launched from $2.84.

**What came before (all significant after correcting for ~1,000 tests):**

- **They were crushed.**
  - A median 88% below the 1-year high (ordinary windows: 44%) and 71% below the 200-day EMA (12%).
  - RSI 34 (46).
  - The Fear & Greed block read extreme fear before 48% of triplers on the daily chart (14% of ordinary
    windows) and 39% on the 1-hour chart (7%).
- **They were volatile and falling into a pattern.**
  - Average true range was 17% of the price (7%).
  - Falling wedges came before 25–27% of triplers on every chart (10–15% of ordinary windows).
  - Range breakdowns came before 34% on the daily chart (16%).
  - Bearish EMA stacks came before 84% on the 1-hour chart (47%).
  - Volume accumulated while price was flat on the 4-hour chart before 20% (9%).
- **They were not consolidating.** Tight consolidations, pullbacks in uptrends and higher-highs structure
  were *less* common before triplers. Calm, orderly charts were the ones that didn't triple.
- **Short side:**
  - The Reg SHO threshold list held 3.9% of triplers vs 0.7% (5.3×). Day 8 or later on the list:
    2.0% vs 0.5%.
  - Short interest was rising (+4.5% vs −0.5%).
  - Days to cover was lower (1.0 vs 2.6), because these stocks trade heavy volume.
  - The short-volume ratio barely differed.
- **News was quiet:** a median of 0 articles in the window (ordinary: 1).
- **Reddit couldn't be measured:** the archive refused most searches from GitHub's servers (HTTP 422) and
  used up its time budget after about 40 events.
- **SEC filings couldn't be measured:** the SEC blocks GitHub's servers.

**Learned scans, tested on the latest 30% of launches (which the learning never saw):**

| Scan | Flags | Catches | Lift |
|---|---|---|---|
| Daily | 141 of 681 windows | 57% of triplers | 2.7× |
| 4-hour | 83 of 570 | 44% | 3.0× |
| 1-hour | 63 of 582 | 37% | 3.4× |

These are lifts over ordinary windows from stocks at the same price, which tripled at the rates shown in the
report. Most crushed, volatile stocks still don't triple. The radar now grades the daily scan on live picks.

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
